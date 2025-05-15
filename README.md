# Chat X-Ray Bot

A Telegram bot that analyzes chat history to provide psychological insights about relationships.

## Features

- Upload chat export files (.txt or .html) for analysis
- Get AI-powered psychological insights about communication patterns
- Receive a detailed PDF report with visualizations
- Analysis based on psychological theories including Gabor Maté's attachment theory, John Gottman's four horsemen, and more

## Technical Stack

- Python 3.12+
- aiogram 3.x for Telegram bot API
- OpenAI API (GPT-3.5 Turbo & GPT-4 Turbo) for chat analysis
- aiohttp for asynchronous web server
- Beautiful Soup for HTML parsing
- Deployed on Render.com

## Installation

1. Clone this repository
```bash
git clone https://github.com/yourusername/chat-xray-bot.git
cd chat-xray-bot
```

2. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration
```
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
WEBHOOK_HOST=your_webhook_host  # Optional for production
SENTRY_DSN=your_sentry_dsn  # Optional for error tracking
```

4. Run the bot locally
```bash
python -m app.bot
```

## Deployment

The bot can be deployed to Render.com or another hosting service that supports Python applications.

### Using the Fix and Redeploy Script

For webhook-based deployments, use the provided script:

```bash
# Create a backup and fix webhook configuration
python fix_and_redeploy.py --webhook

# Create a backup, trigger a Render deployment, and fix webhook configuration
python fix_and_redeploy.py --webhook --render-deploy

# Restart the local bot service
python fix_and_redeploy.py --restart
```

## Timeout Context Manager Fix

This repository includes a fix for the "Timeout context manager should be used inside a task" error that can occur with aiogram 3.x and aiohttp. The error happens when timeout context managers are used outside of proper asyncio tasks.

### Key Improvements:

1. **Enhanced Helper Functions**:
   - `safe_send_message` and `safe_edit_message` now properly handle async task contexts
   - Added nested task functions with comprehensive error handling
   - Implemented retry mechanisms for failed operations

2. **Webhook Handler Optimization**:
   - Completely rewritten to respond immediately to Telegram while processing updates in the background
   - Implemented a two-level task structure for request handling
   - Added proper error recovery to prevent cascading failures

3. **Task Management**: 
   - Fixed task cleanup during shutdown
   - Proper task context for all async operations
   - Improved exception handling throughout the codebase

For more details, see [README_TIMEOUT_FIX.md](README_TIMEOUT_FIX.md).

## Folder Structure

- `app/`: Main application code
  - `bot.py`: Main bot implementation
  - `config.py`: Configuration settings
  - `services/`: Service modules for chat processing
  - `utils/`: Utility functions
- `docs/`: Documentation files
- `uploads/`: Temporary storage for uploaded chat files
- `reports/`: Generated PDF reports

## Privacy and Data Handling

- All chat data is anonymized during processing
- Uploaded files are automatically deleted after 1 hour
- Reports are accessible for 72 hours before deletion

## License

MIT License

## Credits

Developed by Felix
