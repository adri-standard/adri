# GitHub Pages Configuration

This document explains how the GitHub Pages setup works in this repository and how to update it when needed.

## Current Setup

The site is currently configured to use an auto-generated GitHub Pages URL. For public repositories, GitHub supports organization-pattern URLs (`username.github.io/repository-name`).

## Configuration Files

The site URL is centralized in the following files:

1. **`site_config.yml`**: Central configuration file that defines the base URL
2. **`.github/workflows/docs.yml`**: GitHub Action that reads the config file and builds the site
3. **`mkdocs.yml`**: Uses environment variables to get the site URL during build
4. **Various HTML files**: Share buttons and links use the configured URL

## When Making the Repository Public

When the repository is made public, follow these steps to update the URL:

1. Edit `site_config.yml`:
   ```yaml
   # Comment out or remove the auto-generated URL
   # site_base_url: "https://probable-adventure-3jve6ry.pages.github.io/"
   
   # Uncomment the organization URL
   site_base_url: "https://adri-standard.github.io/agent-data-readiness-index/"
   ```

2. Commit and push these changes to the main branch

3. Go to the GitHub repository → Actions tab

4. Manually trigger the "Deploy ADRI Documentation" workflow by clicking the workflow and selecting "Run workflow"

5. After the workflow completes, the site will be available at the organization URL pattern:
   `https://adri-standard.github.io/agent-data-readiness-index/`

## GitHub Pages Settings

The GitHub Pages settings should be configured to:

1. Deploy from the `gh-pages` branch
2. Build from the `/` (root) folder

These settings don't need to be changed when making the repository public.
