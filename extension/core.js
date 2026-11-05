/* Közös, böngészőtől független ellenőrzések és tartós tételállapotok. */
(function (root) {
  "use strict";
  function nextWeek(now = new Date()) {
    const parts = Object.fromEntries(new Intl.DateTimeFormat("en-CA", {
      timeZone: "Europe/Budapest", year: "numeric", month: "2-digit", day: "2-digit"
    }).formatToParts(now).map(p => [p.type, p.value]));
    const monday = new Date(Date.UTC(+parts.year, +parts.month - 1, +parts.day));
    monday.setUTCDate(monday.getUTCDate() + ((8 - monday.getUTCDay()) % 7 || 7));
    const thursday = new Date(monday);
    thursday.setUTCDate(thursday.getUTCDate() + 3);
    const year = thursday.getUTCFullYear();
    const week = Math.ceil((((thursday - Date.UTC(year, 0, 1)) / 86400000) + 1) / 7);
    const sunday = new Date(monday);
    sunday.setUTCDate(sunday.getUTCDate() + 6);
    return {start: monday.toISOString().slice(0, 10), end: sunday.toISOString().slice(0, 10), week, year};
  }
  function validatePlan(plan, expected = nextWeek(), profile = null) {
    if (!plan || plan.version !== 1 || plan.week_start !== expected.start ||
        !Array.isArray(plan.items) || plan.items.length > 18) throw Error("Hibás vagy régi heti kosárterv.");
    if (profile !== null && plan.profile_id !== profile) throw Error("Wrong profile in cart plan.");
    const ids = new Set();
    for (const item of plan.items) {
      if (!item || !Number.isSafeInteger(item.id) || item.id <= 0 || ids.has(item.id) ||
          item.quantity !== 1 || typeof item.date !== "string" ||
          !/^\d{4}-\d{2}-\d{2}$/.test(item.date) || item.date < expected.start || item.date >= expected.end ||
          typeof item.name !== "string" || !item.name.trim() || typeof item.code !== "string" || !item.code.trim())
        throw Error("Érvénytelen kosártétel.");
      ids.add(item.id);
    }
    return plan;
  }
  function ledgerKey(account, week, profile = null) {
    if (!/^[0-9]+$/.test(String(account)) || !/^\d{4}-\d{2}-\d{2}$/.test(week)) throw Error("Hibás fiók vagy hét.");
    if (profile !== null && (typeof profile !== "string" || !/^[a-z][a-z0-9_-]{0,31}$/.test(profile))) throw Error("Invalid profile.");
    return "cart-ledger:" + account + ":" + week + (profile === null ? "" : ":" + profile);
  }
  function claim(ledger, id, tabId) {
    if (Object.hasOwn(ledger, id)) return false;
    ledger[id] = {status: "pending", tabId, at: Date.now()};
    return true;
  }
  function finish(ledger, id, tabId, status) {
    if (!["done", "uncertain"].includes(status) || !ledger[id] ||
        ledger[id].status !== "pending" || ledger[id].tabId !== tabId) throw Error("Nem saját függő tétel.");
    ledger[id] = {...ledger[id], status};
  }
  const api = {nextWeek, validatePlan, ledgerKey, claim, finish};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.InterfoodCartCore = api;
})(globalThis);
