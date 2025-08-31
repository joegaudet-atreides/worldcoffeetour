// Map initialization for index page
if (document.getElementById('map')) {
    const map = L.map('map').setView([30, 0], 2);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

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