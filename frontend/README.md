# PULSE — Frontend Command Center

> **Stack:** Next.js 14 (App Router) · TypeScript · Tailwind CSS · Lucide-React

---

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Set the backend URL (defaults to localhost:8000)
cp .env.example .env.local
# edit NEXT_PUBLIC_API_URL=http://your-fastapi-host:8000

# 3. Run dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of your PULSE FastAPI backend |

Create a `.env.local` file at the root to override:

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## Routes

| Route | Description |
|---|---|
| `/` | Landing — email input → sends magic link |
| `/verify?token=<jwt>` | Auto-verifies token, stores JWT, redirects to `/dashboard` |
| `/dashboard` | Settings — API keys (Vault) + Interest tags (Neural Profile) |

---

## API Contract (FastAPI)

The frontend expects the following endpoints on your FastAPI backend:

### `POST /auth/magic-link`
```json
// Request
{ "email": "user@example.com" }

// Response 200
{ "message": "Magic link sent." }
```

### `POST /auth/verify`
```json
// Request
{ "token": "<opaque-or-jwt-token>" }

// Response 200
{ "access_token": "<jwt>", "token_type": "bearer" }
```

### `GET /user/profile`
```
Authorization: Bearer <jwt>
```
```json
// Response 200
{
  "email": "user@example.com",
  "interests": ["AI Research", "Cybersecurity"],
  "has_groq_key": true,
  "has_tavily_key": false
}
```

### `PUT /user/profile`
```
Authorization: Bearer <jwt>
```
```json
// Request (omit fields you don't want to update)
{
  "groq_api_key": "gsk_...",
  "tavily_api_key": "tvly-...",
  "interests": ["AI Research", "Rust"]
}

// Response 200
{ "message": "Profile updated." }
```

---

## File Structure

```
pulse-frontend/
├── app/
│   ├── globals.css          # Design tokens, glassmorphism, animations
│   ├── layout.tsx           # Root layout + Space Grotesk / Inter fonts
│   ├── page.tsx             # Landing page (/)
│   ├── verify/page.tsx      # Magic-link verify (/verify)
│   └── dashboard/page.tsx   # Settings dashboard (/dashboard)
├── components/
│   ├── PasswordInput.tsx    # Password field with eye toggle
│   └── TagInput.tsx         # Coral pill tag input
└── lib/
    └── api.ts               # Typed fetch wrappers for the FastAPI backend
```

---

## Design System

| Token | Value |
|---|---|
| Background (Obsidian) | `#0B0F19` |
| Primary accent (Electric Indigo) | `#4D4DFF` |
| Tag accent (Neon Coral) | `#FF6B6B` |
| Header font | Space Grotesk |
| Body / input font | Inter |
| Glassmorphism blur | 24 px |

---

## Connecting to PULSE Backend (PULSE FastAPI)

1. Ensure your FastAPI server has CORS configured for `http://localhost:3000` (or your production domain).
2. Set `NEXT_PUBLIC_API_URL` to point at FastAPI.
3. JWT token is stored in `localStorage` under the key `pulse_token` — it's sent as a `Bearer` header on all authenticated requests.
4. The dashboard pre-fetches the profile on mount. If the token is missing or expired, `fetchProfile()` will throw and the error is currently swallowed (defaults are shown). Add a redirect to `/` as needed.
