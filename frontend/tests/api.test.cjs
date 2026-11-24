const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

function client(fetch) {
  const timers = new Map();
  const context = {
    exports: {}, require: () => ({ getToken: () => 'operator-token' }),
    process: { env: {} }, fetch, Response, FormData, AbortController, Date,
    setTimeout(callback, delay) { const id = {}; timers.set(id, { callback, delay }); return id; },
    clearTimeout(id) { timers.delete(id); },
  };
  const source = ts.transpileModule(fs.readFileSync('lib/api.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  vm.runInNewContext(source, context);
  return { ...context.exports, timers };
}
const json = value => new Response(JSON.stringify(value), { headers: { 'content-type': 'application/json' } });

test('a failed read is retryable and successful reads are cached', async () => {
  let calls = 0;
  const api = client(async () => ++calls === 1
    ? new Response('{"detail":"Service warming up"}', { status: 500, headers: { 'content-type': 'application/json' } })
    : json({ ready: 3 }));
  await assert.rejects(api.fetchApi('/stands/'), /Service warming up/);
  assert.equal((await api.fetchApi('/stands/')).ready, 3);
  await api.fetchApi('/stands/');
  assert.equal(calls, 2);
  assert.equal(api.timers.size, 0);
});

test('concurrent reads share one request', async () => {
  let resolve, calls = 0;
  const api = client(() => { calls++; return new Promise(r => { resolve = r; }); });
  const first = api.fetchApi('/dashboard/');
  const second = api.fetchApi('/dashboard/');
  resolve(json([]));
  await Promise.all([first, second]);
  assert.equal(calls, 1);
});

test('a stalled read times out after 60 seconds, clears inflight state, and permits retry', async () => {
  let calls = 0;
  const api = client((url, options) => {
    if (++calls > 1) return Promise.resolve(json({ campaigns: 0 }));
    return new Promise((resolve, reject) => options.signal.addEventListener('abort', () => reject(new Error('aborted'))));
  });
  const first = api.fetchApi('/intelligence/summary');
  const rejected = assert.rejects(first, /connection timed out/);
  const [timer] = api.timers.values();
  assert.equal(timer.delay, 60_000);
  timer.callback();
  await rejected;
  assert.equal((await api.fetchApi('/intelligence/summary')).campaigns, 0);
  assert.equal(calls, 2);
});

test('stand changes are sent once, preserve auth headers, and invalidate old reads', async () => {
  let reads = 0, writes = 0;
  const api = client(async (url, options) => {
    assert.equal(options.headers.Authorization, 'Bearer operator-token');
    if (options.method === 'POST') { writes++; return json({ saved: true }); }
    reads++; return json([]);
  });
  await api.fetchApi('/stands/');
  await api.fetchApi('/operations/stands/change', { method: 'POST', headers: { 'X-Test': 'change' }, body: '{}' });
  await api.fetchApi('/stands/');
  assert.equal(writes, 1);
  assert.equal(reads, 2);
});

test('failed writes are not automatically retried', async () => {
  let calls = 0;
  const api = client(async () => { calls++; throw new Error('Disconnected'); });
  await assert.rejects(api.fetchApi('/operations/stands/change', { method: 'POST', body: '{}' }), /Disconnected/);
  assert.equal(calls, 1);
  assert.equal(api.timers.size, 0);
});

 test('gateway errors on reads recover automatically during cold start', async () => {
  let calls = 0;
  const api = client(async () => ++calls < 3 ? new Response('', {status: 502}) : json({ready: 30}));
  const result = api.fetchApi('/dashboard/');
  for (let i = 0; i < 2; i++) {
    await new Promise(resolve => setImmediate(resolve));
    const entry = [...api.timers.entries()].find(([,timer]) => timer.delay === 2000);
    assert.ok(entry);
    api.timers.delete(entry[0]);
    entry[1].callback();
  }
  assert.equal((await result).ready, 30);
  assert.equal(calls, 3);
  assert.equal(api.timers.size, 0);
});

async function nextRetry(api) {
  await new Promise(resolve => setImmediate(resolve));
  const entry = [...api.timers.entries()].find(([,timer]) => timer.delay === 2000);
  assert.ok(entry, 'expected a bounded read retry');
  api.timers.delete(entry[0]); entry[1].callback();
}
test('HTML 200 wake-up page is retried rather than returned as dashboard data', async () => {
  let calls = 0;
  const api = client(async () => ++calls === 1
    ? new Response('<html>starting</html>', {headers: {'content-type':'text/html'}}) : json([{id:1}]));
  const result = api.fetchApi('/dashboard/');
  await nextRetry(api);
  assert.equal((await result)[0].id, 1);
  assert.equal(calls, 2);
});
test('transient network failure recovers without caching the failure', async () => {
  let calls = 0;
  const api = client(async () => {if (++calls === 1) throw new TypeError('Failed to fetch'); return json({ok:true});});
  const result = api.fetchApi('/dashboard/');
  await nextRetry(api);
  assert.equal((await result).ok, true);
});
test('HTML responses to writes fail once and request verification', async () => {
  let calls = 0;
  const api = client(async () => {calls++; return new Response('<html>starting</html>', {headers:{'content-type':'text/html'}});});
  await assert.rejects(api.fetchApi('/operations/stands/change', {method:'POST',body:'{}'}), /confirm whether the change was saved/);
  assert.equal(calls, 1);
});
test('authorization failures are not retried and binary downloads remain supported', async () => {
  let calls = 0;
  const api = client(async url => {calls++; return url.endsWith('.xlsx')
    ? new Response('spreadsheet', {headers:{'content-type':'application/octet-stream'}})
    : new Response('{"detail":"Sign in"}', {status:401,headers:{'content-type':'application/json'}});});
  await assert.rejects(api.fetchApi('/private'), /Sign in/);
  assert.equal(calls, 1);
  assert.equal(await (await api.fetchApi('/report.xlsx')).text(), 'spreadsheet');
});
