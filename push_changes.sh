#!/bin/bash

# Check if we're in a git repository
if [ ! -d ".git" ]; then
  echo "Error: This doesn't appear to be a git repository."
  echo "Please run this script from the root of your git repository."
  exit 1
fi

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
  echo "No changes to commit."
  exit 0
fi

echo "Changes found in the repository. Committing and pushing..."

# Commit the changes with a descriptive message
git add requirements.txt
git commit -m "Downgrade aiogram to 3.2.0 to fix timeout context manager issue"

# Push the changes
echo "Pushing changes to remote repository..."
git push

if [ $? -eq 0 ]; then
  echo "✅ Changes pushed successfully!"
  echo "This should trigger an automatic deployment on Render."
  echo "You can monitor the deployment using:"
  echo "./fetch_render_logs.py --service-name chat-xray-bot --follow"
else
  echo "❌ Failed to push changes."
  exit 1
fi 