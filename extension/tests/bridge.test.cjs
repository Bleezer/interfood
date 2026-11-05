const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function bridge(body, url='https://ia.interfood.hu/api/v1/user') {
  const messages=[], listeners={};
  const window = {
    fetch:async()=>({url,status:200,clone:()=>({json:async()=>body})}),
    postMessage:message=>messages.push(message),
    addEventListener:(type,fn)=>{listeners[type]=fn;}
  };
  function XHR() {}
  XHR.prototype.open=function(){};
  XHR.prototype.send=function(){};
  const context=vm.createContext({
    window,location:{href:'https://rendel.interfood.hu/',origin:'https://rendel.interfood.hu'},
    URL,XMLHttpRequest:XHR
  });
  vm.runInContext(fs.readFileSync(require.resolve('../bridge.js'),'utf8'),context);
  return {window,messages,listeners};
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));

test('user response forwards only numeric identity, never profile or tokens',async()=>{
  const b=bridge({data:{id:123,email:'private@example.test',token:'DO_NOT_FORWARD'}});
  await b.window.fetch('https://ia.interfood.hu/api/v1/user'); await tick();
  assert.equal(b.messages.length,1);
  assert.deepEqual(JSON.parse(JSON.stringify(b.messages[0])),
    {source:'interfood-cart-bridge',type:'account',accountId:'123'});
});

test('login invalidates prior identity before awaiting network',async()=>{
  const b=bridge({access_token:'DO_NOT_FORWARD'},'https://ia.interfood.hu/api/v1/login');
  await b.window.fetch('https://ia.interfood.hu/api/v1/login'); await tick();
  assert.equal(b.messages.length,1);
  assert.equal(b.messages[0].accountId,null);
  assert.equal(JSON.stringify(b.messages).includes('DO_NOT_FORWARD'),false);
});

test('other tab storage event invalidates historical identity',()=>{
  const b=bridge({});
  b.listeners.storage({});
  assert.equal(b.messages[0].accountId,null);
});

test('responses from other hosts are ignored',async()=>{
  const b=bridge({data:{id:123}},'https://other.example/api/v1/user');
  await b.window.fetch('https://other.example/api/v1/user'); await tick();
  assert.equal(b.messages.length,0);
});
