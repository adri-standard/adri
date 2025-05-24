# Instructions to Remove GitHub Wiki

The Wiki needs to be disabled through the GitHub web interface. Here's how:

## Steps to Remove the Wiki:

1. **Go to your repository on GitHub**:
   https://github.com/ThinkEvolveSolve/agent-data-readiness-index

2. **Navigate to Settings**:
   - Click on "Settings" tab in the repository

3. **Find the Features section**:
   - Scroll down to the "Features" section

4. **Disable the Wiki**:
   - Uncheck the box next to "Wikis"
   - This will disable the Wiki feature for the repository

5. **Save changes** (if required)

## Verification:

After disabling:
- The "Wiki" tab should disappear from the repository navigation
- Any existing wiki content will be archived but not publicly accessible
- All documentation will be served from GitHub Pages instead

## GitHub Pages Documentation:

Your documentation is available at:
**https://probable-adventure-3jve6ry.pages.github.io/**

(This is a special URL because the repository is private. When/if the repository becomes public, the URL will change to: https://thinkevolvesolve.github.io/agent-data-readiness-index/)

The GitHub Actions workflow "Deploy ADRI Documentation" will automatically build and deploy documentation from the `docs/` folder whenever you push to the main branch.

## Current Status:

- ✅ Documentation build has been triggered by the recent commit
- ✅ The gh-pages branch exists and is configured
- ⚠️ The site is only accessible to authenticated GitHub users (because the repo is private)

## To Check Deployment Status:

1. Go to the repository's Actions tab:
   https://github.com/ThinkEvolveSolve/agent-data-readiness-index/actions

2. Look for the "Deploy ADRI Documentation" workflow run

3. Once complete, visit the documentation at:
   https://probable-adventure-3jve6ry.pages.github.io/
