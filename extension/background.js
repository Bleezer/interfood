"use strict";
importScripts("core.js");
const HOST = "hu.interfood.menu_helper";
let queue = Promise.resolve();

async function handle(message, sender) {
  if (sender.id !== chrome.runtime.id || sender.frameId !== 0 || !sender.tab ||
      new URL(sender.url).origin !== "https://rendel.interfood.hu" ||
      !message || typeof message !== "object") throw Error("Nem engedélyezett kérés.");
  if (message.type === "account") {
    const account = message.accountId;
    if (account !== null && (typeof account !== "string" || !/^[1-9][0-9]*$/.test(account)))
      throw Error("Hibás fiókjelzés.");
    const saved = await chrome.storage.local.get(["observedAccount", "authEpoch"]);
    if (saved.observedAccount !== account) await chrome.storage.local.set({
      observedAccount: account, authEpoch: (saved.authEpoch || 0) + 1
    });
    return {ok: true};
  }
  if (message.type === "settings") {
    const settings = await chrome.storage.local.get(["enabled", "observedAccount"]);
    return {ok: true, enabled: settings.enabled !== false, accountId: settings.observedAccount ?? null};
  }
  if (message.type === "status") {
    if (typeof message.text !== "string") throw Error("Hibás állapot.");
    await chrome.storage.local.set({lastStatus: message.text.slice(0, 500)});
    return {ok: true};
  }
  const account = String(message.accountId);
  const week = InterfoodCartCore.nextWeek();
  const key = InterfoodCartCore.ledgerKey(account, week.start);
  if ((await chrome.storage.local.get("observedAccount")).observedAccount !== account)
    throw Error("A bejelentkezett fiók másik fülön megváltozott; frissítsd az oldalt.");
  const planKey = "plan:" + account + ":" + week.start;
  if (message.type === "plan") {
    if ((await chrome.storage.local.get("enabled")).enabled === false)
      throw Error("A kosársegéd ki van kapcsolva.");
    let response;
    try {
      response = await chrome.runtime.sendNativeMessage(HOST, {type: "plan", payload: message.payload});
    } catch {
      throw Error("A helyi kosársegéd nem érhető el. Futtasd a telepítőt.");
    }
    if (!response || response.ok !== true) throw Error(response?.error || "Nem készült kosárterv.");
    const plan = InterfoodCartCore.validatePlan(response.plan, week);
    await chrome.storage.local.set({[planKey]: plan});
    return {ok: true, plan};
  }
  if (message.weekStart !== week.start) throw Error("A hét közben megváltozott; frissítsd az oldalt.");
  const stored = await chrome.storage.local.get([key, planKey, "enabled"]);
  if (stored.enabled === false && message.type === "claim") throw Error("A kosársegéd ki van kapcsolva.");
  const plan = stored[planKey];
  if (!plan || !plan.items.some(item => item.id === message.itemId)) throw Error("A tétel nincs a kosártervben.");
  const ledger = stored[key] || {};
  if (message.type === "claim") {
    const claimed = InterfoodCartCore.claim(ledger, message.itemId, sender.tab.id);
    if (claimed) await chrome.storage.local.set({[key]: ledger});
    return {ok: true, claimed, status: ledger[message.itemId].status};
  }
  if (message.type === "finish") {
    InterfoodCartCore.finish(ledger, message.itemId, sender.tab.id, message.status);
    await chrome.storage.local.set({[key]: ledger});
    return {ok: true};
  }
  throw Error("Ismeretlen művelet.");
}

chrome.runtime.onMessage.addListener((message, sender, reply) => {
  queue = queue.catch(() => {}).then(() => handle(message, sender));
  queue.then(reply, error => reply({ok: false, error: error.message || "A kosársegéd leállt."}));
  return true;
});
