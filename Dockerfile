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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry==1.7.1

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-dev

# Copy requirements file and install as fallback
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create directories for uploads and reports and ensure proper permissions
RUN mkdir -p uploads reports && chmod 777 uploads reports

# Create a startup script
RUN echo '#!/bin/bash\n\
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
echo "RENDER_EXTERNAL_URL set: $(if [ -n "$RENDER_EXTERNAL_URL" ]; then echo YES - $RENDER_EXTERNAL_URL; else echo NO; fi)"\n\
echo "Starting bot in webhook mode, binding to port ${PORT:-8080}..."\n\
# Make sure we use the right port\n\
export PORT=${PORT:-8080}\n\
# Starting the application\n\
exec python -m app.bot\n' > /app/start.sh && chmod +x /app/start.sh

# Expose the port that the application uses
EXPOSE 8080

# Start the bot using the startup script
CMD ["/app/start.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1 