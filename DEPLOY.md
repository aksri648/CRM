# Hackathon Deploy Checklist

Goal: turn a working but flag-gated codebase into a live demo in ~45 minutes. Every feature is behind a flag that defaults OFF, so flip them on one at a time and verify each step before moving to the next.

If anything looks wrong, re-read the **Verify** line before bumping flags.

---

## 0. Prereqs (5 min)

Sign up and grab the keys. All free tier.

| Service | Sign up at | What to copy |
|---|---|---|
| Clerk | clerk.com | `pk_test_…` (publishable) + frontend API URL (e.g. `https://xxx.clerk.accounts.dev`) |
| Groq | console.groq.com | `gsk_…` API key |
| Resend | resend.com | `re_…` API key + the dashboard URL for webhook config |
| Upstash | upstash.com → Redis | `rediss://default:…@…upstash.io:6379` URL |

Generate one shared secret yourself: `python -c "import secrets; print(secrets.token_urlsafe(32))"` → call it `INTERNAL_SHARED_TOKEN`. You'll paste this same value into 4 places (App, Agent, Comm, Worker).

---

## 1. Render env vars

For each service: Dashboard → Service → Environment → add the keys below. Hit "Save Changes" — Render auto-redeploys.

### App Service (`xeno-crm-app-service`)
```
CLERK_ISSUER=https://xxx.clerk.accounts.dev
INTERNAL_SHARED_TOKEN=<your shared secret>
```
Already set: `DATABASE_URL`, `JWT_SECRET_KEY`, `AGENT_SERVICE_URL`, `COMMUNICATION_SERVICE_URL`.

### Agent Service (`xeno-crm-agent-service`)
```
GROQ_API_KEY=gsk_xxx
LLM_ENABLED=true
REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379
RQ_ENABLED=true
```
Already set: `DATABASE_URL`, `APP_SERVICE_URL`.

### Agent Worker (new Background Worker service — see §3)
Same env vars as Agent Service above.

### Communication Service (`xeno-crm-communication-service`)
```
RESEND_API_KEY=re_xxx
RESEND_FROM_EMAIL=onboarding@resend.dev
RESEND_WEBHOOK_SECRET=<pick any token; use as query string in §2>
EMAIL_SEND_ENABLED=true
INTERNAL_SHARED_TOKEN=<same shared secret as App Service>
WORKFLOWS_ENABLED=true
WORKER_INTERNAL_URL=https://xeno-api-worker.<your-subdomain>.workers.dev
```
Already set: `DATABASE_URL`, `APP_SERVICE_URL`.

> `onboarding@resend.dev` is Resend's official sandbox sender — works without verifying a domain. Demo-safe.

---

## 2. Configure Resend webhook (so delivered/opened events flow back)

1. Resend dashboard → Webhooks → Add endpoint.
2. URL: `https://xeno-crm-communication-service.onrender.com/api/v1/webhooks/resend?token=<RESEND_WEBHOOK_SECRET>`
3. Subscribe events: `email.sent`, `email.delivered`, `email.opened`, `email.clicked`, `email.bounced`, `email.complained`.

---

## 3. Render Background Worker for RQ

Render → New + → Background Worker → connect the same repo and branch.
- **Root Directory:** `backend/agent_service`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python -m app.worker`
- **Env vars:** copy ALL env vars from the Agent Service web service.

> If Render no longer offers a free Background Worker tier on your account: skip this and set `RQ_ENABLED=false` on the Agent Service. The agents will run synchronously inside the HTTP request — slower but still works for demo.

---

## 4. Cloudflare Worker deploy (Workflows + Durable Objects + Cache)

From the `worker/` directory on your laptop:

```bash
cd worker
npx wrangler secret put INTERNAL_SHARED_TOKEN
# paste your shared secret when prompted
npx wrangler deploy
```

This creates:
- `CommandCentreDO` (Durable Object, SQLite-backed, free tier)
- `campaign-pipeline` (Workflow)
- KV cache binding (already exists)

Verify in Cloudflare Dashboard → Workers → `xeno-api-worker` → Bindings.

---

## 5. Frontend env (Render Static Site)

Frontend service → Environment:
```
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxx
VITE_API_URL=https://xeno-api-worker.<your-subdomain>.workers.dev
```
Trigger a manual deploy after saving.

---

## 6. Flip-flag order (do NOT do all at once)

This order minimizes blast radius. After each step, hit the listed verify URL or action.

| Step | Flag(s) | Verify |
|---|---|---|
| 6.1 | `VITE_CLERK_PUBLISHABLE_KEY` set | Open frontend → Clerk SignIn appears → sign up → land on `/` → DevTools shows Authorization header with `Bearer eyJhbGc…` Clerk JWT shape |
| 6.2 | `LLM_ENABLED=true`, `GROQ_API_KEY` set | Generate AI campaign → response shows `agent_count: 8` and `reasoning` text that is clearly LLM-written, not the deterministic stub |
| 6.3 | `RQ_ENABLED=true`, `REDIS_URL` set, worker process running | Generate AI campaign → response is `{"job_id": "...", "status": "queued"}` instantly → App Service polls and returns the final result within ~30s → Upstash dashboard shows command count rising |
| 6.4 | `EMAIL_SEND_ENABLED=true`, `RESEND_API_KEY` set | Launch a campaign targeting 1 customer whose email is YOUR inbox → email arrives → dashboard shows `sent → delivered → opened` after you open it |
| 6.5 | `WORKFLOWS_ENABLED=true`, `WORKER_INTERNAL_URL` set | Launch a campaign with 30+ customers → `npx wrangler workflows list campaign-pipeline` shows a running instance → batches process every 30s |

If a step fails, set its flag back to false. The previous steps keep working.

---

## 7. Demo smoke test (do this 30 minutes before showtime)

1. Open frontend → Clerk SignIn → log in.
2. Dashboard loads. KPIs show real numbers (not "—").
3. Open AI Command Centre overlay → ask "How many customers do we have?" → real number comes back.
4. Refresh page → chat history persists (proves Durable Object).
5. Go to AI Studio → enter goal "Win back customers who haven't bought in 60 days" → submit → ~30s wait → proposal appears with 8 agents listed in the trace.
6. Approve the proposal → Launch campaign targeting your own email → check inbox → email arrives within 1 min → dashboard shows delivered.
7. Open the email → dashboard shows opened.

If all 7 pass: you're demo-ready.

---

## 8. Common gotchas

- **Render free web services sleep after 15 min idle.** Hit each service's `/api/v1/health` URL 2 min before stage time to warm them up.
- **Upstash 10k cmd/day cap.** RQ heartbeats burn ~5k/day on their own. For the demo it's fine; for sustained use disable heartbeats or bump tier.
- **Resend 100 emails/day cap.** Demo campaigns should target a handful of recipients, not your whole customer list.
- **Groq 30 req/min.** Each campaign uses 5 LLM calls. So 6 campaigns/min max — well above demo needs.
- **Clerk login still loops?** Check `CLERK_ISSUER` on the App Service exactly matches the URL in `worker/wrangler.jsonc` and your Clerk dashboard.
- **Email never arrives?** Check Comm Service logs for `resend_send_failed` → most often the `from` address. If you verified your own domain, set `RESEND_FROM_EMAIL` to that.
- **Workflow never runs?** Confirm `INTERNAL_SHARED_TOKEN` matches across Comm Service AND `wrangler secret put`. The Worker rejects the dispatch silently if they differ.

---

## 9. Rollback for stage panic

If any flag misbehaves during the demo, set it back to `false` and refresh. The codebase is designed so each flag failure falls back to the previous working path:

- `LLM_ENABLED=false` → deterministic agent stubs (still produce coherent output)
- `RQ_ENABLED=false` → synchronous agent execution
- `EMAIL_SEND_ENABLED=false` → email simulator (events still fire, no real send)
- `WORKFLOWS_ENABLED=false` → asyncio queue worker (still dispatches, no rate limiting)
- Clerk key missing → legacy login form (any credentials accepted)

That's the entire safety net. Good luck.
