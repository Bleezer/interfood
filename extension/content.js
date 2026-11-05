/* Kézi, személyenként egyszeri kosárfeltöltés; az oldal saját pluszgombjaival. */
(() => {
  "use strict";
  const core = globalThis.InterfoodCartCore;
  let accountId = null, payload = null, busy = false, generation = 0, timer = null;
  let profiles = null, selectedProfile = "self", lastHint = null, helperEnabled = true;
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const visible = element => !!element && element.getClientRects().length > 0;
  async function call(message) {
    const response = await chrome.runtime.sendMessage(message);
    if (!response?.ok) throw Error(response?.error || "Nem érhető el a kosársegéd.");
    return response;
  }
  function panel() {
    if (!document.body) return null;
    let box = document.getElementById("interfood-cart-status");
    if (!box) {
      box = document.createElement("aside");
      box.id = "interfood-cart-status";
      box.style.cssText = "position:fixed;bottom:16px;right:16px;max-width:380px;z-index:2147483647;background:#fff;color:#222;border:2px solid #26734d;border-radius:8px;padding:12px;font:14px sans-serif;box-shadow:0 2px 12px #0003";
      const label = document.createElement("div");
      label.dataset.statusText = "1";
      box.append(label);
      const person = document.createElement("select");
      person.id = "interfood-cart-person";
      person.setAttribute("aria-label", "Kinek az ajánlásait tegyem a kosárba?");
      person.style.cssText = "display:block;margin:8px 0;max-width:100%";
      person.addEventListener("change", () => {
        if (busy) return;
        selectedProfile = person.value;
        generation++;
        lastHint = null;
        chrome.storage.local.set({selectedProfileId: selectedProfile});
        schedule();
      });
      box.append(person);
      const start = document.createElement("button");
      start.id = "interfood-cart-start";
      start.type = "button";
      start.textContent = "Kosárba teszem";
      start.disabled = true;
      start.addEventListener("click", () => run().catch(error => show("Kosársegéd: " + error.message)));
      box.append(start);
      document.body.append(box);
    }
    const select = box.querySelector("#interfood-cart-person");
    const signature = JSON.stringify(profiles);
    if (select.dataset.signature !== signature) {
      select.replaceChildren();
      if (profiles) {
        for (const profile of profiles) {
          const option = document.createElement("option");
          option.value = profile.id;
          option.disabled = !profile.configured;
          option.textContent = profile.name + (profile.configured ? "" : " — még nincs beállítva");
          select.append(option);
        }
      } else {
        const option = document.createElement("option");
        option.textContent = "Profilok betöltése…";
        select.append(option);
      }
      select.dataset.signature = signature;
    }
    select.value = selectedProfile;
    select.disabled = busy || !profiles;
    box.querySelector("#interfood-cart-start").disabled = busy || !helperEnabled || !accountId ||
      !profiles?.some(profile => profile.id === selectedProfile && profile.configured);
    return box;
  }
  function show(message) {
    const label = panel()?.querySelector("[data-status-text]");
    if (label && label.textContent !== message) {
      label.textContent = message;
      call({type: "status", text: message}).catch(() => {});
    }
  }
  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(() => refresh().catch(error => show("Kosársegéd: " + error.message)), 300);
  }
  async function refresh() {
    if (!document.body || busy) return;
    const settings = await call({type: "settings"});
    if (busy) return;
    helperEnabled = settings.enabled;
    if (profiles?.some(profile => profile.id === settings.profileId && profile.configured))
      selectedProfile = settings.profileId;
    const box = panel();
    box.querySelector("#interfood-cart-start").disabled ||= !settings.enabled;
    const hint = [settings.enabled, accountId, selectedProfile, !!profiles].join(":");
    if (hint === lastHint) return;
    lastHint = hint;
    show(!settings.enabled ? "Kosársegéd kikapcsolva." : !accountId
      ? "A kosárfeltöltéshez jelentkezz be. Semmit nem teszek be automatikusan."
      : "Válassz személyt, majd nyomd meg a Kosárba teszem gombot.");
  }
  async function active(account, version, profile) {
    const settings = await call({type: "settings"});
    if (accountId !== account || version !== generation || selectedProfile !== profile ||
        settings.accountId !== account || !settings.enabled)
      throw Error("A kosárfeltöltés megszakítva.");
  }
  async function waitFor(getter, account, version, profile, timeout = 10000) {
    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
      await active(account, version, profile);
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
  async function selectWeek(week, account, version, profile) {
    const selector = [...document.querySelectorAll('[aria-label^="Hét kiválasztása, jelenleg"]')].find(visible);
    if (!selector) throw Error("Nyisd meg az Interfood étlapját.");
    if (selector.getAttribute("aria-label") === "Hét kiválasztása, jelenleg kiválasztott hét: " + week.week) return;
    await active(account, version, profile);
    selector.click();
    const choice = await waitFor(() => [...document.querySelectorAll("[aria-label]")].find(element =>
      visible(element) && element.getAttribute("aria-label") === "Hét kiválasztása: " + week.week + ". hét"),
    account, version, profile);
    if (choice.disabled || choice.getAttribute("aria-disabled") === "true")
      throw Error("A következő hét még nem rendelhető.");
    choice.click();
  }
  function cardFor(item) {
    const cards = [...document.querySelectorAll('.food[data-menu-item-id="' + item.id + '"]')].filter(visible);
    return cards.length === 1 ? cards[0] : null;
  }
  function quantity(card) {
    const value = card?.querySelector(".food-middle-right-quantity")?.textContent.trim();
    return /^\d+$/.test(value || "") ? Number(value) : null;
  }
  async function fill(plan, account, version, profile) {
    let added = 0, skipped = 0;
    const operation = {accountId: account, weekStart: plan.week_start, profileId: profile};
    for (const item of plan.items) {
      await active(account, version, profile);
      const day = [...document.querySelectorAll("[data-date]")].find(element =>
        visible(element) && element.getAttribute("data-date") === item.date);
      if (!day) throw Error("Nem található rendelési nap: " + item.date);
      if (!day.classList.contains("active"))
        (day.closest('ion-segment-button,button,[role="tab"]') || day).click();
      const card = await waitFor(() => cardFor(item), account, version, profile);
      const add = card.querySelector('button[aria-label^="Kosárhoz adás:"]');
      if (!add || add.disabled || card.classList.contains("disabled") || quantity(card) === null)
        throw Error("Ez a tétel most nem rendelhető: " + item.code);
      const claim = await call({type: "claim", ...operation, itemId: item.id});
      if (!claim.claimed) {
        if (claim.status !== "done") throw Error("Korábbi bizonytalan kosártétel; ellenőrizd kézzel.");
        skipped++;
        continue;
      }
      try {
        await active(account, version, profile);
        const before = quantity(cardFor(item));
        if (before === null) throw Error("A kosármennyiség nem olvasható.");
        if (before === 0 || claim.addOne) {
          const fresh = cardFor(item), button = fresh?.querySelector('button[aria-label^="Kosárhoz adás:"]');
          if (!fresh || fresh.classList.contains("disabled") || !button || button.disabled)
            throw Error("Az ételkártya megváltozott.");
          button.click();
          await waitFor(() => quantity(cardFor(item)) >= before + 1, account, version, profile);
          added++;
        } else skipped++;
        await call({type: "finish", ...operation, itemId: item.id, status: "done"});
      } catch (error) {
        await call({type: "finish", ...operation, itemId: item.id, status: "uncertain"}).catch(() => {});
        throw error;
      }
      show("Kosársegéd: " + added + " hozzáadva, " + skipped + " már meglévő adag.");
    }
    return {added, skipped};
  }
  function already(status) {
    show(status === "done" ? "Ennek a személynek erre a hétre már megtörtént a kosárfeltöltés."
      : "Ennek a személynek erre a hétre már indult feltöltés. A bizonytalan eredményt ellenőrizd kézzel; nem teszek be újra.");
  }
  async function run() {
    if (busy || !accountId || !profiles?.some(p => p.id === selectedProfile && p.configured)) return;
    busy = true;
    panel();
    const week = core.nextWeek(), account = accountId, version = generation, profile = selectedProfile;
    const operation = {accountId: account, weekStart: week.start, profileId: profile};
    let started = false;
    try {
      await active(account, version, profile);
      const previous = await call({type: "run-status", ...operation});
      if (previous.status !== "new") { already(previous.status); return; }
      show("Kosársegéd: a kiválasztott személy következő heti étlapjának ellenőrzése…");
      await selectWeek(week, account, version, profile);
      await waitFor(() => currentMenu(week), account, version, profile);
      const result = await call({type: "plan", ...operation, payload});
      const plan = core.validatePlan(result.plan, week, profile);
      if (!plan.items.length) { show("Nincs megfelelő kosárjelölt ehhez a profilhoz."); return; }
      await active(account, version, profile);
      const begin = await call({type: "begin", ...operation});
      if (!begin.started) { already(begin.status); return; }
      started = true;
      const counts = await fill(plan, account, version, profile);
      await call({type: "finish-run", ...operation, status: "done"});
      started = false;
      show("Kosársegéd kész: " + counts.added + " hozzáadva, " + counts.skipped +
        " már meglévő adag. Vedd ki, ami nem kell; a rendelést te véglegesíted.");
    } catch (error) {
      if (started) await call({type: "finish-run", ...operation, status: "uncertain"}).catch(() => {});
      throw error;
    } finally {
      busy = false;
      panel();
    }
  }
  window.addEventListener("message", event => {
    if (event.source !== window || event.origin !== location.origin || event.data?.source !== "interfood-cart-bridge") return;
    if (event.data.type === "account") {
      const next = typeof event.data.accountId === "string" && /^[0-9]+$/.test(event.data.accountId)
        ? event.data.accountId : null;
      if (next !== accountId) { accountId = next; generation++; lastHint = null; }
      call({type: "account", accountId: next}).then(schedule).catch(error => show(error.message));
    }
    if (event.data.type === "menu") payload = event.data.payload;
    schedule();
  });
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    if (changes.enabled) helperEnabled = changes.enabled.newValue !== false;
    if (changes.observedAccount || changes.authEpoch || changes.enabled ||
        (changes.selectedProfileId && changes.selectedProfileId.newValue !== selectedProfile)) {
      generation++; lastHint = null;
      if (busy) show("A kosárfeltöltés megszakítva; a fiók vagy profil megváltozott.");
      schedule();
    }
  });
  async function start() {
    new MutationObserver(schedule).observe(document.body, {childList: true, subtree: true});
    panel();
    window.postMessage({source: "interfood-cart-content", type: "state"}, location.origin);
    try {
      const result = await call({type: "profiles"});
      if (!Array.isArray(result.profiles) || !result.profiles.length) throw Error("Nem érkezett profillista.");
      profiles = result.profiles;
      if (!profiles.some(profile => profile.id === selectedProfile && profile.configured))
        selectedProfile = profiles.find(profile => profile.configured)?.id || "";
      panel(); schedule();
    } catch (error) { show("Kosársegéd: " + error.message); }
  }
  if (document.body) start();
  else document.addEventListener("DOMContentLoaded", start, {once: true});
})();
