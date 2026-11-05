"""Izolált Chrome DOM-próba: minden URL helyi HTML, valódi kosárkérés nélkül."""

from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
core = (ROOT / "extension/core.js").read_text(encoding="utf-8")
background = (ROOT / "extension/background.js").read_text(encoding="utf-8")
content = (ROOT / "extension/content.js").read_text(encoding="utf-8")

stub = """
window.__adds=0;window.__planCalls=0;window.__claimedAny=false;
window.__lastStatus="";window.__changeListeners=[];window.__contentListeners=[];
window.importScripts=()=>{};
window.chrome={
 runtime:{
  id:"a".repeat(32),
  onMessage:{addListener:fn=>{if(!window.__worker)window.__worker=fn;else window.__contentListeners.push(fn);}},
  sendNativeMessage:async(host,request)=>{
    if(request.type==="profiles") return {ok:true,profiles:[
      {id:"self",name:"Én",configured:true},
      {id:"wife",name:"Feleségem",configured:true},
      {id:"son",name:"Fiam",configured:true}]};
    window.__planCalls++;
    return {ok:true,plan:{...window.__plan,profile_id:request.profile_id}};
  },
  sendMessage:async message=>{
    if(message.type==="settings" && window.__logoutAfterClaim && window.__claimedAny) {
      window.__logoutAfterClaim=false;
      window.postMessage({source:"interfood-cart-bridge",type:"account",accountId:null},location.origin);
      await new Promise(resolve=>setTimeout(resolve,50));
    }
    if(message.type==="status") window.__lastStatus=message.text;
    const response=await new Promise(resolve=>window.__worker(message,{
      id:"a".repeat(32),frameId:0,tab:{id:1},url:location.href},resolve));
    if(message.type==="claim" && response.claimed) window.__claimedAny=true;
    return response;
  }
 },
 tabs:{sendMessage:async(tabId,message)=>new Promise(resolve=>{
   if(!window.__contentListeners.length)resolve(null);
   else window.__contentListeners.forEach(fn=>fn(message,{id:window.chrome.runtime.id},resolve));
 })},
 storage:{
  local:{
   get:async keys=>{
    const state=JSON.parse(localStorage.getItem("extension-store")||"{}");
    return Object.fromEntries((keys===null?Object.keys(state):Array.isArray(keys)?keys:[keys])
      .filter(key=>Object.hasOwn(state,key)).map(key=>[key,state[key]]));
   },
   remove:async keys=>{
    const state=JSON.parse(localStorage.getItem("extension-store")||"{}");
    for(const key of keys)delete state[key];
    localStorage.setItem("extension-store",JSON.stringify(state));
   },
   set:async values=>{
    const state=JSON.parse(localStorage.getItem("extension-store")||"{}"), changes={};
    for(const [key,value] of Object.entries(values)) {
      if(JSON.stringify(state[key])!==JSON.stringify(value)) changes[key]={oldValue:state[key],newValue:value};
      state[key]=value;
    }
    localStorage.setItem("extension-store",JSON.stringify(state));
    if(Object.keys(changes).length) setTimeout(()=>window.__changeListeners.forEach(fn=>fn(changes,"local")),0);
   }
  },
  onChanged:{addListener:fn=>window.__changeListeners.push(fn)}
 }
};
"""
html = """<!doctype html><html><head><meta charset="utf-8"></head><body>
<button id="week"></button><div class="date-button active" id="day"></div>
<div class="food" data-menu-item-id="1">
<span class="food-middle-right-quantity">0</span>
<button aria-label="Kosárhoz adás: Csirke" onclick="window.__adds++;this.previousElementSibling.textContent=Number(this.previousElementSibling.textContent)+1">+</button>
</div>
<div class="food" data-menu-item-id="2">
<span class="food-middle-right-quantity">1</span>
<button aria-label="Kosárhoz adás: Rizottó" onclick="window.__adds++;this.previousElementSibling.textContent=Number(this.previousElementSibling.textContent)+1">+</button>
</div></body></html>"""


def prepare(page, login=True):
    page.evaluate("""login=>{
      const week=InterfoodCartCore.nextWeek();
      document.getElementById("week").setAttribute("aria-label","Hét kiválasztása, jelenleg kiválasztott hét: "+week.week);
      document.getElementById("day").setAttribute("data-date",week.start);
      window.__plan={version:1,week_start:week.start,week_end:week.end,items:[
        {id:1,name:"Csirke",code:"E1",date:week.start,quantity:1},
        {id:2,name:"Rizottó",code:"E2",date:week.start,quantity:1}]};
      window.postMessage({source:"interfood-cart-bridge",type:"menu",payload:{
        data:{a:{categories:[{items:[{date:week.start}]}]}}}},location.origin);
      if(login) window.postMessage({source:"interfood-cart-bridge",type:"account",accountId:"123"},location.origin);
    }""", login)


def ready(page):
    page.wait_for_function('document.getElementById("interfood-cart-start")?.disabled===false')


def done(page):
    page.wait_for_function('window.__lastStatus.startsWith("Kosársegéd kész")', timeout=15000)


def amount(page, identity):
    return page.locator(f'[data-menu-item-id="{identity}"] .food-middle-right-quantity').inner_text()


with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    try:
        def new_context():
            context=browser.new_context()
            context.route("**/*",lambda route:route.fulfill(status=200,content_type="text/html",body=html))
            context.add_init_script(stub+"\n(function(){\n"+core+"\n"+background+"\n})();\n"+content)
            return context
        context=new_context()
        page=context.new_page()
        page.goto("https://rendel.interfood.hu/",wait_until="domcontentloaded")
        prepare(page,False)
        page.wait_for_timeout(600)
        assert page.locator("#interfood-cart-start").is_disabled()
        assert page.evaluate("window.__adds") == 0
        prepare(page,True);ready(page)
        page.wait_for_timeout(600)
        assert page.evaluate("window.__adds===0 && window.__planCalls===0"), "Login started automatic work"
        page.locator("#interfood-cart-start").click();done(page)
        assert page.evaluate("window.__adds") == 1
        assert amount(page,2) == "1", "Existing first-person quantity changed"
        page.locator("#interfood-cart-start").click()
        page.wait_for_function('window.__lastStatus.includes("már megtörtént")')
        assert page.evaluate("window.__adds") == 1
        page.reload(wait_until="domcontentloaded");prepare(page);ready(page)
        page.locator("#interfood-cart-start").click()
        page.wait_for_function('window.__lastStatus.includes("már megtörtént")')
        assert page.evaluate("window.__adds") == 0, "Reload bypassed the weekly lock"
        page.locator("#interfood-cart-person").select_option("wife")
        ready(page);page.wait_for_timeout(400)
        assert page.evaluate("window.__adds") == 0, "Changing person started work"
        page.locator("#interfood-cart-start").click();done(page)
        assert page.evaluate("window.__adds") == 2
        assert (amount(page,1),amount(page,2)) == ("1","2"), "Earlier removed portion was restored"
        page.locator("#interfood-cart-person").select_option("son")
        ready(page);page.locator("#interfood-cart-start").click();done(page)
        assert (amount(page,1),amount(page,2)) == ("2","3")
        page.locator("#interfood-cart-start").click()
        page.wait_for_function('window.__lastStatus.includes("már megtörtént")')
        assert page.evaluate("window.__adds") == 4
        assert page.locator("#interfood-cart-reset").count() == 1, "Weekly reset option is missing"
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.locator("#interfood-cart-reset").click()
        assert page.evaluate("window.__adds") == 4
        page.once("dialog", lambda dialog: dialog.accept())
        page.locator("#interfood-cart-reset").click()
        page.wait_for_function('window.__lastStatus.includes("törölve")')
        assert (amount(page,1),amount(page,2)) == ("2","3"), "Reset changed basket contents"
        assert page.evaluate("window.__adds") == 4, "Reset started filling"
        page.evaluate('document.querySelectorAll(".food-middle-right-quantity").forEach(element=>element.textContent="0")')
        page.locator("#interfood-cart-person").select_option("self")
        ready(page)
        page.locator("#interfood-cart-start").click();done(page)
        assert (amount(page,1),amount(page,2)) == ("1","1"), "Reset did not allow a fresh manual fill"
        assert page.evaluate("window.__adds") == 6
        page.evaluate('chrome.storage.local.set({enabled:false})')
        page.wait_for_timeout(500)
        assert page.locator("#interfood-cart-start").is_disabled(), "Disabled helper button is enabled"
        context.close()
        context=new_context();page=context.new_page()
        page.goto("https://rendel.interfood.hu/",wait_until="domcontentloaded")
        prepare(page);ready(page)
        page.evaluate("window.__logoutAfterClaim=true")
        page.locator("#interfood-cart-start").click()
        page.wait_for_function('window.__lastStatus.includes("megszak")',timeout=15000)
        assert page.evaluate("window.__adds") == 0, "Logout during async validation still clicked"
        print("Offline DOM passed: manual only, per-person weekly lock, three family portions, no restoration, logout protection, scoped weekly reset and refill.")
    except Exception:
        print("DOM diagnostics:",page.evaluate("({status:window.__lastStatus,adds:window.__adds,body:document.body.innerText})"))
        raise
    finally:
        browser.close()
