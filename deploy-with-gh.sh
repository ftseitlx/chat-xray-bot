#!/bin/bash
set -e

echo "Deploying Chat X-Ray Bot and Ollama using GitHub..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI not found. Please install it with: brew install gh (or equivalent)"
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &>/dev/null; then
    echo "Please login to GitHub first:"
    gh auth login
fi

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $BRANCH"

# Push changes
echo "Pushing changes to GitHub..."
git add .
git commit -m "Update Ollama integration and WeasyPrint compatibility" || echo "No changes to commit"
git push origin $BRANCH

# Trigger workflow
echo "Triggering deployment workflow..."
gh workflow run deploy.yml

echo "Deployment initiated! Check status with: gh run list"
echo "You can also monitor deployment at: https://render.com/dashboard" 