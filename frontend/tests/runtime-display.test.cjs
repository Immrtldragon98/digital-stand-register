const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
const context={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/runtime-display.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,context);
const {runtimeHours,runtimeLabel}=context.exports;
test('unknown and invalid life never becomes measured zero',()=>{
 for(const value of [null,undefined,"",false,true,-1,Infinity,NaN])assert.equal(runtimeHours(value),"Not recorded");
 assert.equal(runtimeHours(0),"0 h");assert.equal(runtimeHours(12),"12 h");
});
test('partial measured history stays explicitly incomplete',()=>{
 assert.equal(runtimeLabel(null,8,false),"8 h measured · partial");
 assert.equal(runtimeLabel(null,null,false),"Incomplete history");
 assert.equal(runtimeLabel(null,8,undefined),"Not recorded");
 assert.equal(runtimeLabel(0,0,true),"0 h");
});
