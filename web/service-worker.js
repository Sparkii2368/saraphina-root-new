self.addEventListener('install', (e) => {
  e.waitUntil(caches.open('saraphina-cache-v1').then(cache => cache.addAll([
    '/dashboard',
    '/dashboard/manifest.json'
  ])));
});
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((resp) => resp || fetch(e.request))
  );
});
