const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
const context={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/runtime-display.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,context);
const {runtimeHours,runtimeLabel,apiDateMs,installationElapsedHours,currentRunLeaders,supportedComparison,comparisonDuration}=context.exports;
test('unknown and invalid life never becomes measured zero',()=>{
 for(const value of [null,undefined,""," ",false,true,-1,Infinity,NaN])assert.equal(runtimeHours(value),"Not recorded");
 assert.equal(runtimeHours(0),"0 h");assert.equal(runtimeHours(12),"12 h");
});
test('missing runtime records do not display a fabricated zero run',()=>{
 assert.equal(runtimeLabel(null,8,false),"8 h observed · incomplete");
 assert.equal(runtimeLabel(null,null,false),"Not recorded · runtime history missing");
 assert.equal(runtimeLabel(null,0,false),"0 h observed · incomplete");
 assert.equal(runtimeLabel(null,8,undefined),"Not recorded");
 assert.equal(runtimeLabel(0,0,true),"0 h");
});
const asOf=Date.parse('2026-11-26T12:00:00Z');
test('naive API installation timestamps are interpreted as UTC',()=>{
 assert.equal(apiDateMs('2026-11-25T12:00:00'),Date.parse('2026-11-25T12:00:00Z'));
 assert.equal(installationElapsedHours({installed_at:'2026-11-25T12:00:00'},asOf),24);
 assert.equal(installationElapsedHours({installed_at:'2026-11-27T12:00:00'},asOf),null);
 assert.equal(installationElapsedHours({elapsed_hours:0},asOf),0);
});
test('current installation leader never becomes best measured run without complete coverage',()=>{
 const lines=[{name:'W1',positions:[
  {position_number:1,current_stand:{code:'1A',elapsed_hours:200,campaign_hours:null,known_runtime_hours:0,runtime_complete:false}},
  {position_number:2,current_stand:{code:'2B',elapsed_hours:100,campaign_hours:50,known_runtime_hours:50,runtime_complete:true}},
  {position_number:3,current_stand:null}]}];
 const result=currentRunLeaders(lines,asOf);
 assert.equal(result.installedCount,2);assert.equal(result.measuredCount,1);
 assert.equal(result.elapsedLeader.stand,'1A');assert.equal(result.measuredLeader.stand,'2B');
});
test('no runtime coverage produces no measured leader, while a true measured zero remains valid',()=>{
 const result=currentRunLeaders([{name:'W1',positions:[{position_number:1,current_stand:{code:'1A',installed_at:'2026-11-25T12:00:00Z',runtime_complete:false,known_runtime_hours:0,campaign_hours:null}}]}],asOf);
 assert.equal(result.measuredLeader,null);assert.equal(result.elapsedLeader.elapsed_hours,24);
 const zero=currentRunLeaders([{name:'W1',positions:[{position_number:1,current_stand:{code:'1A',elapsed_hours:2,runtime_complete:true,campaign_hours:0}}]}],asOf);
 assert.equal(zero.measuredLeader.actual_runtime_hours,0);
});

test('measured completed comparisons outrank historical screening without mixing units',()=>{
 const measured={stand:'1A',evidence:'SUFFICIENT',basis:'MEASURED_MILL_RUNTIME_HOURS',median_hours:100,peer_median_hours:80,vs_peer_pct:25};
 const historical={stand:'1B',evidence:'SUFFICIENT',basis:'INFERRED_SNAPSHOT_ELAPSED_DAYS',median_days:10,peer_median_days:5,vs_peer_pct:100};
 assert.equal(supportedComparison([measured],[historical],'better').stand,'1A');
 assert.equal(comparisonDuration(measured),'100 h');assert.equal(comparisonDuration(historical),'10 d elapsed');
 assert.equal(supportedComparison([{...measured,evidence:'INSUFFICIENT'}],[historical],'better').stand,'1B');
 assert.equal(supportedComparison([measured],[historical],'weaker'),null);
});
