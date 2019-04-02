var CACHE_NAME = 'faceNLZ-cache-v1';
var urlsToCache = ['/wasm/20190326/cybert.data', '/wasm/20190326/cybert.wasm'];

self.addEventListener('activate', function (event) {
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', function (event) {
    var path = new URL(event.request.url).pathname;

    if (!urlsToCache.includes(path)) {
        return;
    }

    event.respondWith(caches.match(event.request).then(function (response) {
        if (response) {
            return response;
        }

        var fetchRequest = event.request.clone();

        return fetch(fetchRequest).then(function (response) {
            if (!response || response.status !== 200) {
                return response;
            }

            var responseToCache = response.clone();

            caches.open(CACHE_NAME).then(function (cache) {
                return cache.put(event.request, responseToCache);
            });

            return response;
        });
    }));
});
