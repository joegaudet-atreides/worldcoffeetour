---
layout: default
title: About
permalink: /about/
---

<div class="about-page">
    <div class="about-content">
        <div class="about-header">
            <img src="{{ '/assets/images/joe-profile.jpg' | relative_url }}" alt="Joe Gaudet" class="profile-pic">
            <div class="about-intro">
                <h2>About the Tour Captain</h2>
                <p class="lead">
                    Exploring the world's coffee culture through local cafés and roasters.
                </p>
            </div>
        </div>
        
        <p>
            Hello, welcome to my dumb corner of the internet. I like many engineers, fell in love with coffee in school, late nights in the lab powered by rocket fuel. However initially I packed it with cream and sugar. My frequent consumption of this high calorie slurry caused me to balloon up in 3rd year to 230lbs (from 190). This led me to the conclusion that I needed to learn to drink coffee black.
        </p>
        <p>
            Fast forward 19 years, and my two favourite coffee drinks are a perfectly made pour over, and a creamy espresso.
        </p>
        <p>
            Please enjoy my ramblings here, and ping me for any recommendations that haven't made it to the page.
        </p>
        <p>&nbsp;</p> 
        <p>
            Years ago, my friend <a href="https://www.instagram.com/jamesgolick" target="_blank" rel="noopener">James Golick</a> 
            passed away tragically. Among the many things that James was, he was a lover of coffee. 
            What started as a way to honor a friend, became a way to explore the world, one cup of coffee at a time. 
        </p>
        <p>&nbsp;</p> 
        <p>
            Over the years folks have asked me for my coffee recommendations, and this felt like an 
            easier way to give them than by pointing them at my Instagram. 
        </p>
        <p>&nbsp;</p> 
        <p>
            As the song says, these are a few of my favorite things.
        </p>
        
        <div class="social-links">
            <h3>Connect with me</h3>
            <div class="social-buttons">
                <a href="https://joegaudet.com" target="_blank" rel="noopener" class="social-link">
                    <span>🌐</span> Main Site
                </a>
                <a href="https://github.com/joegaudet" target="_blank" rel="noopener" class="social-link">
                    <span>💻</span> GitHub
                </a>
                <a href="https://linkedin.com/in/josephgaudet" target="_blank" rel="noopener" class="social-link">
                    <span>💼</span> LinkedIn
                </a>
                <a href="https://x.com/joegaudet" target="_blank" rel="noopener" class="social-link">
                    <span>🐦</span> X (Twitter)
                </a>
                <a href="https://bsky.app/profile/joegaudet.bsky.social" target="_blank" rel="noopener" class="social-link">
                    <span>🦋</span> Bluesky
                </a>
                <a href="https://instagram.com/joegaudet" target="_blank" rel="noopener" class="social-link">
                    <span>📸</span> Instagram
                </a>
            </div>
        </div>

        {% comment %} Show all posts - even those with incomplete location data {% endcomment %}
        {% assign valid_posts = site.coffee_posts %}
        <div class="coffee-stats">
            <div class="stat">
                <span class="stat-number">{{ valid_posts.size }}</span>
                <span class="stat-label">Coffee Stops</span>
            </div>
            <div class="stat">
                {% assign known_countries = valid_posts | map: 'country' | uniq | where_exp: 'country', 'country != "Unknown"' %}
                <span class="stat-number">{{ known_countries | size }}</span>
                <span class="stat-label">Countries</span>
            </div>
            <div class="stat">
                {% assign known_cities = valid_posts | map: 'city' | uniq | where_exp: 'city', 'city != "Unknown"' %}
                <span class="stat-number">{{ known_cities | size }}</span>
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

.about-header {
    display: flex;
    align-items: center;
    gap: 2rem;
    margin-bottom: 2rem;
}

.profile-pic {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    flex-shrink: 0;
}

.about-intro h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.8rem;
    font-weight: 400;
    color: var(--accent-color);
}

.about-intro .lead {
    margin: 0;
    text-align: left;
}

.social-links {
    margin-top: 3rem;
    padding: 2rem;
    background: var(--card-bg);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.social-links h3 {
    margin: 0 0 1.5rem 0;
    font-size: 1.3rem;
    font-weight: 400;
    color: var(--accent-color);
    text-align: center;
}

.social-buttons {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
}

.social-link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--bg-color);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    text-decoration: none;
    color: var(--primary-color);
    transition: all 0.2s ease;
    font-size: 0.9rem;
}

.social-link:hover {
    background: var(--accent-color);
    color: var(--bg-color);
    border-color: var(--accent-color);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(212, 165, 116, 0.3);
}

.social-link span {
    font-size: 1.1rem;
}

@media (max-width: 768px) {
    .about-page {
        padding: 2rem 1.5rem;
    }
    
    .about-page h1 {
        font-size: 2rem;
    }
    
    .about-header {
        flex-direction: column;
        text-align: center;
        gap: 1.5rem;
    }
    
    .about-intro .lead {
        text-align: center;
    }
    
    .profile-pic {
        width: 100px;
        height: 100px;
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
    
    .social-buttons {
        grid-template-columns: 1fr;
    }
}
</style>