const CACHE_NAME = "creovanta-shell-v1";
const SHELL = ["/", "/app", "/static/manifest.webmanifest", "/static/icons/icon-192.svg", "/static/icons/icon-512.svg"];
self.addEventListener("install", (event) => { event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener("activate", (event) => { event.waitUntil(self.clients.claim()); });
self.addEventListener("fetch", (event) => { if (event.request.method !== "GET") return; event.respondWith(fetch(event.request).catch(() => caches.match(event.request))); });
