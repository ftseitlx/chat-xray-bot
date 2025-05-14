#!/bin/bash

# Read the GitHub token from file
GITHUB_TOKEN=$(cat gh_token.txt)

# Set GitHub token as environment variable
export GH_TOKEN="$GITHUB_TOKEN"

echo "Creating pull request using GitHub CLI..."

# Create the pull request
gh pr create \
  --base main \
  --head fix-webhook-handler \
  --title "Fix Timeout Context Error in Webhook Handler" \
  --body "## Problem
The bot was experiencing a \`RuntimeError: Timeout context manager should be used inside a task\` error when processing webhook updates. This was preventing the bot from responding to messages and file uploads.

## Solution
- Replaced the default \`SimpleRequestHandler\` with a custom webhook handler function
- Implemented asynchronous update processing by creating a separate task for each update
- Separated the response cycle from the update processing to prevent timeout errors

## Testing
After merging this PR, the bot should properly handle all incoming webhook updates without timeout context errors, allowing it to respond to both text messages and file uploads."

# Check if PR was created successfully
if [ $? -eq 0 ]; then
    echo "✅ Pull request created successfully!"
    echo "You can now merge it on GitHub or use this command:"
    echo "gh pr merge --auto --merge"
else
    echo "❌ Failed to create pull request using GitHub CLI."
    echo "Please create a pull request manually at: https://github.com/ftseitlx/chat-xray-bot/pull/new/fix-webhook-handler"
fi

# Remove the token file for security
rm gh_token.txt 