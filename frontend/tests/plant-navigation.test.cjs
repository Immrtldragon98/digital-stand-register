const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const context={exports:{},URLSearchParams};vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/plant-navigation.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,context);
const {matchingPositions,selectionFromLocation}=context.exports;
const lines=[{id:1,name:'W1',positions:[{id:10,position_number:1,current_stand:{code:'1A'}},{id:11,position_number:2,current_stand:null}]},{id:4,name:'New Line',positions:[{id:40,position_number:1,current_stand:{code:'CUSTOM-7'}}]}];
test('deep links resolve the actual line and position, not hardcoded line IDs',()=>{
 const selected=selectionFromLocation(lines,'?line=New%20Line&position=1');assert.equal(selected.line.id,4);assert.equal(selected.position.id,40);
 assert.equal(selectionFromLocation(lines,'?line=missing&position=999').position,null);
});
test('stand search can select a matching line and combines line and position terms',()=>{
 assert.equal(selectionFromLocation(lines,'?q=CUSTOM-7').line.name,'New Line');
 assert.equal(matchingPositions(lines,'W1 P1 1A').length,1);assert.equal(matchingPositions(lines,'empty')[0].position.id,11);
 assert.equal(matchingPositions(lines,'not-present').length,0);
});
test('empty registers and missing positions preserve an empty state',()=>{
 assert.equal(selectionFromLocation([],'?line=W1').line,null);assert.equal(matchingPositions([],'').length,0);
});
