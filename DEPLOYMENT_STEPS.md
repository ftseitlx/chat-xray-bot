# Deployment Steps for Chat X-Ray Bot

## What We've Fixed

1. **Ollama Integration**
   - Updated model configuration from `llama2:7b-chat` to `llama3.2`
   - Enhanced API endpoint handling with multiple fallback URLs
   - Added robust JSON parsing for streaming responses
   - Improved error handling and added OpenAI fallback

2. **WeasyPrint PDF Generation**
   - Added compatibility for all WeasyPrint API versions
   - Improved error reporting for PDF generation

3. **Testing Tools**
   - Created scripts to verify Ollama connectivity
   - Added tools to test API functionality

## Deployment Steps

### 1. Local Testing (Already Completed)

- Verified Ollama is running locally at http://localhost:11434
- Confirmed the API works with the llama3.2 model
- Tested JSON parsing with streaming responses

### 2. GitHub Deployment

To deploy to Render via GitHub:

1. Authenticate with GitHub CLI with proper scopes:
   ```
   gh auth login
   ```
   - Select GitHub.com
   - Select HTTPS
   - Choose Yes to authenticate Git
   - Choose "Login with a web browser" or token with scopes: repo, read:org, workflow

2. Deploy using our script:
   ```
   ./deploy-with-gh.sh
   ```
   This will:
   - Commit all changes
   - Push to your repository
   - Trigger the GitHub Actions workflow
   - Deploy both the main app and Ollama service to Render

3. Monitor deployment:
   ```
   gh run list
   ```

### 3. Verify Deployment

After deployment completes (5-10 minutes):

1. Test the Ollama service:
   ```
   python test_ollama_api.py --url https://llama2-ollama.onrender.com
   ```

2. Test the main application:
   Visit your app URL or use the Telegram bot

### 4. Troubleshooting

If issues persist:

1. Check Render logs:
   ```
   python get_render_app_logs.py
   ```

2. Verify Ollama connectivity:
   ```
   python check_ollama_connection.py --url https://llama2-ollama.onrender.com
   ```

3. Restart services if needed:
   ```
   python fix_and_redeploy.py --restart
   ``` 