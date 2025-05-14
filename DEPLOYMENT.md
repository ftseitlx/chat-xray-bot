# Deployment Guide for Chat X-Ray Bot

This guide will walk you through deploying your Chat X-Ray bot to Render.com for free continuous hosting.

## Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign up for a free account if you don't have one
2. Click the "+" icon in the top right corner and select "New repository"
3. Name your repository "chat-xray-bot"
4. Set it to Private
5. Click "Create repository"
6. Follow the instructions on the next page to push your existing code:

```bash
# Initialize Git repository (if not already done)
git init

# Add all files to Git
git add .

# Commit the files
git commit -m "Initial commit"

# Add the GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/chat-xray-bot.git

# Push the code to GitHub
git push -u origin main
```

## Step 2: Sign Up for Render.com

1. Go to [Render.com](https://render.com) and sign up for a free account
2. You can sign up directly with your GitHub account for easier integration

## Step 3: Deploy to Render.com

1. In your Render dashboard, click "New +" and select "Web Service"
2. Connect your GitHub account if you haven't already
3. Select the "chat-xray-bot" repository
4. Configure your web service:
   - Name: chat-xray-bot
   - Environment: Docker
   - Branch: main
   - Plan: Free
5. Add the following environment variables:
   - BOT_TOKEN: Your Telegram bot token from BotFather
   - OPENAI_API_KEY: Your OpenAI API key
6. Click "Create Web Service"

## Step 4: Update Telegram Bot to Use Webhook

Once your service is deployed, Render will provide you with a URL (something like `https://chat-xray-bot.onrender.com`).

The bot will automatically use webhook mode when deployed, as configured in the code.

## Step 5: Monitor Your Deployment

1. In the Render dashboard, you can view logs for your service
2. You can also set up alerts for when your service goes down

## Important Notes

1. **Free Tier Limitations**: Render's free tier will spin down your service after 15 minutes of inactivity. It will automatically spin back up when a new request comes in, but there might be a slight delay for the first request after inactivity.

2. **Storage**: The free tier doesn't have persistent storage, so any uploaded files and generated reports will be lost if the service restarts. This is usually not a problem since your bot already has automatic cleanup of files.

3. **Usage Limits**: The free tier includes 750 hours of runtime per month, which is enough for continuous operation.

## Troubleshooting

If your bot doesn't respond after deployment:

1. Check the logs in the Render dashboard for any errors
2. Make sure your BOT_TOKEN and OPENAI_API_KEY are correctly set
3. Verify that the webhook URL is correctly configured
4. Try restarting the service from the Render dashboard 