# ==========================================
# 🐳 SkillSwap Production Dockerfile
# ==========================================

# 1. Base Image
FROM python:3.10-slim

# 2. Environment Configurations
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=8080

# 3. Working Directory
WORKDIR /app

# 4. Install Core System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. Cache Python Dependency Layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy App Codebase
COPY . .

# 7. Expose Container Port (Cloud Run binds dynamically via $PORT)
EXPOSE 8080

# 8. Start Gunicorn with high-performance Eventlet worker wrapper for real-time WebSockets!
CMD exec gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT run:app
