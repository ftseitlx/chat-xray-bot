# Deployment Instructions for Timeout Fix

This document provides detailed step-by-step instructions for deploying the fix for the "Timeout context manager should be used inside a task" error.

## Quick Setup Guide

For a one-command deployment using our script:

```bash
python fix_and_redeploy.py --webhook --render-deploy
```

## Step-by-Step Manual Deployment

If you prefer to deploy manually or if the script doesn't work for some reason, follow these steps:

### 1. Merge the Fix Branch

First, merge the `fix-timeout-context-manager` branch into your main branch:

1. Go to: https://github.com/ftseitlx/chat-xray-bot/pull/new/fix-timeout-context-manager
2. Create and complete the pull request
3. Click "Merge pull request"

### 2. Update Your Local Repository

```bash
git checkout main
git pull origin main
```

### 3. Test the Fixed Code Locally (Optional)

```bash
python -m app.bot
```

Look for the distinctive log message: "TIMEOUT FIX VERSION 2025-05-14 ACTIVATED"

### 4. Deploy to Render.com

#### A. Using the Render Dashboard

1. Log in to your Render.com account
2. Navigate to your Chat X-Ray Bot service
3. Click on "Manual Deploy" > "Deploy latest commit"
4. Wait for deployment to complete (check the deployment logs)

#### B. Using API (Alternative)

```bash
curl -X POST \
  https://api.render.com/v1/services/srv-d0i3t06mcj7s739m48r0/deploys \
  -H 'Authorization: Bearer YOUR_RENDER_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"clearCache": true}'
```

### 5. Verify Bot Webhook Configuration

```bash
python reset_webhook.py
```

Or manually:

```bash
BOT_TOKEN="your_bot_token"
WEBHOOK_URL="your_webhook_url"

# Delete existing webhook
curl -X POST https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook?drop_pending_updates=true

# Set new webhook
curl -X POST https://api.telegram.org/bot$BOT_TOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$WEBHOOK_URL\", \"drop_pending_updates\": true}"

# Verify webhook status
curl -X GET https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo
```

## Verifying the Deployment

To verify that the fix has been properly deployed:

1. Check the Render.com logs for the distinctive message: "TIMEOUT FIX VERSION 2025-05-14 ACTIVATED"
2. Send a document to the bot and check if it processes it without the timeout error
3. Look for detailed "[TIMEOUT-FIX]" log messages in the Render.com logs

## Troubleshooting

If you still encounter the timeout error:

1. **Webhook Issue**: Make sure the webhook is properly set by using the "getWebhookInfo" endpoint
2. **Cache Issue**: Try deploying with cache cleared using the Render dashboard
3. **Process Restart**: Ensure the process has been restarted with the new code
4. **Check Logs**: Look for the "[TIMEOUT-FIX]" log markers to ensure the new code is running

## Rollback Plan

If you need to rollback to the previous version:

1. Use the Render dashboard to deploy a specific previous commit
2. Or restore from a backup if available

## Contact Support

If you continue to experience issues, please open an issue on GitHub or contact the development team. 