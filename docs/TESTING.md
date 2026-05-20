# Testing Guide

## Manual Testing Checklist

### Authentication
- [ ] Register as student and client
- [ ] Login/logout
- [ ] JWT persists in localStorage
- [ ] Protected routes redirect when logged out

### Student
- [ ] Update profile, upload avatar
- [ ] Add skills and portfolio items
- [ ] Browse and apply to projects
- [ ] Save/bookmark jobs
- [ ] View applications status
- [ ] Real-time chat with client
- [ ] AI profile summary and project matches

### Client
- [ ] Post project with budget and deadline
- [ ] View applicants; accept/reject
- [ ] Update project progress
- [ ] Record payment milestone
- [ ] Save freelancers

### Admin
- [ ] Dashboard stats load
- [ ] Ban user
- [ ] Resolve report
- [ ] Approve verification
- [ ] Manage categories

### UI
- [ ] Dark/light theme toggle
- [ ] Mobile responsive sidebar
- [ ] Toast notifications on actions

## API Testing (curl)

```bash
# Health
curl http://127.0.0.1:5000/api/health

# Register
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@test.edu\",\"password\":\"Test1234!\",\"full_name\":\"Test User\",\"role\":\"student\",\"campus\":\"Demo U\"}"

# Login
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"alex@campus.edu\",\"password\":\"Demo123!\"}"
```

## Automated Tests (optional extension)

Add `pytest` and `tests/test_auth.py` for unit tests on auth and projects endpoints.
