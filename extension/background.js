"use strict";
importScripts("core.js");
const HOST = "hu.interfood.menu_helper";
let queue = Promise.resolve();

async function native(request) {
  let response;
  try { response = await chrome.runtime.sendNativeMessage(HOST, request); }
  catch { throw Error("A helyi kosársegéd nem érhető el. Futtasd a telepítőt."); }
  if (!response || response.ok !== true) throw Error(response?.error || "Nem készült kosárterv.");
  return response;
}

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
    const settings = await chrome.storage.local.get(["enabled", "observedAccount", "selectedProfileId"]);
    return {ok: true, enabled: settings.enabled !== false,
      accountId: settings.observedAccount ?? null, profileId: settings.selectedProfileId || "self"};
  }
  if (message.type === "status") {
    if (typeof message.text !== "string") throw Error("Hibás állapot.");
    await chrome.storage.local.set({lastStatus: message.text.slice(0, 500)});
    return {ok: true};
  }
  if (message.type === "profiles") return native({type: "profiles"});

  const account = String(message.accountId), profile = message.profileId;
  if (typeof profile !== "string" || !/^[a-z][a-z0-9_-]{0,31}$/.test(profile))
    throw Error("Válassz személyt a kosárfeltöltéshez.");
  const week = InterfoodCartCore.nextWeek();
  const oldKey = InterfoodCartCore.ledgerKey(account, week.start);
  const key = InterfoodCartCore.ledgerKey(account, week.start, profile);
  const runKey = "cart-run:" + account + ":" + week.start + ":" + profile;
  const sharedKey = "cart-contributors:" + account + ":" + week.start;
  const planKey = "plan:" + account + ":" + week.start + ":" + profile;
  if ((await chrome.storage.local.get("observedAccount")).observedAccount !== account)
    throw Error("A bejelentkezett fiók másik fülön megváltozott; frissítsd az oldalt.");
  if (message.weekStart !== week.start) throw Error("A hét közben megváltozott; frissítsd az oldalt.");

  // A régi automatikus kosár a saját profilé; az átállás nem töltheti újra.
  const selfKey = InterfoodCartCore.ledgerKey(account, week.start, "self");
  const selfRunKey = "cart-run:" + account + ":" + week.start + ":self";
  let state = await chrome.storage.local.get([key, runKey, selfKey, selfRunKey, sharedKey, oldKey, "enabled", planKey]);
  if (!state[selfRunKey] && Object.keys(state[oldKey] || {}).length) {
    const legacy = state[oldKey], contributors = state[sharedKey] || {};
    for (const id of Object.keys(legacy)) contributors[id] = [...new Set([...(contributors[id] || []), "self"])];
    const status = Object.values(legacy).every(item => item.status === "done") ? "done" : "uncertain";
    await chrome.storage.local.set({[selfKey]: legacy, [selfRunKey]: {status, legacy: true}, [sharedKey]: contributors});
    state = {...state, [selfKey]: legacy, [selfRunKey]: {status, legacy: true}, [sharedKey]: contributors};
  }
  if (message.type === "run-status") return {ok: true, status: state[runKey]?.status || "new"};
  if (message.type === "plan") {
    if (state.enabled === false) throw Error("A kosársegéd ki van kapcsolva.");
    const response = await native({type: "plan", payload: message.payload, profile_id: profile});
    const plan = InterfoodCartCore.validatePlan(response.plan, week, profile);
    await chrome.storage.local.set({[planKey]: plan});
    return {ok: true, plan};
  }
  if (message.type === "begin") {
    if (state[runKey]) return {ok: true, started: false, status: state[runKey].status};
    if (state.enabled === false || !state[planKey]) throw Error("Nincs indítható kosárterv.");
    await chrome.storage.local.set({[runKey]: {status: "running", tabId: sender.tab.id}});
    return {ok: true, started: true};
  }
  const run = state[runKey], plan = state[planKey];
  if (!run || run.status !== "running" || run.tabId !== sender.tab.id || !plan)
    throw Error("Erre a személyre és hétre nincs saját futó feltöltés.");
  const ledger = state[key] || {};
  if (message.type === "finish-run") {
    if (!["done", "uncertain"].includes(message.status)) throw Error("Hibás futási állapot.");
    if (message.status === "done" && !plan.items.every(item => ledger[item.id]?.status === "done"))
      throw Error("Nem minden tétel eredménye igazolt.");
    await chrome.storage.local.set({[runKey]: {...run, status: message.status}});
    return {ok: true};
  }
  if (!plan.items.some(item => item.id === message.itemId)) throw Error("A tétel nincs a kosártervben.");
  if (message.type === "claim") {
    if (state.enabled === false) throw Error("A kosársegéd ki van kapcsolva.");
    const claimed = InterfoodCartCore.claim(ledger, message.itemId, sender.tab.id);
    const contributors = state[sharedKey] || {}, previous = contributors[message.itemId] || [];
    const addOne = previous.some(identity => identity !== profile);
    if (claimed) {
      contributors[message.itemId] = [...new Set([...previous, profile])];
      await chrome.storage.local.set({[key]: ledger, [sharedKey]: contributors});
    }
    return {ok: true, claimed, status: ledger[message.itemId].status, addOne};
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
