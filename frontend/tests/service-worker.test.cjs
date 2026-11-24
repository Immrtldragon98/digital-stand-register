const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function worker() {
  const handlers = {}, matches = [];
  const self = {location: {origin:'https://app.test'}, addEventListener: (event, handler) => handlers[event] = handler};
  vm.runInNewContext('const CACHE="dsr-shell-test"; const ASSETS=["/dashboard/","/_next/static/app.js"];\n' + fs.readFileSync('scripts/service-worker.js','utf8'), {
    self, URL, Response,
    fetch: async () => {throw Error('offline');},
    caches: {open: async () => ({match: async path => {matches.push(path); return new Response('saved shell');}})},
  });
  return {handlers, matches};
}
test('worker never intercepts API requests, external requests or writes', () => {
  const {handlers} = worker();
  for (const [url, method] of [['https://app.test/api/v1/dashboard/','GET'], ['https://api.test/api/v1/dashboard/','GET'], ['https://app.test/dashboard/','POST']]) {
    handlers.fetch({request:{url,method,mode:'navigate'},respondWith(){assert.fail('private or mutating request intercepted');}});
  }
});
test('offline dashboard navigation restores only the precached public shell', async () => {
  const {handlers,matches} = worker();
  let result;
  handlers.fetch({request:{url:'https://app.test/dashboard/',method:'GET',mode:'navigate'},respondWith(value){result=value;}});
  assert.equal(await (await result).text(), 'saved shell');
  assert.deepEqual(matches, ['/dashboard/']);
});
