const CACHE_NAME = "halalcheck-v1";
const OFFLINE_ASSETS = [
  "/web/",
  "/web/index.html",
  "/web/css/style.css",
  "/web/js/api.js",
  "/web/js/scanner.js",
  "/web/js/app.js",
  "/web/manifest.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_ASSETS)));
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches
      .match(event.request)
      .then((cached) => cached || fetch(event.request).catch(() => caches.match("/web/index.html")))
  );
});
