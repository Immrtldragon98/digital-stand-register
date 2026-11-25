const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');const ts=require('typescript');
const context={exports:{},Map,Date,Math};vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/confirmation-key.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,context);
test('retry key stays stable until acknowledged, then a later preparation cycle gets a new command',()=>{
 const {confirmationKey,forgetConfirmationKey}=context.exports;
 const key=confirmationKey('stage','same-payload');assert.equal(confirmationKey('stage','same-payload'),key);
 forgetConfirmationKey('stage','same-payload');assert.notEqual(confirmationKey('stage','same-payload'),key);
});