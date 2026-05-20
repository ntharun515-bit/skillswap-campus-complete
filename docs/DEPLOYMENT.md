# Deployment Guide

## Environment Variables

Copy `.env.example` to `.env` and set:

- `SECRET_KEY`, `JWT_SECRET_KEY` — long random strings
- `DATABASE_URL` — MySQL connection string
- `FLASK_ENV=production`
- `CORS_ORIGINS` — your frontend domain(s)

## Render

1. Create **Web Service** from GitHub repo.
2. Build: `pip install -r requirements.txt`
3. Start: `gunicorn --worker-class eventlet -w 1 backend.app:app`
4. Add MySQL addon; set `DATABASE_URL`.
5. Run seed once via shell: `python database/seed.py`

## Railway

1. New project → Deploy from repo.
2. Add MySQL plugin.
3. Start command: `gunicorn --worker-class eventlet -w 1 "backend.app:app" --bind 0.0.0.0:$PORT`
4. Set env vars in Variables tab.

## PythonAnywhere

1. Upload code; create virtualenv and `pip install -r requirements.txt`.
2. Use **MySQL** from PythonAnywhere databases.
3. Configure WSGI to point to `backend.app:app` (SocketIO may need paid plan for WebSockets).
4. Map static files: `/frontend` → `frontend/`, `/uploads` → `uploads/`.

## Production Checklist

- [ ] Strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] `SESSION_COOKIE_SECURE=true`
- [ ] HTTPS only
- [ ] MySQL backups enabled
- [ ] Rate limits configured
- [ ] File upload size limits
- [ ] CORS restricted to your domain

## Local Production Test

```bash
gunicorn --worker-class eventlet -w 1 "backend.app:app" --bind 0.0.0.0:5000
```
