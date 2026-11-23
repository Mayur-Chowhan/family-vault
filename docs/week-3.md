# Week 3 — Users, families and authentication

## Database (migration `f6286e3bd36d`)

- `users` — id, email (unique), password_hash, display_name, timestamps
- `family_members` — family_id + user_id (unique pair), role
  (`owner`/`admin`/`member`), timestamps via created_at
- `family_invitations` — family_id, email, role, token (unique), invited_by,
  expires_at, accepted_at

## Backend

### Auth (`app/routers/auth.py`, prefix `/api/v1/auth`)
- `POST /register` — email + password (min 8) + display_name → 201 + JWT
- `POST /login` — email + password → JWT (`TokenResponse`)
- `GET /me` — current user

### Security (`app/security.py`, `app/deps.py`)
- Passwords hashed with **argon2** via `pwdlib` (`PasswordHash.recommended()`)
- JWT (HS256, PyJWT), `SECRET_KEY` in `.env`, 7-day expiry
- `HTTPBearer` auth → `get_current_user` dependency (401 on missing/invalid)
- `require_membership(family_id)` → 404 if family missing, 403 if not a member
- Role checks via `require_family_role_dependency({"owner","admin"})`

### Families (`app/routers/families.py`)
- All endpoints now require auth
- `POST /families` — creator becomes `owner`
- `GET /families` — only families the user belongs to
- `PATCH`/`DELETE` — owner/admin only
- `GET /{id}/members` — any member (eager-loads user via selectinload)
- `DELETE /{id}/members/{member_id}` — owner/admin; cannot remove owner

### Albums — all endpoints require family membership

### Invitations (`app/routers/invitations.py`)
- `POST /families/{id}/invitations` — owner/admin; `{email, role}` → token
- `GET /families/{id}/invitations` — owner/admin list
- `GET /invitations/mine` — pending invites for current user's email
- `POST /invitations/{token}/accept` — validates expiry (7d), single-use,
  email match, non-member → creates FamilyMember with invite's role

## Frontend (Angular)

- `auth/auth.service.ts` — signal-based user state, token in localStorage,
  login/register/logout
- `auth/auth.interceptor.ts` — attaches `Authorization: Bearer` to all requests
- `auth/auth.guard.ts` — protects `/` route
- `login/` + `register/` pages (shared CSS), `home/` — protected page listing
  families + create-family form, calls real API at `localhost:8000`
- `api.ts` — `API_URL` constant + shared interfaces

## Tests — 36 passing

- `test_auth.py` — register/login/me, duplicate email, weak password, bad token
- `test_families.py` — updated for auth; ownership, 403 non-member, member list
- `test_albums.py` — updated for auth; membership enforcement
- `test_invitations.py` — full invite→accept flow, wrong-email reject,
  member/stranger cannot invite, single-use token, admin permissions

## Gotchas

- Dependency functions can't be declared after the routes that use them —
  decorator args evaluate at import time.
- `FamilyMember.user.has(...)` doesn't work for many-to-one; use a join.
- Auth check order matters: verify family exists (404) before membership (403).
- JWT secret must be ≥32 bytes for HS256 (PyJWT warns otherwise).
