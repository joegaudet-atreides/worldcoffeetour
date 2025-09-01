---
layout: default
title: About
permalink: /about/
---

<div class="about-page">
    <div class="about-content">
        <p class="lead">
            One cup at a time, exploring the world's coffee culture through local cafés and roasters.
        </p>
        <p>
            Years ago, my friend <a href="https://www.instagram.com/jamesgolick" target="_blank" rel="noopener">James Golick</a> 
            passed away tragically. Among the many things that James was, he was a lover of coffee. 
            What started as a way to honor a friend, became a way to explore the world, one cup of coffee at a time. As the song says, these are a few of my favorite things.
        </p>
        <p>&nbsp;</p> 
        <p>
            Over the years folks have asked me for my coffee recommendations, and this felt like an 
            easier way to give them than by pointing them at my Instagram. 
        </p>

        {% comment %} Filter posts with valid location data {% endcomment %}
        {% assign valid_posts = site.coffee_posts %}
        {% assign filtered_posts = "" | split: "" %}
        {% for post in valid_posts %}
          {% if post.latitude and post.longitude and post.city != "Unknown" and post.country != "Unknown" and post.continent != "World" %}
            {% assign filtered_posts = filtered_posts | push: post %}
          {% endif %}
        {% endfor %}
        {% assign valid_posts = filtered_posts %}
        <div class="coffee-stats">
            <div class="stat">
                <span class="stat-number">{{ valid_posts.size }}</span>
                <span class="stat-label">Coffee Stops</span>
            </div>
            <div class="stat">
                <span class="stat-number">{{ valid_posts | map: 'country' | uniq | size }}</span>
                <span class="stat-label">Countries</span>
            </div>
            <div class="stat">
                <span class="stat-number">{{ valid_posts | map: 'city' | uniq | size }}</span>
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
    .about-page {
        padding: 2rem 1.5rem;
    }
    
    .about-page h1 {
        font-size: 2rem;
    }
    
    .lead {
        font-size: 1.1rem;
    }
    
    .coffee-stats {
        grid-template-columns: 1fr;
        gap: 1.5rem;
        margin-left: -0.5rem;
        margin-right: -0.5rem;
    }
}
</style>