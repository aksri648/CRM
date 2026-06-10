# Xeno CRM — Deployment Guide

End-to-end guide for deploying the Xeno CRM stack: 3 FastAPI microservices, a Cloudflare Worker (with KV cache, Durable Object, and a Workflow), and a Vite React frontend. Everything sits on free tiers.

For a fast hackathon-only checklist, see [`DEPLOY.md`](./DEPLOY.md). This document is the canonical reference.

---

## 1. Architecture at a glance

```
                   ┌──────────────────────┐
                   │   User browser       │
                   │  (React + Vite)      │
                   └──────────┬───────────┘
                              │  Bearer JWT (Clerk or local)
                              ▼
                   ┌──────────────────────┐
                   │  Cloudflare Worker   │  KV cache + Durable Objects
                   │  xeno-api-worker     │  + Workflow dispatcher
                   └──┬──────┬─────────┬──┘
                      │      │         │
            ┌─────────┘      │         └────────────┐
            ▼                ▼                      ▼
   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
   │ App Service    │  │ Agent Service  │  │ Comm Service   │
   │ FastAPI :8001  │  │ FastAPI :8002  │  │ FastAPI :8003  │
   │ - auth         │  │ - LangGraph    │  │ - dispatch     │
   │ - customers    │  │ - 6 LLM agents │  │ - Resend email │
   │ - campaigns    │  │ - NLP module   │  │ - webhooks     │
   │ - analytics    │  │ - RQ jobs      │  │ - queue worker │
   └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
           │                   │                   │
           │           ┌───────┴────────┐          │
           │           │ Upstash Redis  │          │
           │           │ (RQ queue)     │          │
           │           └────────────────┘          │
           │                                       │
           ▼                                       ▼
   ┌────────────────────────────────────────────────────┐
   │              PostgreSQL (Render)                   │
   │  schemas: crm, analytics, system, communications   │
   └────────────────────────────────────────────────────┘
```

External services (all free tier):
- **Clerk** — auth (10 k MAU)
- **Groq** — LLM inference (30 req/min, llama-3.3-70b-versatile)
- **Resend** — transactional email (100/day, 3 000/mo)
- **Upstash** — Redis for RQ (10 k cmds/day)
- **Render** — host the 3 FastAPI services + the static frontend + 1 background worker
- **Cloudflare Workers** — edge proxy, KV cache, Durable Objects, Workflows (free tier)

---

## 2. Prerequisites

| Tool | Why | Install |
|---|---|---|
| `git` | clone & push | system pkg |
| `gh` CLI | optional, for `gh pr` flows | https://cli.github.com |
| `node >= 18` | build frontend + worker | https://nodejs.org |
| `python >= 3.11` | run services locally | https://python.org |
| `wrangler` | deploy Cloudflare Worker | `npm i -g wrangler` (or use `npx`) |

Accounts (all free):
- GitHub (you have this — repo is `aksri648/CRM`)
- Render (https://render.com)
- Cloudflare (https://cloudflare.com)
- Clerk, Groq, Resend, Upstash — sign up on demand

---

## 3. Environment-variable matrix

Single source of truth for every key needed across the stack. Use this when filling in Render / Cloudflare dashboards.

| Variable | Service(s) | Required? | Default | Notes |
|---|---|---|---|---|
| `DATABASE_URL` | App, Comm | yes | — | Render Postgres connection string (`postgresql+asyncpg://…`) |
| `JWT_SECRET_KEY` | App | yes | — | Any 32+ char random; used by local login |
| `JWT_ALGORITHM` | App | no | `HS256` | |
| `JWT_EXPIRE_MINUTES` | App | no | `1440` | 24 h |
| `CLERK_ISSUER` | App, Worker | yes for Clerk | — | e.g. `https://capable-airedale-73.clerk.accounts.dev` |
| `VITE_CLERK_PUBLISHABLE_KEY` | Frontend | yes for Clerk | — | `pk_test_…` |
| `AGENT_SERVICE_URL` | App | yes | `http://agent-service:8002` | Render internal URL |
| `COMMUNICATION_SERVICE_URL` | App | yes | `http://comm-service:8003` | Render internal URL |
| `APP_SERVICE_URL` | Agent, Comm, Worker | yes | `http://app-service:8001` | Render internal URL |
| `INTERNAL_SHARED_TOKEN` | App, Comm, Worker | yes | — | One value, paste in 3 places — gates internal endpoints |
| `GROQ_API_KEY` | Agent | optional | — | `gsk_…`; turn on `LLM_ENABLED` together |
| `GROQ_MODEL` | Agent | no | `llama-3.3-70b-versatile` | |
| `LLM_ENABLED` | Agent | no | `false` | Flip to `true` after `GROQ_API_KEY` is set |
| `LLM_TIMEOUT_SECONDS` | Agent | no | `30` | Per-request timeout |
| `NLP_CLASSIFIER_ENABLED` | Agent | no | `true` | Deterministic segment classifier; safe to leave on |
| `NLP_OVERRIDE_THRESHOLD` | Agent | no | `0.75` | Confidence above which NLP overrides LLM segment |
| `REDIS_URL` | Agent + Worker(bg) | optional | — | `rediss://default:…@…upstash.io:6379` |
| `RQ_ENABLED` | Agent + Worker(bg) | no | `false` | Flip on after Redis is up + background worker running |
| `RQ_QUEUE_NAME` | Agent + Worker(bg) | no | `agent-jobs` | |
| `RQ_JOB_TIMEOUT` | Agent + Worker(bg) | no | `300` | Seconds |
| `RESEND_API_KEY` | Comm | optional | — | `re_…` |
| `RESEND_FROM_EMAIL` | Comm | no | `onboarding@resend.dev` | Resend's sandbox sender — works without domain verification |
| `RESEND_WEBHOOK_SECRET` | Comm | optional | — | You pick; used as `?token=` query string in Resend webhook URL |
| `EMAIL_SEND_ENABLED` | Comm | no | `false` | Flip on after `RESEND_API_KEY` is set |
| `WORKFLOWS_ENABLED` | Comm | no | `false` | Flip on after Cloudflare Worker is deployed |
| `WORKER_INTERNAL_URL` | Comm | yes for Workflows | — | e.g. `https://xeno-api-worker.you.workers.dev` |
| `WORKFLOW_BATCH_SIZE` | Comm | no | `25` | |
| `WORKFLOW_RATE_LIMIT_SECONDS` | Comm | no | `30` | Gap between batches |
| `VITE_API_URL` | Frontend | yes | — | Cloudflare Worker URL (NOT App Service) |
| `COMM_SERVICE_URL` | Worker (vars) | yes | — | Public URL of Comm Service (Render) |
| `DEFAULT_TTL` | Worker (vars) | no | `300` | KV cache TTL seconds |

The big rule: every flag named `*_ENABLED` defaults to `false` so a fresh deploy is safe. Flip them on one at a time after the underlying credential is in place.

---

## 4. Database setup

A managed Postgres on Render is enough. Free tier expires after 90 days; rotate.

1. Render dashboard → **New +** → **PostgreSQL** → choose free tier → name `xeno-crm-db`.
2. After provisioning, copy the **Internal Database URL** (asyncpg format starts with `postgresql+asyncpg://`; if Render gives `postgresql://`, swap the prefix).
3. The schemas (`crm`, `analytics`, `system`, `communications`) and tables are created on App Service startup by SQLAlchemy. Seed data via `POST /api/v1/seed` after the service is up.

---

## 5. Render service setup (4 services)

For each service: **New +** → **Web Service** (or Background Worker) → connect this GitHub repo → branch `main`.

### 5.1 App Service (`xeno-crm-app-service`)
- **Root Directory:** `backend/app_service`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Env vars:** `DATABASE_URL`, `JWT_SECRET_KEY`, `AGENT_SERVICE_URL`, `COMMUNICATION_SERVICE_URL`, `INTERNAL_SHARED_TOKEN`, optionally `CLERK_ISSUER`.

### 5.2 Agent Service (`xeno-crm-agent-service`)
- **Root Directory:** `backend/agent_service`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Env vars:** `APP_SERVICE_URL`, `INTERNAL_SHARED_TOKEN`. Add `GROQ_API_KEY` + `LLM_ENABLED=true` for AI inference. Add `REDIS_URL` + `RQ_ENABLED=true` for async jobs.

### 5.3 Agent Worker (Background Worker — optional but recommended)
Only required if `RQ_ENABLED=true`. Without it, agent jobs queued in Redis will never run.
- **New +** → **Background Worker**
- **Root Directory:** `backend/agent_service`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python -m app.worker`
- **Env vars:** copy ALL env vars from the Agent Service web service.

If Render's free Background Worker tier isn't available on your account, set `RQ_ENABLED=false` on the Agent Service. LangGraph runs synchronously in the HTTP request — slower (~30 s per campaign) but works.

### 5.4 Communication Service (`xeno-crm-communication-service`)
- **Root Directory:** `backend/communication_service`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Env vars:** `DATABASE_URL`, `APP_SERVICE_URL`, `INTERNAL_SHARED_TOKEN`. Add `RESEND_API_KEY` + `EMAIL_SEND_ENABLED=true` for real email. Add `WORKER_INTERNAL_URL` + `WORKFLOWS_ENABLED=true` for Cloudflare-orchestrated dispatch.

### 5.5 Frontend (Static Site)
- **New +** → **Static Site**
- **Root Directory:** `frontend`
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `dist`
- **Env vars:** `VITE_API_URL` (= Cloudflare Worker URL), `VITE_CLERK_PUBLISHABLE_KEY` (if using Clerk).

---

## 6. Cloudflare Worker deploy

The Worker handles:
1. KV-cached proxy in front of App Service GETs.
2. Durable Object–backed Command Centre chat history (`CommandCentreDO`).
3. The `CampaignPipeline` Workflow that paces large email dispatches.

```bash
cd worker
npm install
npx wrangler login                # one-time, opens browser
npx wrangler secret put INTERNAL_SHARED_TOKEN
# paste the same value used on App + Comm services
npx wrangler deploy
```

On first deploy:
- Wrangler reads `wrangler.jsonc` — confirms `migrations.v1` will create `CommandCentreDO` as a SQLite-backed Durable Object (free tier).
- Wrangler creates the `campaign-pipeline` Workflow.
- KV namespace ID in `wrangler.jsonc` must already exist (it does — `fc3027c4…`).

After deploy:
```bash
npx wrangler tail                 # live logs
npx wrangler workflows list campaign-pipeline   # see running instances
```

### Worker `vars` to set (in `wrangler.jsonc`)
- `CLERK_ISSUER` — must match the App Service env var
- `COMM_SERVICE_URL` — full https URL of Comm Service on Render
- `DEFAULT_TTL` — `"300"` is fine

### Worker secrets to set via `wrangler secret put`
- `INTERNAL_SHARED_TOKEN` — same value as App + Comm services
- `APP_SERVICE_URL` — already in Cloudflare Secrets Store; see `wrangler.jsonc` `secrets_store_secrets`

---

## 7. Resend webhook configuration

Once `EMAIL_SEND_ENABLED=true` and emails start flowing, Resend posts delivery events back. Wire the endpoint:

1. Resend dashboard → **Webhooks** → **Add endpoint**.
2. URL: `https://xeno-crm-communication-service.onrender.com/api/v1/webhooks/resend?token=<RESEND_WEBHOOK_SECRET>`
3. Subscribe events: `email.sent`, `email.delivered`, `email.opened`, `email.clicked`, `email.bounced`, `email.complained`.

The handler maps each event type to an internal status (sent, delivered, opened, clicked, failed) and writes a `CommunicationEvent` row. Re-runs are idempotent at the event-record level.

---

## 8. Clerk setup

1. Sign up at clerk.com → create application (any name) → **API Keys**.
2. Copy the **Publishable Key** (`pk_test_…`) → put in frontend `VITE_CLERK_PUBLISHABLE_KEY`.
3. Copy your **Frontend API URL** (e.g. `https://capable-airedale-73.clerk.accounts.dev`) → put in:
   - App Service `CLERK_ISSUER` env var
   - Worker `vars.CLERK_ISSUER` in `wrangler.jsonc`
4. Redeploy frontend + App Service + Worker.

The backend verifies Clerk JWTs via JWKS (`{issuer}/.well-known/jwks.json`). If `CLERK_ISSUER` is empty, the backend falls back to the local `JWT_SECRET_KEY`-signed token from the legacy login form.

---

## 9. Flag-flip order

Each flag has a fall-through default, so flipping safely is just a matter of order. Verify each step before moving on.

| Step | Flag(s) | What to verify |
|---|---|---|
| 9.1 | `CLERK_ISSUER` + `VITE_CLERK_PUBLISHABLE_KEY` | Open frontend → Clerk SignIn appears → sign up → land on `/` → DevTools network panel shows Clerk-issued JWT on API calls |
| 9.2 | `LLM_ENABLED=true` (+ `GROQ_API_KEY`) | Generate AI campaign → proposal shows `agent_count: 8`, reasoning text is clearly LLM-written, segment `supporting_data.nlp` block is populated |
| 9.3 | `RQ_ENABLED=true` (+ `REDIS_URL`, background worker running) | Generate campaign → response is `{"job_id": "...", "status": "queued"}` instantly → App Service polls and returns result within ~30 s |
| 9.4 | `EMAIL_SEND_ENABLED=true` (+ `RESEND_API_KEY`, webhook configured) | Launch campaign targeting your own inbox → email arrives → dashboard shows `sent → delivered → opened` |
| 9.5 | `WORKFLOWS_ENABLED=true` (+ `WORKER_INTERNAL_URL`, Worker deployed) | Launch campaign w/ 30+ customers → `npx wrangler workflows list campaign-pipeline` shows a running instance → batches process every 30 s |

If a step fails, set the flag back to `false`. The previous configuration keeps working.

---

## 10. Feature flag inventory

Every flag, what enables/disables, and the fallback when off.

| Flag | When ON | When OFF (default) |
|---|---|---|
| `LLM_ENABLED` | 6 Atlas/Sophia/Mercury/Nova/Athena/CommandCentre agents call Groq | Deterministic stubs return coherent canned output |
| `NLP_CLASSIFIER_ENABLED` | Atlas runs deterministic NLP segmentation alongside LLM | Atlas uses legacy substring keyword match |
| `RQ_ENABLED` | Agent jobs enqueue to Redis; HTTP returns `job_id` instantly | Agent runs in the HTTP request (synchronous, ~30s) |
| `EMAIL_SEND_ENABLED` | Real email via Resend API for channel=email | Probabilistic simulator fires events without sending |
| `WORKFLOWS_ENABLED` | Comm Service POSTs dispatch to Cloudflare Worker; Workflow paces batches | Asyncio queue worker in Comm Service handles dispatch directly |

---

## 11. Verification — end-to-end smoke test

Run this after every deploy. Should complete in <5 minutes.

1. **Frontend loads** → no console errors. Clerk SignIn renders (if enabled).
2. **Auth round-trip** → sign in → land on `/` → DevTools shows `Authorization: Bearer …` on `/api/v1/dashboard/stats`.
3. **Dashboard renders** → KPIs show real numbers from DB. If "—" everywhere, run `POST /api/v1/seed`.
4. **NLP endpoint** → `curl -X POST $WORKER_URL/api/v1/nlp/classify -H 'Authorization: Bearer <token>' -d '{"text":"Win back customers who haven\'t bought in 60 days"}'` → returns `{"segment_key":"inactive", "confidence":..., "features":{...}}`.
5. **AI Command Centre** → open overlay → "How many customers?" → real number returned. Refresh → history persists (Durable Object).
6. **Campaign generation** → AI Studio → enter goal → submit → wait for proposal. Confirm `proposal.agent_count === 8` and `audience.supporting_data.nlp.matched_features` is populated.
7. **Approval + launch** → approve → launch targeting one address you own.
8. **Email delivery** → check inbox. Within ~1 min: dashboard shows `sent → delivered`. Open the email: `opened`.

---

## 12. Common gotchas

- **Render free web services sleep after 15 min idle.** Ping each service's `/api/v1/health` before any time-sensitive demo.
- **Cold start can take 30 s on Render free tier.** The first request after sleep is slow; subsequent ones are fast.
- **Upstash 10 k cmd/day cap.** RQ heartbeats burn ~5 k/day on their own. Fine for demos, monitor for sustained use.
- **Resend 100 emails/day, 3 000/mo.** Demo campaigns should target a few recipients, not your whole customer list.
- **Groq 30 req/min.** Each campaign uses 5 LLM calls → ~6 campaigns/min ceiling. Plenty for demos.
- **`CLERK_ISSUER` mismatch.** It must match in three places: Clerk dashboard, App Service env, Worker `vars`. Trailing slash matters.
- **Resend `from` rejected.** `onboarding@resend.dev` works without domain verification. If you set your own `from`, you must verify the domain first.
- **Workflow never runs.** Confirm `INTERNAL_SHARED_TOKEN` matches exactly across Comm + Worker. Workers silently 401 mismatched dispatches.
- **NLP classifier overrides too aggressively.** Lower `NLP_OVERRIDE_THRESHOLD` only if you've audited the lexicons.

---

## 13. Rollback table

If something breaks live, flip the relevant flag and refresh. Each flag's `false` state is a known-working fallback.

| Symptom | Flag to flip | Result |
|---|---|---|
| Agents return nonsense / Groq errors | `LLM_ENABLED=false` | Deterministic agent stubs |
| Agent requests hang | `RQ_ENABLED=false` | Synchronous in-request execution |
| Emails not sending / Resend errors | `EMAIL_SEND_ENABLED=false` | Probabilistic event simulation |
| Worker workflow stuck | `WORKFLOWS_ENABLED=false` | Asyncio queue in Comm Service |
| Clerk login loop | Remove `VITE_CLERK_PUBLISHABLE_KEY` | Legacy login form (accepts any credentials) |
| NLP misclassifies | `NLP_CLASSIFIER_ENABLED=false` | Legacy keyword fallback path |

---

## 14. Local development

For developing without deploying:

```bash
# Postgres locally
docker run -d --name xeno-pg -e POSTGRES_USER=xeno -e POSTGRES_PASSWORD=xeno \
  -e POSTGRES_DB=xeno -p 5432:5432 postgres:16

# Each service in its own terminal
cd backend/app_service && pip install -r requirements.txt && uvicorn app.main:app --port 8001 --reload
cd backend/agent_service && pip install -r requirements.txt && uvicorn app.main:app --port 8002 --reload
cd backend/communication_service && pip install -r requirements.txt && uvicorn app.main:app --port 8003 --reload

# Frontend
cd frontend && npm install && npm run dev   # http://localhost:5173

# Worker (skips Workflows in dev unless --remote)
cd worker && npx wrangler dev
```

All `*_ENABLED` flags default to `false` so the stack runs entirely on stubs locally with no external accounts.

To test the NLP classifier offline:
```bash
cd backend/agent_service
python -m app.nlp.tests
```

---

## 15. NLP segmentation module reference

The deterministic NLP segmentation lives in `backend/agent_service/app/nlp/`. Pure-Python, no external deps.

**Entry points:**
```python
from app.nlp import classify, extract_features, SegmentPrediction, GoalFeatures

pred = classify("Win back customers who haven't bought in 60 days")
# pred.segment_key, pred.confidence, pred.raw_scores, pred.winning_matches, pred.rationale

feats = extract_features("Reward our VIP loyal customers")
# feats.tokens, feats.segment_matches, feats.time_horizon_days,
# feats.intent_categories, feats.value_markers
```

**HTTP endpoint:**
```
POST /api/v1/nlp/classify
{"text": "Reactivate dormant customers from the holiday cohort"}
→ {
    "segment_key": "reactivation",
    "confidence": 0.83,
    "raw_scores": {...},
    "winning_matches": [...],
    "rationale": "Classified as 'reactivation' on evidence: reactivate, dormant. ...",
    "features": {...}
  }
```

**Integration in Atlas:**
1. Always runs (if `NLP_CLASSIFIER_ENABLED=true`).
2. If LLM is off → NLP's choice is final.
3. If LLM is on AND they disagree AND NLP confidence ≥ `NLP_OVERRIDE_THRESHOLD` → NLP overrides.
4. NLP evidence is always attached to `audience.supporting_data.nlp` for transparency.

**Lexicons** (`lexicons.py`):
- `SEGMENT_LEXICONS` — six segment → `[(pattern, weight)]` dictionaries
- `INTENT_VERBS` — verb category → conjugated forms
- `VALUE_MARKERS` — phrases denoting customer-value tiers
- `NEGATION_TOKENS` — suppresses nearby matches
- `CONTRACTIONS` — expanded before tokenization

To tune: edit `lexicons.py`, run `python -m app.nlp.tests`, iterate.
