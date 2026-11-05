const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const core = require('../core.js');

function worker(options = {}) {
  const state = {};
  let listener;
  const id = 'a'.repeat(32);
  const context = vm.createContext({
    console, URL, Promise, InterfoodCartCore: core, importScripts() {},
    chrome: {
      tabs: {sendMessage:async()=>({busy:options.tabBusy===true})},
      runtime: {id, onMessage:{addListener(fn){listener=fn;}}, sendNativeMessage:async(host,request)=> {
        if(request.type==='profiles') return {ok:true,profiles:['self','wife','son'].map(id=>({id,name:id,configured:true}))};
        const week=core.nextWeek();
        return {ok:true,plan:{version:1,profile_id:request.profile_id,week_start:week.start,items:[
          {id:1,date:week.start,name:'Csirke',code:'E1',quantity:1}]}};
      }},
      storage:{local:{
        get:async keys => Object.fromEntries((keys===null?Object.keys(state):Array.isArray(keys)?keys:[keys])
          .filter(key=>Object.hasOwn(state,key)).map(key=>[key,structuredClone(state[key])])),
        set:async values=>Object.assign(state,structuredClone(values)),
        remove:async keys=>{for(const key of keys) delete state[key];}
      }}
    }
  });
  vm.runInContext(fs.readFileSync(require.resolve('../background.js'),'utf8'),context);
  const sender = tab => ({id,frameId:0,tab:{id:tab},url:'https://rendel.interfood.hu/'});
  return {state, options, send:(message,tab=1)=>new Promise(resolve=>listener({
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

test('weekly reset clears every person and legacy data, preserving other scopes',async()=>{
  const w=worker(), week=core.nextWeek().start, base='12:'+week;
  const own={
    ['cart-ledger:'+base]:{1:{status:'done'}},
    ['cart-ledger:'+base+':self']:{1:{status:'done'}},
    ['cart-ledger:'+base+':wife']:{1:{status:'done'}},
    ['cart-run:'+base+':self']:{status:'done'},
    ['cart-run:'+base+':son']:{status:'uncertain'},
    ['plan:'+base+':self']:{items:[]},
    ['plan:'+base+':wife']:{items:[]},
    ['cart-contributors:'+base]:{1:['self','wife']}
  };
  Object.assign(w.state,own,{
    ['cart-run:123:'+week+':self']:{status:'done'},
    'cart-run:12:2099-01-05:self':{status:'done'},
    enabled:false,selectedProfileId:'wife'
  });
  await w.send({type:'account',accountId:'12'});
  const response=await w.send({type:'reset-week',accountId:'12',profileId:undefined});
  assert.equal(response.ok,true);
  for(const key of Object.keys(own)) assert.equal(Object.hasOwn(w.state,key),false,key);
  assert.equal(w.state['cart-run:123:'+week+':self'].status,'done');
  assert.equal(w.state['cart-run:12:2099-01-05:self'].status,'done');
  assert.equal(w.state.enabled,false);
  assert.equal(w.state.selectedProfileId,'wife');
  for(const profileId of ['self','wife','son'])
    assert.equal((await w.send({type:'run-status',accountId:'12',profileId})).status,'new');
});

test('weekly reset rejects live filling but permits abandoned running records',async()=>{
  const w=worker({tabBusy:true}), week=core.nextWeek().start;
  w.state['cart-run:12:'+week+':self']={status:'running',tabId:1};
  await w.send({type:'account',accountId:'12'});
  assert.equal((await w.send({type:'reset-week',accountId:'12'})).ok,false);
  assert.equal(w.state['cart-run:12:'+week+':self'].status,'running');
  w.options.tabBusy=false;
  assert.equal((await w.send({type:'reset-week',accountId:'12'})).ok,true);
});

test('reset is bound to current account and next week',async()=>{
  const w=worker(), week=core.nextWeek().start;
  w.state['cart-run:12:'+week+':self']={status:'done'};
  await w.send({type:'account',accountId:'12'});
  assert.equal((await w.send({type:'reset-week',accountId:'13'})).ok,false);
  assert.equal((await w.send({type:'reset-week',accountId:'12',weekStart:'2099-01-05'})).ok,false);
  assert.equal(w.state['cart-run:12:'+week+':self'].status,'done');
});

test('pre-reset operations cannot affect a new run after reset',async()=>{
  const w=worker();
  await w.send({type:'account',accountId:'12'});
  await plan(w);await w.send({type:'begin',accountId:'12'});
  assert.equal((await w.send({type:'reset-week',accountId:'12'})).ok,true);
  const status=await w.send({type:'run-status',accountId:'12'});
  assert.equal(status.resetEpoch,1);
  await w.send({type:'plan',accountId:'12',payload:{},resetEpoch:1});
  assert.equal((await w.send({type:'begin',accountId:'12',resetEpoch:1})).started,true);
  assert.equal((await w.send({type:'claim',accountId:'12',itemId:1,resetEpoch:0})).ok,false);
  assert.equal((await w.send({type:'finish-run',accountId:'12',status:'uncertain',resetEpoch:0})).ok,false);
  assert.equal((await w.send({type:'claim',accountId:'12',itemId:1,resetEpoch:1})).claimed,true);
});
