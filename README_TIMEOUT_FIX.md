# Telegram Bot Timeout Context Manager Fix

This guide provides instructions on how to fix the "Timeout context manager should be used inside a task" error in your Telegram bot using aiogram 3.x.

## The Issue

The error occurs when trying to use timeout context managers outside of asyncio tasks. In the error logs, you can see:

```
Error processing file: Timeout context manager should be used inside a task
RuntimeError: Timeout context manager should be used inside a task
```

This happens because aiogram 3.x and aiohttp use timeouts in their internal methods, and these timeouts need to be used within proper async task contexts.

## The Fix

We've fixed the issue by:

1. Updating the `safe_send_message` and `safe_edit_message` helper functions to properly use tasks
2. Fixing the webhook handler to process updates in separate tasks
3. Ensuring all async operations in the bot use proper task contexts
4. Adding more robust error handling throughout the code

The most critical changes were to:
- Use `asyncio.create_task()` properly for all async operations
- Wrap async operations in dedicated task functions 
- Respond immediately to webhook requests before processing updates

## How to Apply the Fix

### Option 1: Manual Installation

1. Back up your existing `bot.py` file
2. Replace your current `bot.py` with the fixed version
3. Restart your bot service

### Option 2: Using the Automated Script

We've provided a script to simplify the deployment process:

```bash
# Create a backup and fix webhook configuration
python fix_and_redeploy.py --webhook

# Create a backup, trigger a Render deployment, and fix webhook configuration
python fix_and_redeploy.py --webhook --render-deploy

# Restart the local bot service
python fix_and_redeploy.py --restart
```

## Script Options

```
--no-backup       Skip creating a backup before redeploying
--restart         Restart the bot service after redeploying
--webhook         Fix webhook configuration
--render-deploy   Trigger a Render.com redeploy
```

## Verifying the Fix

After applying the fix, check the logs to ensure no more timeout context errors appear. You should see successful webhook handling in the logs.

Test the bot by:
1. Sending a text message
2. Uploading a document
3. Checking that you receive prompt responses

## Technical Details

The main changes involve:

1. **Safe Message Functions**: Updated to use proper task context
```python
async def safe_send_message(message: Message, text: str, **kwargs):
    """Send a message safely in a task to avoid timeout context errors"""
    try:
        # Define a function to be executed in a proper task context
        async def _send():
            try:
                return await message.answer(text, **kwargs)
            except Exception as inner_e:
                logger.error(f"Error in _send task: {inner_e}")
                return None
        
        # Execute the sending in a proper task context
        return await asyncio.create_task(_send())
    except Exception as e:
        logger.error(f"Error creating send message task: {e}")
        # Try one more time with a delay if needed
```

2. **Webhook Handler**: Now returns immediately while processing updates in background tasks
```python
async def handle_webhook(request):
    # Start a background task without waiting for completion
    asyncio.create_task(_process_webhook())
    
    # Return success immediately to prevent Telegram timeouts
    return web.Response(status=200, text='{"ok": true}')
```

3. **Document Handling**: All document processing is now done in proper task contexts

## Additional Resources

- [aiogram Documentation](https://docs.aiogram.dev/)
- [asyncio Tasks Documentation](https://docs.python.org/3/library/asyncio-task.html)
- [aiohttp Client Documentation](https://docs.aiohttp.org/en/stable/client.html)

For questions or issues, please contact the development team. 