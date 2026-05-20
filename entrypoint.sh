#!/bin/sh

# Ensure directories exist
mkdir -p /app/database
mkdir -p /app/uploads
mkdir -p /app/logs

DB_FILE="/app/database/skillswap.db"

# Check if SQLite database exists. If not, seed it!
if [ ! -f "$DB_FILE" ]; then
    echo "===================================================="
    echo "📦 Database file not found at $DB_FILE"
    echo "🚀 Initializing and seeding the production database..."
    echo "===================================================="
    python database/init_db.py
    echo "===================================================="
    echo "✅ Database initialized and seeded successfully!"
    echo "===================================================="
else
    echo "===================================================="
    echo "🗄️ SQLite database found at $DB_FILE. Skipping seeding."
    echo "===================================================="
fi

# Run Gunicorn eventlet worker
echo "⚡ Starting SkillSwap Gunicorn eventlet server on port $PORT..."
exec gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT run:app
