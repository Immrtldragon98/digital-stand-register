const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
const context={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/feedback-draft.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,context);
const {loadFeedbackDraft,saveFeedbackDraft,clearFeedbackDraft}=context.exports;
const form={kind:'BUG',title:'Refresh failed',description:'The dashboard refresh did not finish.',page:'/dashboard',reporter:''};
function storage(){const data=new Map();return {getItem:key=>data.get(key)||null,setItem:(key,value)=>data.set(key,value),removeItem:key=>data.delete(key)};}
test('a reload preserves unsent text and its exact uncertain submission key',()=>{
 const store=storage(),pending={...form,request_id:'c1ff0000-0000-4000-8000-000000000001'};
 assert.equal(saveFeedbackDraft(store,'api-A',{form,pending}),true);
 const restored=loadFeedbackDraft(store,'api-A');assert.equal(restored.form.description,form.description);assert.equal(restored.pending.request_id,pending.request_id);
 assert.equal(loadFeedbackDraft(store,'api-B'),null);
 clearFeedbackDraft(store,'api-A');assert.equal(loadFeedbackDraft(store,'api-A'),null);
});
test('edited or invalid retry payload cannot reuse a stored request key',()=>{
 const store=storage();saveFeedbackDraft(store,'api',{form,pending:{...form,title:'Different report',request_id:'c1ff0000-0000-4000-8000-000000000001'}});
 assert.equal(loadFeedbackDraft(store,'api').pending,null);
});
test('a maximum-length report with escaped text still survives uncertain submission recovery',()=>{
 const store=storage(),large={...form,description:'"'.repeat(5000)};
 saveFeedbackDraft(store,'api',{form:large,pending:{...large,request_id:'c1ff0000-0000-4000-8000-000000000001'}});
 assert.equal(loadFeedbackDraft(store,'api').pending.description.length,5000);
});
test('corrupt drafts and denied browser storage do not crash the form',()=>{
 assert.equal(loadFeedbackDraft({getItem:()=>'{broken'},'api'),null);
 assert.equal(loadFeedbackDraft({getItem:()=>{throw Error('Denied')}},'api'),null);
 assert.equal(saveFeedbackDraft({setItem:()=>{throw Error('Full')}},'api',{form,pending:null}),false);
});
