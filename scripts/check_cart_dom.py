"""Izolált Chrome DOM-próba; minden URL helyi HTML-t kap, nincs valódi kosár."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
core = (ROOT / "extension/core.js").read_text(encoding="utf-8")
content = (ROOT / "extension/content.js").read_text(encoding="utf-8")
stub = """
window.__adds = 0;
window.__lastStatus = "";
window.__settingsCalls = 0;
window.__planCalls = 0;
window.chrome = {
  runtime: {sendMessage: async message => {
    if (message.type === "account") {window.__observed=message.accountId;return {ok:true};}
    if (message.type === "settings") {
      const count=++window.__settingsCalls;
      if (window.__logoutOnSettings===count) {
        window.postMessage({source:"interfood-cart-bridge",type:"account",accountId:null},location.origin);
        await new Promise(resolve=>setTimeout(resolve,50));
      }
      if (window.__slowSettings && count===1) await new Promise(resolve=>setTimeout(resolve,800));
      return {ok:true,enabled:true,accountId:window.__observed};
    }
    if (message.type === "status") {window.__lastStatus=message.text;return {ok:true};}
    if (message.type === "plan") {window.__planCalls++;return {ok:true,plan:window.__plan};}
    const ledger=JSON.parse(localStorage.getItem("test-ledger")||"{}");
    if (message.type === "claim") {
      const claimed=!ledger[message.itemId];
      if (claimed) {ledger[message.itemId]="pending";localStorage.setItem("test-ledger",JSON.stringify(ledger));}
      return {ok:true,claimed,status:ledger[message.itemId]};
    }
    if (message.type === "finish") {
      ledger[message.itemId]=message.status;
      localStorage.setItem("test-ledger",JSON.stringify(ledger));return {ok:true};
    }
    throw Error("Unknown test message");
  }},
  storage: {local:{set:async()=>{}},onChanged:{addListener:()=>{}}}
};
"""
html = """<!doctype html><html><head><meta charset="utf-8"></head><body>
<button id="week"></button>
<div class="date-button active" id="day"></div>
<div class="food" data-menu-item-id="1">
<span class="food-middle-right-quantity">0</span>
<button aria-label="Kosárhoz adás: Csirke" onclick="window.__adds++;this.previousElementSibling.textContent='1'">+</button>
</div>
<div class="food" data-menu-item-id="2">
<span class="food-middle-right-quantity">1</span>
<button aria-label="Kosárhoz adás: Rizottó" onclick="window.__adds++;this.previousElementSibling.textContent='2'">+</button>
</div></body></html>"""


def prepare(page, login):
    page.evaluate("""login => {
      const week=InterfoodCartCore.nextWeek();
      document.getElementById("week").setAttribute("aria-label","Hét kiválasztása, jelenleg kiválasztott hét: "+week.week);
      document.getElementById("day").setAttribute("data-date",week.start);
      window.__plan={version:1,week_start:week.start,week_end:week.end,items:[
        {id:1,name:"Csirke",code:"E1",date:week.start,quantity:1},
        {id:2,name:"Rizottó",code:"E2",date:week.start,quantity:1}]};
      window.postMessage({source:"interfood-cart-bridge",type:"menu",payload:{
        data:{a:{categories:[{items:[{date:week.start}]}]}}}},location.origin);
      if (login) window.postMessage({source:"interfood-cart-bridge",type:"account",accountId:"123"},location.origin);
    }""", login)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    try:
        context = browser.new_context()
        context.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=html))
        context.add_init_script(stub + "\n" + core + "\n" + content)
        page = context.new_page()
        page.goto("https://rendel.interfood.hu/", wait_until="domcontentloaded")
        prepare(page, False)
        page.wait_for_timeout(600)
        assert page.evaluate("window.__adds") == 0, "Anonymous session changed the basket"
        page.evaluate('window.postMessage({source:"interfood-cart-bridge",type:"account",accountId:"123"},location.origin)')
        page.wait_for_function('window.__lastStatus.startsWith("Kosársegéd kész")', timeout=15000)
        assert page.evaluate("window.__adds") == 1, "Existing item should not be incremented"
        assert page.locator('[data-menu-item-id="2"] .food-middle-right-quantity').inner_text() == "1"
        page.reload(wait_until="domcontentloaded")
        prepare(page, True)
        page.wait_for_function('window.__lastStatus.startsWith("Kosársegéd kész")', timeout=15000)
        assert page.evaluate("window.__adds") == 0, "Removed item reappeared after reload"
        context.close()
        context = browser.new_context()
        context.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=html))
        context.add_init_script(stub + "\n" + core + "\n" + content)
        page = context.new_page()
        page.goto("https://rendel.interfood.hu/", wait_until="domcontentloaded")
        page.evaluate("window.__logoutOnSettings=5")
        prepare(page, True)
        page.wait_for_function('window.__lastStatus.includes("megszak")', timeout=15000)
        assert page.evaluate("window.__adds") == 0, "Logout during async validation still clicked add"
        context.close()
        context = browser.new_context()
        context.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=html))
        context.add_init_script(stub + "\n" + core + "\n" + content)
        page = context.new_page()
        page.goto("https://rendel.interfood.hu/", wait_until="domcontentloaded")
        page.evaluate("window.__slowSettings=true")
        prepare(page, True)
        page.wait_for_function("window.__settingsCalls===1")
        prepare(page, True)
        page.wait_for_function('window.__lastStatus.startsWith("Kosársegéd kész")', timeout=15000)
        page.wait_for_timeout(1000)
        assert page.evaluate("window.__planCalls") == 1, "Two concurrent runs entered"
        print("Offline DOM check passed: no anonymous cart change; existing quantity preserved; no re-add after reload.")
    except Exception:
        print("DOM diagnostics:", page.evaluate("({status:window.__lastStatus,adds:window.__adds,ledger:localStorage.getItem(\"test-ledger\"),body:document.body.innerText})"))
        raise
    finally:
        browser.close()
