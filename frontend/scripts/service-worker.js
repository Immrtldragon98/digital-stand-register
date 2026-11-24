/* CACHE and ASSETS are supplied by the static build. No runtime API caching. */
const allowed = new Set(ASSETS);
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
  // Activate after existing tabs close, so bundles from different builds never mix.
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys
    .filter(key => key.startsWith('dsr-shell-') && key !== CACHE).map(key => caches.delete(key)))));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin) return;
  let asset = url.pathname;
  if (event.request.mode === 'navigate') {
    asset = asset.endsWith('/') ? asset + 'index.html' : asset;
    if (!allowed.has(asset)) asset = url.pathname.replace(/\/$/, '') + '/index.html';
  }
  if (!allowed.has(asset)) return;
  event.respondWith(fetch(event.request).catch(async () => {
    const cached = await (await caches.open(CACHE)).match(asset);
    return cached || Response.error();
  }));
});
