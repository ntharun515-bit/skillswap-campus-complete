# SkillSwap API Documentation

Base URL: `http://localhost:5000/api`

Authentication: `Authorization: Bearer <access_token>` or JWT cookies after login.

## Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register (body: email, password, full_name, role, campus) |
| POST | `/auth/login` | Login |
| POST | `/auth/logout` | Logout |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Current user + profile |

## Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/freelancers` | List freelancers (?q, ?skill) |
| GET | `/users/freelancers/:id` | Freelancer profile |
| GET/PUT | `/users/profile` | Own freelancer profile |
| POST | `/users/profile/avatar` | Upload avatar (multipart) |
| GET/POST | `/users/skills` | Manage skills |
| GET/POST | `/users/portfolio` | Portfolio items |

## Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects` | List projects |
| POST | `/projects` | Create project (client) |
| GET | `/projects/:id` | Project detail |
| POST | `/projects/:id/apply` | Apply (student) |
| GET | `/projects/:id/applications` | List applicants |
| PUT | `/projects/applications/:id` | Accept/reject |

## Chat (REST + Socket.IO)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chat/conversations` | List conversations |
| POST | `/chat/conversations` | Start conversation |
| GET | `/chat/conversations/:id/messages` | Message history |

**Socket events:** `connect`, `send_message`, `new_message`, `typing`, `notification`

## Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/dashboard` | Platform stats |
| GET/PUT | `/admin/users` | User management |
| GET/PUT | `/admin/reports` | Reports |
| GET/PUT | `/admin/verifications` | Verification queue |

## AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/profile-summary` | Generate profile summary |
| GET | `/ai/skill-suggestions` | Suggested skills |
| GET | `/ai/project-matches` | Matched projects for student |
| POST | `/ai/chatbot` | Public chatbot |
