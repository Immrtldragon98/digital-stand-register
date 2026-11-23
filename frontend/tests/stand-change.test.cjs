const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
function client(fetchApi){
 let invalidations=0;
 const context={exports:{},require:()=>({fetchApi,invalidateApiCache:()=>invalidations++})};
 const source=ts.transpileModule(fs.readFileSync('lib/stand-change.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
 vm.runInNewContext(source,context);
 return {...context.exports,invalidations:()=>invalidations};
}
const payload={position_id:7,removed_stand_code:'7A',installed_stand_code:'7.1'};
const lines=[{positions:[{id:7,current_stand:{code:'7A'}}]}];
const ready=[{code:'7.1',current_status:'READY',current_position_id:null}];

test('fresh state is checked before the stand change is sent once',async()=>{
 const calls=[];
 const api=client(async(path,options)=>{calls.push(path);if(path==='/dashboard/')return lines;if(path==='/stands/')return ready;assert.equal(options.method,'POST');assert.deepEqual(JSON.parse(options.body),payload);return {status:'success'};});
 assert.equal((await api.saveStandChange(payload)).status,'success');
 assert.equal(api.invalidations(),1);
 assert.deepEqual(calls,['/dashboard/','/stands/','/operations/stands/change']);
});

test('changed running position blocks the write',async()=>{
 let writes=0;
 const api=client(async(path)=>path==='/dashboard/'?[{positions:[]}]:path==='/stands/'?ready:++writes);
 await assert.rejects(api.saveStandChange(payload),/running stand has changed/);
 assert.equal(writes,0);
});

test('replacement must still be Ready and unassigned',async()=>{
 for(const replacement of [{...ready[0],current_status:'PENDING'},{...ready[0],current_position_id:3}]){
  let writes=0;
  const api=client(async(path)=>path==='/dashboard/'?lines:path==='/stands/'?[replacement]:++writes);
  await assert.rejects(api.saveStandChange(payload),/no longer available/);
  assert.equal(writes,0);
 }
});

test('failed preflight sends no write and an uncertain write is never retried',async()=>{
 let writes=0;
 const unavailable=client(async()=>{throw new Error('Waking up')});
 await assert.rejects(unavailable.saveStandChange(payload),/Waking up/);
 const api=client(async(path)=>{if(path==='/dashboard/')return lines;if(path==='/stands/')return ready;writes++;throw new Error('Gateway timeout');});
 await assert.rejects(api.saveStandChange(payload),/Gateway timeout/);
 assert.equal(writes,1);
});
