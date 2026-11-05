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
      runtime: {id, onMessage:{addListener(fn){listener=fn;}}, sendNativeMessage:async()=> {
        const week=core.nextWeek();
        return {ok:true,plan:{version:1,week_start:week.start,items:[
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
  return {state, send:(message,tab=1)=>new Promise(resolve=>listener(message,sender(tab),resolve))};
}

test('another tab account change invalidates the first account', async () => {
  const w=worker(), week=core.nextWeek().start;
  assert.equal((await w.send({type:'account',accountId:'12'})).ok,true);
  assert.equal((await w.send({type:'plan',accountId:'12',payload:{}})).ok,true);
  assert.equal((await w.send({type:'account',accountId:'34'},2)).ok,true);
  assert.equal((await w.send({type:'settings'})).accountId,'34');
  assert.equal((await w.send({type:'claim',accountId:'12',weekStart:week,itemId:1})).ok,false);
});

test('same account tabs cannot claim the same item twice', async () => {
  const w=worker(), week=core.nextWeek().start;
  await w.send({type:'account',accountId:'12'});
  await w.send({type:'plan',accountId:'12',payload:{}});
  const results = await Promise.all([1,2].map(tab=>w.send({
    type:'claim',accountId:'12',weekStart:week,itemId:1},tab)));
  assert.deepEqual(results.map(result=>result.claimed).sort(),[false,true]);
});

test('logout invalidates active claims and new plans', async () => {
  const w=worker();
  await w.send({type:'account',accountId:'12'});
  await w.send({type:'account',accountId:null});
  assert.equal((await w.send({type:'settings'})).accountId,null);
  assert.equal((await w.send({type:'plan',accountId:'12',payload:{}})).ok,false);
});
