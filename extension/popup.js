"use strict";
(async () => {
  const saved = await chrome.storage.local.get(["enabled", "lastStatus"]);
  document.getElementById("enabled").checked = saved.enabled !== false;
  document.getElementById("status").textContent = saved.lastStatus ||
    "Nyisd meg az Interfood étlapját, és jelentkezz be. Első használat előtt futtasd a helyi telepítőt.";
})();
document.getElementById("enabled").addEventListener("change", event =>
  chrome.storage.local.set({enabled: event.target.checked}));
