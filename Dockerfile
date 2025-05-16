FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    wkhtmltopdf \
    curl \
    software-properties-common \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies with better error handling
RUN poetry install --no-interaction --no-ansi --no-dev || \
    (echo "Poetry install failed, falling back to pip..." && \
    pip install --no-cache-dir -r requirements.txt)

# Copy application code
COPY . .

# Create directories for uploads and reports and ensure proper permissions
RUN mkdir -p uploads reports && chmod 777 uploads reports

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a startup script with better error handling
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting Chat X-Ray Bot..."\n\
echo "Python version: $(python --version)"\n\
echo "Checking directories:"\n\
ls -la /app\n\
echo "Uploads directory:"\n\
ls -la /app/uploads\n\
echo "Reports directory:"\n\
ls -la /app/reports\n\
echo "Checking key environment variables:"\n\
echo "BOT_TOKEN set: $(if [ -n "$BOT_TOKEN" ]; then echo YES; else echo NO; fi)"\n\
echo "OPENAI_API_KEY set: $(if [ -n "$OPENAI_API_KEY" ]; then echo YES; else echo NO; fi)"\n\
echo "WEBHOOK_HOST set: $(if [ -n "$WEBHOOK_HOST" ]; then echo YES; else echo NO; fi)"\n\
echo "PORT set: $(if [ -n "$PORT" ]; then echo YES - $PORT; else echo NO; fi)"\n\
echo "OLLAMA_URL set: $(if [ -n "$OLLAMA_URL" ]; then echo YES - $OLLAMA_URL; else echo NO; fi)"\n\
echo "OLLAMA_MODEL set: $(if [ -n "$OLLAMA_MODEL" ]; then echo YES - $OLLAMA_MODEL; else echo NO; fi)"\n\
echo "Starting bot in webhook mode, binding to port ${PORT:-8000}..."\n\
# Make sure we use the right port\n\
export PORT=${PORT:-8000}\n\
# Starting the application\n\
exec python -m app.bot\n' > /app/start.sh && chmod +x /app/start.sh

# Expose the port that the application uses
EXPOSE 8000

# Start the bot using the startup script
CMD ["/app/start.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1 