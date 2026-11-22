// Run after a local production build with the default API origin (localhost:8000).
const http=require('node:http');
const {spawn}=require('node:child_process');
const assert=require('node:assert/strict');
const paths=[];
let next;
const api=http.createServer((req,res)=>{
 paths.push(req.url);
 if(req.url==='/api/v1/dashboard/'||req.url==='/api/v1/stands/'||req.url==='/api/v1/intelligence/summary'){
  res.setHeader('content-type','application/json');res.end(JSON.stringify({path:req.url}));
 }else{res.statusCode=307;res.setHeader('location',`http://localhost:8000${req.url}/`);res.end();}
});
(async()=>{
 await new Promise((resolve,reject)=>{api.once('error',reject);api.listen(8000,'127.0.0.1',resolve)});
 let logs='';
 next=spawn(process.execPath,['node_modules/next/dist/bin/next','start','--hostname','127.0.0.1','--port','18081'],{cwd:process.cwd(),env:{...process.env,NODE_ENV:'production'},stdio:['ignore','pipe','pipe']});
 next.stdout.on('data',b=>logs+=b);next.stderr.on('data',b=>logs+=b);
 await new Promise((resolve,reject)=>{
  const timer=setInterval(()=>{if(logs.includes('Ready in')){clearInterval(timer);clearTimeout(timeout);resolve();}},100);
  const timeout=setTimeout(()=>{clearInterval(timer);reject(new Error('Next failed to start: '+logs))},20000);
  next.once('exit',c=>{if(c){clearInterval(timer);clearTimeout(timeout);reject(new Error('Next exited '+c+': '+logs));}});
 });
 for(const path of ['/api/v1/dashboard/','/api/v1/stands/','/api/v1/intelligence/summary']){
  const r=await fetch(`http://127.0.0.1:18081${path}`,{redirect:'manual'});
  assert.equal(r.status,200,`${path}: got ${r.status}, location ${r.headers.get('location')}`);
  assert.equal((await r.json()).path,path);
  console.log('PASS same-origin proxy preserves '+path);
 }
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>{next?.kill('SIGTERM');api.close();});
