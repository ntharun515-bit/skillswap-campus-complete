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

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# 7. Expose Container Port (Cloud Run binds dynamically via $PORT)
EXPOSE 8080

# 8. Run entrypoint script which handles auto-seeding and boots Gunicorn
CMD ["/app/entrypoint.sh"]
