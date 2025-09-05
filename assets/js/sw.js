// Service Worker for caching static assets during development
const CACHE_NAME = 'worldcoffeetour-assets-v1';
const CACHE_URLS = [
  // Cache all image assets
];

// Cache images on the fly
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // Only cache image assets from our domain
  if (url.origin === location.origin && url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
    event.respondWith(
      caches.open(CACHE_NAME).then(cache => {
        return cache.match(event.request).then(response => {
          if (response) {
            // Serve from cache
            console.log('Serving from cache:', url.pathname);
            return response;
          }
          
          // Fetch and cache
          return fetch(event.request).then(fetchResponse => {
            if (fetchResponse.ok) {
              cache.put(event.request, fetchResponse.clone());
              console.log('Cached image:', url.pathname);
            }
            return fetchResponse;
          });
        });
      })
    );
  }
});

// Clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});