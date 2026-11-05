const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const core = require('../core.js');

function worker() {
  const state = {};
  let listener;
  const id = 'a'.repeat(32);
  const context = vm.createContext({
    console, URL, Promise, InterfoodCartCore: core, importScripts() {},
    chrome: {
      runtime: {id, onMessage:{addListener(fn){listener=fn;}}, sendNativeMessage:async(host,request)=> {
        if(request.type==='profiles') return {ok:true,profiles:['self','wife','son'].map(id=>({id,name:id,configured:true}))};
        const week=core.nextWeek();
        return {ok:true,plan:{version:1,profile_id:request.profile_id,week_start:week.start,items:[
          {id:1,date:week.start,name:'Csirke',code:'E1',quantity:1}]}};
      }},
      storage:{local:{
        get:async keys => Object.fromEntries((Array.isArray(keys)?keys:[keys])
          .filter(key=>Object.hasOwn(state,key)).map(key=>[key,structuredClone(state[key])])),
        set:async values=>Object.assign(state,structuredClone(values))
      }}
    }
  });
  vm.runInContext(fs.readFileSync(require.resolve('../background.js'),'utf8'),context);
  const sender = tab => ({id,frameId:0,tab:{id:tab},url:'https://rendel.interfood.hu/'});
  return {state, send:(message,tab=1)=>new Promise(resolve=>listener({
    profileId:'self',weekStart:core.nextWeek().start,...message},sender(tab),resolve))};
}

async function plan(w,profileId='self',tab=1) {
  return w.send({type:'plan',accountId:'12',profileId,payload:{}},tab);
}

test('another tab account change invalidates the first account', async () => {
  const w=worker();
  assert.equal((await w.send({type:'account',accountId:'12'})).ok,true);
  assert.equal((await plan(w)).ok,true);
  await w.send({type:'account',accountId:'34'},2);
  assert.equal((await w.send({type:'settings'})).accountId,'34');
  assert.equal((await w.send({type:'claim',accountId:'12',itemId:1})).ok,false);
});

test('one weekly button operation per person even after new plan', async () => {
  const w=worker();
  await w.send({type:'account',accountId:'12'});
  assert.equal((await w.send({type:'run-status',accountId:'12'})).status,'new');
  await plan(w);
  assert.equal((await w.send({type:'begin',accountId:'12'})).started,true);
  await w.send({type:'claim',accountId:'12',itemId:1});
  await w.send({type:'finish',accountId:'12',itemId:1,status:'done'});
  await w.send({type:'finish-run',accountId:'12',status:'done'});
  await plan(w);
  const repeated=await w.send({type:'begin',accountId:'12'});
  assert.equal(repeated.started,false);
  assert.equal(repeated.status,'done');
});

test('concurrent tabs cannot start the same person twice',async()=>{
  const w=worker();
  await w.send({type:'account',accountId:'12'});
  await plan(w);
  const results=await Promise.all([1,2].map(tab=>w.send({type:'begin',accountId:'12'},tab)));
  assert.deepEqual(results.map(result=>result.started).sort(),[false,true]);
});

test('another family member adds their own portion of shared meal',async()=>{
  const w=worker();
  await w.send({type:'account',accountId:'12'});
  await plan(w);
  await w.send({type:'begin',accountId:'12'});
  const first=await w.send({type:'claim',accountId:'12',itemId:1});
  assert.equal(first.claimed,true);
  assert.equal(first.addOne,false);
  await w.send({type:'finish',accountId:'12',itemId:1,status:'done'});
  await w.send({type:'finish-run',accountId:'12',status:'done'});
  assert.equal((await w.send({type:'run-status',accountId:'12',profileId:'wife'})).status,'new');
  await plan(w,'wife');
  assert.equal((await w.send({type:'begin',accountId:'12',profileId:'wife'})).started,true);
  const second=await w.send({type:'claim',accountId:'12',profileId:'wife',itemId:1});
  assert.equal(second.claimed,true);
  assert.equal(second.addOne,true);
});

test('legacy automatic fill counts as self, without blocking other people',async()=>{
  const w=worker(), week=core.nextWeek().start;
  w.state[core.ledgerKey('12',week)]={1:{status:'done',tabId:10}};
  await w.send({type:'account',accountId:'12'});
  assert.equal((await w.send({type:'run-status',accountId:'12'})).status,'done');
  assert.equal((await w.send({type:'run-status',accountId:'12',profileId:'son'})).status,'new');
});

test('uncertain or interrupted week cannot be restarted',async()=>{
  const w=worker();
  await w.send({type:'account',accountId:'12'});
  await plan(w);await w.send({type:'begin',accountId:'12'});
  assert.equal((await w.send({type:'begin',accountId:'12'},2)).started,false);
  await w.send({type:'finish-run',accountId:'12',status:'uncertain'});
  assert.equal((await w.send({type:'begin',accountId:'12'})).started,false);
});

test('logout invalidates active claims and new plans', async () => {
  const w=worker();
  await w.send({type:'account',accountId:'12'});
  await w.send({type:'account',accountId:null});
  assert.equal((await w.send({type:'settings'})).accountId,null);
  assert.equal((await plan(w)).ok,false);
});

test('wife-first upgrade still adds a portion beyond legacy self cart',async()=>{
  const w=worker(), week=core.nextWeek().start;
  w.state[core.ledgerKey('12',week)]={1:{status:'done',tabId:10}};
  await w.send({type:'account',accountId:'12'});
  await plan(w,'wife');
  await w.send({type:'begin',accountId:'12',profileId:'wife'});
  const claim=await w.send({type:'claim',accountId:'12',profileId:'wife',itemId:1});
  assert.equal(claim.claimed,true);
  assert.equal(claim.addOne,true);
});
