const CACHE_NAME = 'faceNLZ-cache-v1';
let urlsToCache = [
    '/wasm/20190123/cybert.data',
    '/wasm/20190123/cybert.wasm'
];

self.addEventListener('activate', event => {
    event.waitUntil(clients.claim())
});

self.addEventListener('fetch', function(event) {
    let path = new URL(event.request.url).pathname;

    if (!urlsToCache.includes(path)) {
        return
    }

    event.respondWith(
        caches
            .match(event.request)
            .then(response => {
                if (response) { return response }

                let fetchRequest = event.request.clone();

                return fetch(fetchRequest).then(response => {
                    if(!response || response.status !== 200) {
                        return response
                    }

                    let responseToCache =
                        response.clone();

                    caches.open(CACHE_NAME)
                        .then(cache =>
                            cache.put(event.request, responseToCache));

                    return response
                })
            })
    )
});
