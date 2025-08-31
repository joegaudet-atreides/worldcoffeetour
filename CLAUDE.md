# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Jekyll-based static site project configured for GitHub Pages deployment. The project appears to be for a world coffee tour website.

## Development Setup

### Jekyll/GitHub Pages Setup

Since this is a Jekyll site for GitHub Pages:

1. Install Jekyll and dependencies:
   ```bash
   gem install bundler jekyll
   bundle install
   ```

2. Serve the site locally:
   ```bash
   bundle exec jekyll serve
   ```

3. Build the site:
   ```bash
   bundle exec jekyll build
   ```

## Project Structure

- The project uses Jekyll's default structure
- `_site/` directory contains the generated static site (gitignored)
- GitHub Pages will handle the Jekyll build process when deployed

## Important Notes

- `Gemfile.lock` is intentionally gitignored as GitHub Pages uses its own version of the pages-gem
- The site will be served from the repository root when deployed to GitHub Pages
- Jekyll cache directories (`.sass-cache/`, `.jekyll-cache/`, `.jekyll-metadata`) are gitignored