/* MAIN world: csak étlapot és számszerű belépésjelzést figyel, headereket nem. */
(() => {
  "use strict";
  let lastMenu = null, accountId = null;
  const publish = (type, data) => window.postMessage({source: "interfood-cart-bridge", type, ...data}, location.origin);
  function inspect(url, status, body) {
    let address;
    try { address = new URL(url, location.href); } catch { return; }
    if (address.origin !== "https://ia.interfood.hu") return;
    if (address.pathname === "/api/v1/logout") {
      accountId = null;
      publish("account", {accountId});
      return;
    }
    if (address.pathname === "/api/v1/user") {
      const id = body?.data?.id;
      accountId = status >= 200 && status < 300 && /^[1-9][0-9]*$/.test(String(id)) ? String(id) : null;
      publish("account", {accountId});
    }
    if (address.pathname === "/api/v1/menu" && status >= 200 && status < 300 && body?.data) {
      lastMenu = body;
      publish("menu", {payload: lastMenu});
    }
  }
  function relevant(url) {
    try {
      const u = new URL(url, location.href);
      return u.origin === "https://ia.interfood.hu" &&
        ["/api/v1/user", "/api/v1/menu", "/api/v1/logout"].includes(u.pathname);
    } catch { return false; }
  }
  function invalidate() {
    accountId = null;
    publish("account", {accountId});
  }
  function authMutation(url) {
    try {
      const address = new URL(url, location.href);
      return address.origin === "https://ia.interfood.hu" &&
        ["/api/v1/login", "/api/v1/logout"].includes(address.pathname);
    } catch { return false; }
  }
  window.addEventListener("storage", invalidate);
  const originalFetch = window.fetch;
  window.fetch = async function (...args) {
    if (authMutation(typeof args[0] === "string" ? args[0] : args[0]?.url)) invalidate();
    const response = await originalFetch.apply(this, args);
    if (relevant(response.url)) response.clone().json()
      .then(body => inspect(response.url, response.status, body)).catch(() => {});
    return response;
  };
  const open = XMLHttpRequest.prototype.open;
  const send = XMLHttpRequest.prototype.send;
  const urls = new WeakMap();
  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    urls.set(this, String(url));
    return open.call(this, method, url, ...rest);
  };
  XMLHttpRequest.prototype.send = function (...args) {
    if (authMutation(urls.get(this))) invalidate();
    if (relevant(urls.get(this))) this.addEventListener("load", () => {
      try {
        const body = this.responseType === "json" ? this.response : JSON.parse(this.responseText);
        inspect(this.responseURL || urls.get(this), this.status, body);
      } catch {}
    }, {once: true});
    return send.apply(this, args);
  };
  window.addEventListener("message", event => {
    if (event.source !== window || event.origin !== location.origin ||
        event.data?.source !== "interfood-cart-content" || event.data.type !== "state") return;
    publish("account", {accountId});
    if (lastMenu) publish("menu", {payload: lastMenu});
  });
})();
