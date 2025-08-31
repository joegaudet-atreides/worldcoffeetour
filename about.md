---
layout: default
title: About
permalink: /about/
---

<div class="about-page">
    <h1>About World Coffee Tour</h1>
    
    <div class="about-content">
        <p class="lead">
            One cup at a time, exploring the world's coffee culture through local cafés, 
            roasters, and the stories behind every brew.
        </p>
        
        <p>
            This journey started with a simple love for coffee and curiosity about how different 
            cultures approach this universal ritual. From the precise pour-overs of Tokyo to the 
            leisurely espressos of Rome, each cup tells a story about its place and people.
        </p>
        
        <h2>The Mission</h2>
        <p>
            To discover and document exceptional coffee experiences around the world, celebrating 
            the craft of local roasters and baristas who turn coffee into an art form.
        </p>
        
        <h2>Follow Along</h2>
        <p>
            Join the journey on Instagram 
            <a href="https://instagram.com/{{ site.instagram_username }}" target="_blank" rel="noopener">@{{ site.instagram_username }}</a> 
            with <a href="https://www.instagram.com/explore/tags/worldcoffeetour/" target="_blank" rel="noopener">#worldcoffeetour</a>
        </p>
        
        <div class="coffee-stats">
            <div class="stat">
                <span class="stat-number">{{ site.coffee_posts.size }}</span>
                <span class="stat-label">Coffee Stops</span>
            </div>
            <div class="stat">
                <span class="stat-number">{{ site.coffee_posts | map: 'country' | uniq | size }}</span>
                <span class="stat-label">Countries</span>
            </div>
            <div class="stat">
                <span class="stat-number">{{ site.coffee_posts | map: 'city' | uniq | size }}</span>
                <span class="stat-label">Cities</span>
            </div>
        </div>
    </div>
</div>

<style>
.about-page {
    max-width: 700px;
    margin: 0 auto;
    padding: 2rem 0;
}

.about-page h1 {
    font-size: 2.5rem;
    font-weight: 300;
    margin-bottom: 2rem;
    text-align: center;
}

.about-content {
    line-height: 1.8;
    color: var(--primary-color);
}

.lead {
    font-size: 1.25rem;
    font-weight: 300;
    margin-bottom: 2rem;
    color: var(--text-light);
    text-align: center;
}

.about-content h2 {
    font-size: 1.5rem;
    font-weight: 400;
    margin: 2rem 0 1rem;
    color: var(--accent-color);
}

.about-content a {
    color: var(--accent-color);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.3s ease;
}

.about-content a:hover {
    border-bottom-color: var(--accent-color);
}

.coffee-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    margin-top: 3rem;
    padding: 2rem;
    background: var(--card-bg);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.stat {
    text-align: center;
}

.stat-number {
    display: block;
    font-size: 2.5rem;
    font-weight: 300;
    color: var(--accent-color);
    margin-bottom: 0.5rem;
}

.stat-label {
    display: block;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-light);
}

@media (max-width: 768px) {
    .about-page h1 {
        font-size: 2rem;
    }
    
    .lead {
        font-size: 1.1rem;
    }
    
    .coffee-stats {
        grid-template-columns: 1fr;
        gap: 1.5rem;
    }
}
</style>