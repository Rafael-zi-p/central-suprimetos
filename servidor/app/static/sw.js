// Central de Suprimentos — service worker (instalação como aplicativo)
// Estratégia: a página SEMPRE vem da rede quando há internet (nunca fica presa
// numa versão antiga); a cópia guardada só é usada sem conexão. Dados do
// servidor e do TOTVS nunca são guardados aqui.
const CACHE = "pz-servidor-v1";
const BASICOS = ["./", "./index.html", "./xlsx-0.20.3.full.min.js", "./qrcode-1.4.4.js", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./apple-touch-icon.png"];

self.addEventListener("install", (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(BASICOS)).catch(() => {}));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;          // servidor, CDNs: direto na rede
  if (url.pathname.startsWith("/totvs/")) return;
  if (/^\/(api|auth|logout|login|getAToken|saude)(\/|$)/.test(url.pathname)) return;   // servidor: sempre direto            // proxy do TOTVS: nunca em cache

  const pagina = req.mode === "navigate" || url.pathname === "/" || url.pathname.endsWith(".html");
  if (pagina) {
    e.respondWith(
      fetch(req).then((r) => {
        if (r && r.ok) { const copia = r.clone(); caches.open(CACHE).then((c) => c.put("./index.html", copia)); }
        return r;
      }).catch(() => caches.match("./index.html").then((m) => m || caches.match("./")))
    );
    return;
  }
  e.respondWith(
    caches.match(req).then((m) => m || fetch(req).then((r) => {
      if (r && r.ok && BASICOS.some((b) => url.pathname.endsWith(b.replace("./", "/")))) { const copia = r.clone(); caches.open(CACHE).then((c) => c.put(req, copia)); }
      return r;
    }))
  );
});
