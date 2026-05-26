const CACHE_NAME = "luzagenda-v1";
const CORE_ASSETS = ["/", "/static/css/styles.css", "/static/js/app.js"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)));
});

self.addEventListener("fetch", (event) => {
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
