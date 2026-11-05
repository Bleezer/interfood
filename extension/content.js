/* Az oldal saját vezérlőin dolgozik; nincs közvetlen kosár-API vagy rendelés. */
(() => {
  "use strict";
  const core = globalThis.InterfoodCartCore;
  let accountId = null, payload = null, busy = false, generation = 0, timer = null;
  const attempted = new Set();
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const visible = element => !!element && element.getClientRects().length > 0;
  async function call(message) {
    const response = await chrome.runtime.sendMessage(message);
    if (!response?.ok) throw Error(response?.error || "Nem érhető el a kosársegéd.");
    return response;
  }
  function show(message) {
    if (!document.body) return;
    let box = document.getElementById("interfood-cart-status");
    if (!box) {
      box = document.createElement("aside");
      box.id = "interfood-cart-status";
      box.style.cssText = "position:fixed;bottom:16px;right:16px;max-width:360px;z-index:2147483647;background:#fff;color:#222;border:2px solid #26734d;border-radius:8px;padding:12px;font:14px sans-serif;box-shadow:0 2px 12px #0003";
      const label = document.createElement("div");
      label.dataset.statusText = "1";
      box.append(label);
      const pause = document.createElement("button");
      pause.type = "button";
      pause.textContent = "Automatika kikapcsolása";
      pause.addEventListener("click", () => chrome.storage.local.set({enabled: false}));
      box.append(pause);
      document.body.append(box);
    }
    const label = box.querySelector("[data-status-text]");
    if (label.textContent !== message) {
      label.textContent = message;
      call({type: "status", text: message}).catch(() => {});
    }
  }
  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(() => run().catch(error => show("Kosársegéd: " + error.message)), 300);
  }
  async function active(account, version) {
    const settings = await call({type: "settings"});
    if (accountId !== account || version !== generation ||
        settings.accountId !== account || !settings.enabled)
      throw Error("A kosárfeltöltés megszakítva.");
  }
  async function waitFor(getter, account, version, timeout = 10000) {
    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
      await active(account, version);
      const result = getter();
      if (result) return result;
      await sleep(100);
    }
    throw Error("Az oldal nem igazolta a várt állapotot; nem próbálkozom újra.");
  }
  function currentMenu(week) {
    if (!payload?.data || typeof payload.data !== "object") return false;
    const dates = Object.values(payload.data).flatMap(group =>
      (group.categories || []).flatMap(category => (category.items || []).map(item => item.date)));
    return dates.length > 0 && dates.every(day => typeof day === "string" && day >= week.start && day <= week.end);
  }
  async function selectWeek(week, account, version) {
    const selector = [...document.querySelectorAll('[aria-label^="Hét kiválasztása, jelenleg"]')].find(visible);
    if (!selector) return false;
    if (selector.getAttribute("aria-label") === "Hét kiválasztása, jelenleg kiválasztott hét: " + week.week)
      return true;
    await active(account, version);
    selector.click();
    const choice = await waitFor(() => [...document.querySelectorAll("[aria-label]")].find(element =>
      visible(element) && element.getAttribute("aria-label") === "Hét kiválasztása: " + week.week + ". hét"),
    account, version);
    if (choice.disabled || choice.getAttribute("aria-disabled") === "true")
      throw Error("A következő hét még nem rendelhető.");
    choice.click();
    return false;
  }
  function cardFor(item) {
    const cards = [...document.querySelectorAll('.food[data-menu-item-id="' + item.id + '"]')].filter(visible);
    return cards.length === 1 ? cards[0] : null;
  }
  function quantity(card) {
    const value = card?.querySelector(".food-middle-right-quantity")?.textContent.trim();
    return /^\d+$/.test(value || "") ? Number(value) : null;
  }
  async function fill(plan, account, version) {
    let added = 0, skipped = 0, uncertain = 0;
    for (const item of plan.items) {
      await active(account, version);
      const day = [...document.querySelectorAll("[data-date]")].find(element =>
        visible(element) && element.getAttribute("data-date") === item.date);
      if (!day) throw Error("Nem található rendelési nap: " + item.date);
      if (!day.classList.contains("active")) {
        (day.closest('ion-segment-button,button,[role="tab"]') || day).click();
      }
      const card = await waitFor(() => cardFor(item), account, version);
      const add = card.querySelector('button[aria-label^="Kosárhoz adás:"]');
      const amount = quantity(card);
      if (!add || add.disabled || card.classList.contains("disabled") || amount === null)
        throw Error("Ez a tétel most nem rendelhető: " + item.code);
      const claim = await call({type: "claim", accountId: account, weekStart: plan.week_start, itemId: item.id});
      if (!claim.claimed) {
        skipped++;
        if (claim.status !== "done") uncertain++;
        continue;
      }
      try {
        await active(account, version);
        // Újraolvassuk, hátha közben kézzel már a kosárba került.
        if (quantity(cardFor(item)) === 0) {
          const fresh = cardFor(item);
          if (!fresh || fresh.classList.contains("disabled")) throw Error("Az ételkártya megváltozott.");
          fresh.querySelector('button[aria-label^="Kosárhoz adás:"]').click();
          await waitFor(() => quantity(cardFor(item)) > 0, account, version);
          added++;
        } else if (quantity(cardFor(item)) === null) {
          throw Error("A kosármennyiség nem olvasható.");
        } else {
          skipped++;
        }
        await call({type: "finish", accountId: account, weekStart: plan.week_start, itemId: item.id, status: "done"});
      } catch (error) {
        await call({type: "finish", accountId: account, weekStart: plan.week_start, itemId: item.id, status: "uncertain"}).catch(() => {});
        throw error;
      }
      show("Kosársegéd: " + added + " hozzáadva, " + skipped + " már kezelt tétel.");
    }
    show("Kosársegéd kész: " + added + " hozzáadva, " + skipped + " már kezelt tétel." +
      (uncertain ? " " + uncertain + " korábbi bizonytalan tételt ellenőrizz kézzel." : "") +
      " Vedd ki, ami nem kell; a rendelést te véglegesíted.");
  }
  async function run() {
    if (busy || !accountId || !document.body) return;
    const week = core.nextWeek();
    const key = accountId + ":" + week.start;
    if (attempted.has(key)) return;
    busy = true;
    const account = accountId, version = generation;
    try {
      if (!(await call({type: "settings"})).enabled) return;
      show("Kosársegéd: a következő heti étlap ellenőrzése…");
      if (!await selectWeek(week, account, version) || !currentMenu(week)) return;
      attempted.add(key);
      const result = await call({type: "plan", accountId: account, payload});
      const plan = core.validatePlan(result.plan, week);
      await active(account, version);
      await fill(plan, account, version);
    } catch (error) {
      attempted.add(key);
      throw error;
    } finally {
      busy = false;
      if (generation !== version && accountId) schedule();
    }
  }
  window.addEventListener("message", event => {
    if (event.source !== window || event.origin !== location.origin ||
        event.data?.source !== "interfood-cart-bridge") return;
    if (event.data.type === "account") {
      const next = typeof event.data.accountId === "string" && /^[0-9]+$/.test(event.data.accountId)
        ? event.data.accountId : null;
      if (next !== accountId) { accountId = next; generation++; }
      call({type: "account", accountId: next}).then(schedule).catch(error => show(error.message));
    }
    if (event.data.type === "menu") payload = event.data.payload;
    schedule();
  });
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    if (changes.observedAccount || changes.authEpoch) {
      generation++;
      if (changes.observedAccount && changes.observedAccount.newValue !== accountId && accountId)
        show("Kosársegéd: másik fülön belépés vagy kilépés történt. Frissítsd az oldalt.");
    }
    if (!changes.enabled) return;
    generation++;
    if (changes.enabled.newValue === false) show("Kosársegéd kikapcsolva.");
    else { attempted.clear(); schedule(); }
  });
  function start() {
    new MutationObserver(schedule).observe(document.body, {childList: true, subtree: true});
    window.postMessage({source: "interfood-cart-content", type: "state"}, location.origin);
    schedule();
  }
  if (document.body) start();
  else document.addEventListener("DOMContentLoaded", start, {once: true});
})();
