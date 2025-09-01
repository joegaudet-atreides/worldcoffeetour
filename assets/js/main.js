// Map initialization for index page
if (document.getElementById('map')) {
    // Use global mainMap variable so other scripts can access it
    window.mainMap = L.map('map', {
        zoomAnimation: true,
        fadeAnimation: false,
        markerZoomAnimation: false,
        inertia: false,          // Disable momentum scrolling
        bounceAtZoomLimits: false, // Prevent bouncing at zoom limits
        maxBoundsViscosity: 0.0   // Remove bounce effect
    }).setView([30, 0], 2);
    const map = window.mainMap;
    
    const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20,
        keepBuffer: 6,           // Keep even more tiles loaded
        updateWhenZooming: false, // Don't update tiles while zooming
        updateInterval: 200,     // Longer batch intervals
        zoomAnimationThreshold: 2, // Animate for smaller zoom differences
        fadeAnimation: false,    // Disable fade to reduce flashing
        zoomReverse: false,      // Don't reverse zoom direction
        detectRetina: true       // Use high-DPI tiles when available
    }).addTo(map);
    
    // Store tile layer reference globally for prefetching
    window.mainTileLayer = tileLayer;

    // Custom coffee cup marker
    const coffeeIcon = L.divIcon({
        html: '<div style="background: #d4a574; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #0a0a0a; font-size: 16px; box-shadow: 0 2px 6px rgba(212, 165, 116, 0.4);">☕</div>',
        iconSize: [30, 30],
        className: 'coffee-marker'
    });

    // Add markers from coffee posts data
    if (typeof coffeePostsData !== 'undefined') {
        const markers = [];
        coffeePostsData.forEach(post => {
            if (post.latitude && post.longitude) {
                const marker = L.marker([post.latitude, post.longitude], { icon: coffeeIcon })
                    .addTo(map)
                    .bindPopup(`
                        <div style="text-align: center; min-width: 150px; color: #fff;">
                            <strong>${post.title}</strong><br>
                            ${post.city}, ${post.country}<br>
                            <a href="${post.url}" style="color: #d4a574;">View Post →</a>
                        </div>
                    `);
                markers.push(marker);
            }
        });

        // Fit map to show all markers
        if (markers.length > 0) {
            const group = new L.featureGroup(markers);
            map.fitBounds(group.getBounds().pad(0.1));
            
            // Start prefetching tiles after initial load
            setTimeout(() => {
                prefetchTilesForCoffeePosts(coffeePostsData);
            }, 2000);
        }
    }
}

// Map for individual post page
if (document.getElementById('post-map')) {
    const postMapEl = document.getElementById('post-map');
    const lat = parseFloat(postMapEl.dataset.lat);
    const lng = parseFloat(postMapEl.dataset.lng);
    const title = postMapEl.dataset.title;
    
    if (lat && lng) {
        const postMap = L.map('post-map').setView([lat, lng], 15);
        
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(postMap);

        const coffeeIcon = L.divIcon({
            html: '<div style="background: #d4a574; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #0a0a0a; font-size: 16px; box-shadow: 0 2px 6px rgba(212, 165, 116, 0.4);">☕</div>',
            iconSize: [30, 30],
            className: 'coffee-marker'
        });

        L.marker([lat, lng], { icon: coffeeIcon })
            .addTo(postMap)
            .bindPopup(title)
            .openPopup();
    }
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Lazy loading for images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });

    document.querySelectorAll('img.lazy').forEach(img => {
        imageObserver.observe(img);
    });
}

// Tile prefetching system
function prefetchTilesForCoffeePosts(coffeePosts) {
    if (!window.mainTileLayer || !coffeePosts) return;
    
    console.log('Starting tile prefetch for', coffeePosts.length, 'coffee posts');
    
    // Group posts by regions to calculate bounds
    const regions = {};
    const countries = {};
    const cities = {};
    
    coffeePosts.forEach(post => {
        if (!post.latitude || !post.longitude) return;
        
        const continent = post.continent?.toLowerCase().replace(/\s/g, '-');
        const country = post.country;
        const city = post.city;
        
        // Group by continent
        if (continent && continent !== 'unknown') {
            if (!regions[continent]) regions[continent] = [];
            regions[continent].push([post.latitude, post.longitude]);
        }
        
        // Group by country
        if (country && country !== 'Unknown') {
            if (!countries[country]) countries[country] = [];
            countries[country].push([post.latitude, post.longitude]);
        }
        
        // Group by city
        if (city && city !== 'Unknown') {
            if (!cities[city]) cities[city] = [];
            cities[city].push([post.latitude, post.longitude]);
        }
    });
    
    // Prefetch tiles for each region at appropriate zoom levels
    const prefetchPromises = [];
    
    // Continental views (zoom 2-6)
    Object.entries(regions).forEach(([continent, coords]) => {
        if (coords.length > 0) {
            const bounds = L.latLngBounds(coords);
            prefetchPromises.push(prefetchBoundsAtZoom(bounds.pad(0.15), 4));
            prefetchPromises.push(prefetchBoundsAtZoom(bounds.pad(0.15), 6));
        }
    });
    
    // Country views (zoom 6-10)
    Object.entries(countries).forEach(([country, coords]) => {
        if (coords.length > 0) {
            const bounds = L.latLngBounds(coords);
            prefetchPromises.push(prefetchBoundsAtZoom(bounds.pad(0.2), 8));
            prefetchPromises.push(prefetchBoundsAtZoom(bounds.pad(0.2), 10));
        }
    });
    
    // City views (zoom 10-15) - only for cities with multiple cafes
    Object.entries(cities).forEach(([city, coords]) => {
        if (coords.length > 1) { // Only prefetch for cities with multiple cafes
            const bounds = L.latLngBounds(coords);
            prefetchPromises.push(prefetchBoundsAtZoom(bounds.pad(0.3), 12));
            prefetchPromises.push(prefetchBoundsAtZoom(bounds.pad(0.3), 14));
        }
    });
    
    console.log('Started', prefetchPromises.length, 'tile prefetch operations');
}

function prefetchBoundsAtZoom(bounds, zoom) {
    return new Promise((resolve) => {
        if (!window.mainTileLayer) {
            resolve();
            return;
        }
        
        // Calculate tile bounds for this zoom level
        const tileBounds = getTileBounds(bounds, zoom);
        const tiles = [];
        
        for (let x = tileBounds.min.x; x <= tileBounds.max.x; x++) {
            for (let y = tileBounds.min.y; y <= tileBounds.max.y; y++) {
                tiles.push({x, y, z: zoom});
            }
        }
        
        // Limit tiles per batch to avoid overwhelming the server
        const maxTiles = 20;
        const tilesToFetch = tiles.slice(0, maxTiles);
        
        console.log(`Prefetching ${tilesToFetch.length} tiles at zoom ${zoom}`);
        
        // Prefetch tiles with a small delay between each
        let index = 0;
        const prefetchNext = () => {
            if (index >= tilesToFetch.length) {
                resolve();
                return;
            }
            
            const tile = tilesToFetch[index];
            prefetchTile(tile.x, tile.y, tile.z);
            index++;
            
            // Small delay to not overwhelm the server
            setTimeout(prefetchNext, 50);
        };
        
        prefetchNext();
    });
}

function getTileBounds(bounds, zoom) {
    const tileSize = 256;
    const worldSize = tileSize * Math.pow(2, zoom);
    
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    
    const swPoint = {
        x: Math.floor((sw.lng + 180) / 360 * Math.pow(2, zoom)),
        y: Math.floor((1 - Math.log(Math.tan(sw.lat * Math.PI / 180) + 1 / Math.cos(sw.lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom))
    };
    
    const nePoint = {
        x: Math.floor((ne.lng + 180) / 360 * Math.pow(2, zoom)),
        y: Math.floor((1 - Math.log(Math.tan(ne.lat * Math.PI / 180) + 1 / Math.cos(ne.lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom))
    };
    
    return {
        min: { x: Math.min(swPoint.x, nePoint.x), y: Math.min(swPoint.y, nePoint.y) },
        max: { x: Math.max(swPoint.x, nePoint.x), y: Math.max(swPoint.y, nePoint.y) }
    };
}

function prefetchTile(x, y, z) {
    const subdomains = ['a', 'b', 'c', 'd'];
    const subdomain = subdomains[(x + y) % subdomains.length];
    const url = `https://${subdomain}.basemaps.cartocdn.com/dark_all/${z}/${x}/${y}.png`;
    
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
        // Tile loaded successfully, browser will cache it
    };
    img.onerror = () => {
        // Silently fail for tiles that don't exist
    };
    img.src = url;
}