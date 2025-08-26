self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('stockgame-v1').then((cache) => cache.addAll([
      '/static/leaderboard.html',
      '/static/styles.css',
      '/static/app.js',
      '/static/manifest.json'
    ]))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((resp) => resp || fetch(event.request))
  );
});
