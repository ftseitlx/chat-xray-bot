# Chat X-Ray Bot

A Telegram bot that analyzes chat files and generates psychological reports using OpenAI's GPT models.

## Features

- Analyzes chat files uploaded via Telegram
- Supports both plaintext (.txt) and WhatsApp HTML exports (.html)
- Generates detailed psychological reports based on chat content
- Uses theories from Gabor Maté, John Gottman, Marshall Rosenberg, and Eric Berne
- Provides visualizations of communication patterns and emotional dynamics
- Parallelized processing for faster analysis
- Delivers insights directly in Telegram with HTML formatting
- Automatically cleans up old files to maintain privacy

## Supported Chat Formats

- WhatsApp text exports (format: `[DD.MM.YYYY, HH:MM] Author: Message`)
- WhatsApp HTML exports (exported from WhatsApp web/desktop)
- Standard text chat logs with author and message content
- Most common chat export formats with timestamps

## Deployment Options

### Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: 
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -e .`
5. Copy `.env.example` to `.env` and fill in your API keys
6. Run the bot: `python -m app.bot`

### Docker Deployment

```bash
docker build -t chat-xray-bot .
docker run -p 8080:8080 --env-file .env chat-xray-bot
```

### Render.com Deployment (Free)

1. Fork this repository to your GitHub account
2. Create a new Web Service on Render.com
3. Connect your GitHub repository
4. Select "Docker" as the environment
5. Add the required environment variables (BOT_TOKEN, OPENAI_API_KEY)
6. Deploy!

## Environment Variables

- `BOT_TOKEN`: Your Telegram bot token from BotFather
- `OPENAI_API_KEY`: Your OpenAI API key
- `WEBHOOK_HOST`: URL of your deployed application (for production)
- `WEBHOOK_PATH`: Path for the webhook endpoint (default: /webhook)
- `PORT`: Port to run the server on (default: 8080)
- `HOST`: Host to bind the server to (default: 0.0.0.0)
- `UPLOAD_RETENTION_HOURS`: Hours to keep uploaded files (default: 1)
- `REPORT_RETENTION_HOURS`: Hours to keep generated reports (default: 72)
- `ENABLE_COST_TRACKING`: Enable cost tracking in logs (default: true)
- `OPENAI_CONCURRENCY_LIMIT`: Maximum number of parallel OpenAI requests (default: 3)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Privacy Policy

See the [Privacy Policy](docs/privacy_policy.md) for information on how user data is handled. 