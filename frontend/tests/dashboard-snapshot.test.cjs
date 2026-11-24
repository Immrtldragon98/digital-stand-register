const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
function client() {
  const context = { exports: {}, Date };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/dashboard-snapshot.ts', 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText, context);
  return context.exports;
}
const lines = [{id: 1, name: 'W1', positions: [{id: 10, position_number: 1, current_stand: {id: 7, code: '1B'}}]}];
test('saved dashboard survives a reload with the original sync time, scoped to API', () => {
  const values = new Map();
  const storage = {getItem: key => values.get(key), setItem: (key, value) => values.set(key, value)};
  const savedAt = Date.now() - 86_400_000;
  client().saveSnapshot(storage, 'https://api-one/api/v1', {savedAt, lines});
  const restored = client().readSnapshot(storage, 'https://api-one/api/v1');
  assert.equal(restored.savedAt, savedAt);
  assert.equal(restored.lines[0].positions[0].current_stand.code, '1B');
  assert.equal(client().readSnapshot(storage, 'https://api-two/api/v1'), null);
});
test('corrupt or unavailable browser storage is harmless', () => {
  const api = client();
  for (const raw of ['invalid', '{}', '{"savedAt":1,"lines":[{}]}']) {
    assert.equal(api.readSnapshot({getItem: () => raw}, '/api/v1'), null);
  }
  const blocked = {getItem() {throw Error('blocked');}, setItem() {throw Error('full');}};
  assert.equal(api.readSnapshot(blocked, '/api/v1'), null);
  assert.doesNotThrow(() => api.saveSnapshot(blocked, '/api/v1', {savedAt: Date.now(), lines}));
});
test('malformed refresh data cannot overwrite a saved dashboard', () => {
  const values = new Map(), api = client();
  const storage = {getItem: key => values.get(key), setItem: (key, value) => values.set(key, value)};
  api.saveSnapshot(storage, '/api/v1', {savedAt: 123, lines});
  for (const bad of [{}, '<html>starting</html>', [{id:1,name:'W1',positions:null}], [{id:1,name:'W1',positions:[{}]}]]) {
    assert.equal(api.isDashboard(bad), false);
    api.saveSnapshot(storage, '/api/v1', {savedAt: Date.now(), lines: bad});
  }
  assert.equal(api.readSnapshot(storage, '/api/v1').savedAt, 123);
});
