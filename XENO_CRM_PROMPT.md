# XENO AI-Native Mini CRM — Full Production Architecture & Build Prompt
### Senior Engineering Spec | 20+ Years Salesforce-Grade Standards
### Assignment: Xeno Engineering Internship 2026

---

## TABLE OF CONTENTS

1. [Project Philosophy & Scope](#1-project-philosophy--scope)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Tech Stack & Rationale](#3-tech-stack--rationale)
4. [Monorepo Structure](#4-monorepo-structure)
5. [Frontend — React + Shadcn + Salesforce Lightning Theme](#5-frontend--react--shadcn--salesforce-lightning-theme)
6. [Main Backend — Express.js + Prisma + PostgreSQL](#6-main-backend--expressjs--prisma--postgresql)
7. [Agent Backend — FastAPI + LangGraph](#7-agent-backend--fastapi--langgraph)
8. [Channel Service — Stubbed Delivery Simulator](#8-channel-service--stubbed-delivery-simulator)
9. [Redis Architecture — Caching, Queues & Pub/Sub](#9-redis-architecture--caching-queues--pubsub)
10. [Complete Database Schema (Prisma)](#10-complete-database-schema-prisma)
11. [Full API Contract Reference](#11-full-api-contract-reference)
12. [LangGraph Agent Definitions](#12-langgraph-agent-definitions)
13. [Environment Variables](#13-environment-variables)
14. [Seed Data Strategy](#14-seed-data-strategy)
15. [Deployment Architecture](#15-deployment-architecture)
16. [Error Handling & Observability](#16-error-handling--observability)
17. [Scalability Tradeoffs & Notes](#17-scalability-tradeoffs--notes)

---

## 1. PROJECT PHILOSOPHY & SCOPE

### What We're Building
An **AI-native Mini CRM** for a D2C or retail brand (e.g. fashion label, coffee chain, beauty brand).
The marketer can ingest customer + order data, segment shoppers intelligently, run personalised campaigns across WhatsApp/SMS/Email/RCS, and surface rich analytics — with AI woven into every step.

### AI-Native Stance
This is **not** an AI chatbot bolted onto a traditional CRM. AI is the primary engine of the product:
- LangGraph agents power the segment builder (natural language → rule set)
- AI drafts personalised message copies per audience segment
- A campaign orchestration agent assists end-to-end from intent to dispatch
- AI surfaces insight summaries from campaign analytics
- A conversational assistant sidebar lets marketers query data in plain English

### Scope Decisions (What We Build vs. What We Don't)
| ✅ Build | ❌ Explicitly Out of Scope |
|---|---|
| Customer + Order ingestion (CSV + API) | Deals/Pipeline/Tickets (no Salesforce Sales Cloud) |
| AI-powered audience segmentation | Real messaging provider integrations |
| Campaign creation + dispatch | Mobile app |
| Stubbed channel service with full event lifecycle | Multi-tenant SaaS billing |
| Campaign analytics dashboard | Deep ML model training |
| LangGraph agents for segment/copy/insights | Complex AB testing engine |
| Redis caching throughout | Advanced auth (OAuth, SSO) |
| Webhook callback loop | |

### Scale Assumption (Stated Explicitly)
- Designed for ~100K customers, ~1M orders, ~10 campaigns/day
- Redis caching covers hot reads; no sharding needed at this scale
- BullMQ handles async callback queue; at 1M+ events/day, migrate to Kafka
- PostgreSQL single-instance with read replica is sufficient; partition `communications` at 10M+ rows

---

## 2. SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          BROWSER CLIENT                                 │
│              React + Shadcn/UI  (Salesforce Lightning Theme)            │
│                         Port 5173 (Vite dev)                            │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ HTTPS REST
          ┌────────────────────▼─────────────────────┐
          │         MAIN BACKEND — Express.js         │
          │     Node 20 LTS  |  TypeScript            │
          │     Port 3001                             │
          │   ┌───────────┐  ┌──────────────────┐    │
          │   │  Prisma   │  │  BullMQ Workers  │    │
          │   │   ORM     │  │ (callback queue) │    │
          │   └─────┬─────┘  └────────┬─────────┘    │
          └─────────│────────────────│───────────────┘
                    │                │
         ┌──────────▼──────┐  ┌─────▼────────────┐
         │  PostgreSQL 16   │  │   Redis 7 (Cloud) │
         │  (Primary DB)    │  │ Cache + BullMQ    │
         └─────────────────┘  └──────────────────┘
                    │
          ┌─────────▼──────────────────────────────┐
          │    AGENT BACKEND — FastAPI + LangGraph  │
          │    Python 3.12  |  Port 8000            │
          │  ┌──────────────────────────────────┐  │
          │  │  LangGraph StateGraph Agents      │  │
          │  │  - SegmentBuilderAgent            │  │
          │  │  - MessageCrafterAgent            │  │
          │  │  - CampaignOrchestratorAgent      │  │
          │  │  - InsightSummaryAgent            │  │
          │  │  - NLQueryAgent                   │  │
          │  └──────────────────────────────────┘  │
          │    + Redis for agent state caching      │
          └────────────────────────────────────────┘
                    │
          ┌─────────▼──────────────────────────────┐
          │    CHANNEL SERVICE — Express.js Stub    │
          │    Port 3002                            │
          │  Receives send requests → simulates     │
          │  delivery → async callbacks → CRM API   │
          └────────────────────────────────────────┘
```

### Request Flow: Campaign Send
```
Marketer clicks "Launch Campaign"
  → Express /api/campaigns/:id/launch
    → Creates Communication records (status: QUEUED)
    → Publishes batch to BullMQ "send-queue"
      → BullMQ Worker picks up job
        → POST /send to Channel Service (per recipient batch)
          → Channel Service queues simulated delivery
            → After random delay (1-10s), POST /api/webhooks/channel/:communicationId
              → CRM updates Communication status (DELIVERED/FAILED/OPENED/READ/CLICKED)
                → Redis cache for analytics is invalidated
                  → Frontend polls /api/campaigns/:id/analytics
```

---

## 3. TECH STACK & RATIONALE

| Layer | Technology | Version | Why |
|---|---|---|---|
| Frontend Framework | React | 18.3 | Concurrent features, ecosystem |
| Frontend Build | Vite | 5.x | Fast HMR, ESM native |
| UI Components | Shadcn/UI | Latest | Radix-based, headless, fully themeable |
| CSS | Tailwind CSS | 3.4 | Utility-first, Salesforce vars override |
| State Management | Zustand | 4.x | Lightweight, no boilerplate |
| Server State | TanStack Query | 5.x | Cache, background sync, optimistic updates |
| Forms | React Hook Form + Zod | Latest | Type-safe validation |
| Charts | Recharts | 2.x | Composable, React-native |
| Table | TanStack Table | 8.x | Headless, virtualised |
| Main Backend | Express.js | 4.x | Battle-tested, composable |
| Backend Language | TypeScript | 5.x | Type safety end-to-end |
| ORM | Prisma | 5.x | Type-safe queries, migrations |
| Primary DB | PostgreSQL | 16 | ACID, JSONB, full-text search |
| Cache / Queue | Redis | 7 | Cache + BullMQ job queues |
| Job Queue | BullMQ | 5.x | Redis-backed, retry, backoff |
| Agent Framework | LangGraph | 0.2 | Stateful, cyclical agent graphs |
| Agent Runtime | FastAPI | 0.115 | Async Python, OpenAPI auto-docs |
| AI Model | Claude claude-sonnet-4-20250514 (Anthropic) | Latest | Instruction following, tool use |
| Validation (BE) | Zod (Node) / Pydantic (Python) | Latest | Schema-first validation |
| Auth | JWT + bcrypt | - | Stateless, refresh token pattern |
| Container | Docker + docker-compose | Latest | Reproducible environments |
| Deployment | Railway / Render / Fly.io | - | Simple PaaS for assignment scope |

---

## 4. MONOREPO STRUCTURE

```
xeno-crm/
├── packages/
│   ├── frontend/               # React + Vite + Shadcn
│   ├── backend/                # Express.js + Prisma
│   ├── agent-service/          # FastAPI + LangGraph
│   └── channel-service/        # Express.js stubbed channel
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── package.json                # Root workspace (pnpm)
├── pnpm-workspace.yaml
└── README.md
```

### Root `package.json` (pnpm workspaces)
```json
{
  "name": "xeno-crm",
  "private": true,
  "scripts": {
    "dev": "concurrently \"pnpm --filter backend dev\" \"pnpm --filter frontend dev\" \"pnpm --filter channel-service dev\"",
    "build": "pnpm --filter backend build && pnpm --filter frontend build",
    "db:migrate": "pnpm --filter backend db:migrate",
    "db:seed": "pnpm --filter backend db:seed"
  }
}
```

---

## 5. FRONTEND — React + Shadcn + Salesforce Lightning Theme

### 5.1 Salesforce Lightning Design System (SLDS) Theme Override

The entire app uses Salesforce Lightning-inspired design tokens via Tailwind CSS custom properties.

#### `packages/frontend/src/styles/salesforce-theme.css`
```css
:root {
  /* Brand Colors — Salesforce Lightning */
  --sf-brand-primary: #0176d3;        /* SLDS Blue */
  --sf-brand-primary-dark: #014486;
  --sf-brand-primary-light: #1b96ff;
  --sf-brand-primary-bg: #e8f4fd;

  /* Neutral Palette */
  --sf-neutral-1: #ffffff;
  --sf-neutral-2: #f3f3f3;            /* Page background */
  --sf-neutral-3: #e5e5e5;
  --sf-neutral-4: #dddbda;            /* Border color */
  --sf-neutral-5: #c9c7c5;
  --sf-neutral-6: #aeacab;
  --sf-neutral-7: #706e6b;
  --sf-neutral-8: #3e3e3c;
  --sf-neutral-9: #1c1b1a;
  --sf-neutral-10: #080707;

  /* Semantic Colors */
  --sf-color-success: #2e844a;
  --sf-color-success-bg: #eff7f0;
  --sf-color-warning: #dd7a01;
  --sf-color-warning-bg: #fef8ee;
  --sf-color-error: #ba0517;
  --sf-color-error-bg: #fef1f1;
  --sf-color-info: #0176d3;
  --sf-color-info-bg: #e8f4fd;

  /* Typography */
  --sf-font-family: 'Salesforce Sans', -apple-system, BlinkMacSystemFont,
    'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --sf-font-size-base: 14px;
  --sf-font-size-sm: 12px;
  --sf-font-size-lg: 16px;
  --sf-font-size-xl: 20px;
  --sf-font-size-2xl: 24px;

  /* Spacing */
  --sf-spacing-xs: 4px;
  --sf-spacing-sm: 8px;
  --sf-spacing-md: 12px;
  --sf-spacing-lg: 16px;
  --sf-spacing-xl: 24px;
  --sf-spacing-2xl: 32px;

  /* Shadows */
  --sf-shadow-sm: 0 2px 2px rgba(0,0,0,0.10);
  --sf-shadow-md: 0 4px 8px rgba(0,0,0,0.12);
  --sf-shadow-lg: 0 8px 16px rgba(0,0,0,0.15);

  /* Border Radius */
  --sf-radius-sm: 4px;
  --sf-radius-md: 8px;
  --sf-radius-lg: 12px;

  /* Header */
  --sf-header-height: 52px;
  --sf-nav-width: 240px;
}
```

#### `packages/frontend/tailwind.config.ts`
```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: 'var(--sf-brand-primary)',
          dark: 'var(--sf-brand-primary-dark)',
          light: 'var(--sf-brand-primary-light)',
          bg: 'var(--sf-brand-primary-bg)',
        },
        neutral: {
          1: 'var(--sf-neutral-1)',
          2: 'var(--sf-neutral-2)',
          3: 'var(--sf-neutral-3)',
          4: 'var(--sf-neutral-4)',
          7: 'var(--sf-neutral-7)',
          8: 'var(--sf-neutral-8)',
        },
        success: 'var(--sf-color-success)',
        warning: 'var(--sf-color-warning)',
        error: 'var(--sf-color-error)',
      },
      fontFamily: {
        sf: ['var(--sf-font-family)'],
      },
      boxShadow: {
        'sf-sm': 'var(--sf-shadow-sm)',
        'sf-md': 'var(--sf-shadow-md)',
        'sf-lg': 'var(--sf-shadow-lg)',
      },
      borderRadius: {
        'sf': 'var(--sf-radius-md)',
      },
    },
  },
  plugins: [],
}

export default config
```

#### `packages/frontend/src/components/ui/` — Shadcn Overrides
Shadcn's `components.json` should be configured to use the Salesforce palette:
```json
{
  "style": "default",
  "rsc": false,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/styles/globals.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

Override Shadcn's `globals.css` CSS variables to map to Salesforce tokens:
```css
@layer base {
  :root {
    --background: 0 0% 95.3%;          /* sf-neutral-2 */
    --foreground: 0 0% 11%;            /* sf-neutral-9 */
    --card: 0 0% 100%;
    --card-foreground: 0 0% 11%;
    --primary: 207 97% 42%;            /* sf-brand-primary #0176d3 */
    --primary-foreground: 0 0% 100%;
    --secondary: 207 97% 95%;          /* sf-brand-primary-bg */
    --secondary-foreground: 207 97% 15%;
    --muted: 0 0% 95%;
    --muted-foreground: 0 0% 44%;
    --accent: 207 97% 42%;
    --accent-foreground: 0 0% 100%;
    --destructive: 354 88% 40%;        /* sf-color-error */
    --border: 0 0% 86%;                /* sf-neutral-4 */
    --input: 0 0% 86%;
    --ring: 207 97% 42%;
    --radius: 0.25rem;                 /* sf-radius-sm */
  }
}
```

---

### 5.2 Frontend Project Structure

```
packages/frontend/src/
├── app/                        # Route definitions
│   └── router.tsx
├── components/
│   ├── ui/                     # Shadcn components (auto-generated)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── table.tsx
│   │   ├── badge.tsx
│   │   ├── toast.tsx
│   │   ├── tabs.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── popover.tsx
│   │   ├── sheet.tsx           # Side panel (SLDS Panel)
│   │   ├── progress.tsx
│   │   └── skeleton.tsx
│   ├── layout/
│   │   ├── AppShell.tsx        # Main layout wrapper
│   │   ├── GlobalHeader.tsx    # Salesforce-style top nav
│   │   ├── SideNav.tsx         # Left nav (SLDS Navigation)
│   │   ├── PageHeader.tsx      # SLDS Page Header pattern
│   │   └── Breadcrumb.tsx
│   ├── shared/
│   │   ├── DataTable.tsx       # TanStack Table wrapper
│   │   ├── StatCard.tsx        # KPI metric card
│   │   ├── StatusBadge.tsx     # SLDS pill/badge
│   │   ├── EmptyState.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── ConfirmDialog.tsx
│   │   ├── CSVImportModal.tsx
│   │   └── AIAssistantPanel.tsx # Sliding AI panel
│   └── charts/
│       ├── FunnelChart.tsx
│       ├── TimeSeriesChart.tsx
│       └── ChannelPieChart.tsx
├── pages/
│   ├── Dashboard/
│   │   ├── index.tsx
│   │   ├── components/
│   │   │   ├── MetricsBar.tsx
│   │   │   ├── RecentCampaigns.tsx
│   │   │   ├── EngagementChart.tsx
│   │   │   └── AIInsightCard.tsx
│   ├── Customers/
│   │   ├── index.tsx           # Customer list with filters
│   │   ├── CustomerDetail.tsx  # Single customer view
│   │   └── components/
│   │       ├── CustomerTable.tsx
│   │       ├── CustomerFilters.tsx
│   │       └── ImportCustomersModal.tsx
│   ├── Orders/
│   │   ├── index.tsx
│   │   └── components/
│   │       └── OrderTable.tsx
│   ├── Segments/
│   │   ├── index.tsx           # Segment list
│   │   ├── SegmentBuilder.tsx  # AI-powered segment builder
│   │   ├── SegmentDetail.tsx
│   │   └── components/
│   │       ├── RuleBuilder.tsx   # Visual rule editor
│   │       ├── AISegmentInput.tsx # NL → rules
│   │       ├── AudiencePreview.tsx
│   │       └── SegmentCard.tsx
│   ├── Campaigns/
│   │   ├── index.tsx           # Campaign list
│   │   ├── CampaignCreate.tsx  # Multi-step wizard
│   │   ├── CampaignDetail.tsx  # Analytics + live feed
│   │   └── components/
│   │       ├── CampaignWizard/
│   │       │   ├── Step1_Audience.tsx
│   │       │   ├── Step2_Message.tsx
│   │       │   ├── Step3_Channel.tsx
│   │       │   └── Step4_Review.tsx
│   │       ├── MessageEditor.tsx    # Rich text + AI draft
│   │       ├── CampaignStatusPill.tsx
│   │       ├── AnalyticsFunnel.tsx
│   │       ├── CommunicationsTable.tsx
│   │       └── LiveFeedDrawer.tsx   # Real-time event feed
│   ├── AIAssistant/
│   │   ├── index.tsx           # Full chat interface
│   │   └── components/
│   │       ├── ChatInterface.tsx
│   │       ├── MessageBubble.tsx
│   │       └── ToolResultCard.tsx  # Structured AI outputs
│   └── Auth/
│       ├── Login.tsx
│       └── Register.tsx
├── stores/
│   ├── authStore.ts
│   ├── uiStore.ts              # Sidebar state, modals
│   └── campaignStore.ts        # Active campaign wizard state
├── hooks/
│   ├── useAuth.ts
│   ├── useCampaignPolling.ts   # Polling campaign analytics
│   ├── useAIAgent.ts           # Streaming AI responses
│   └── useCSVImport.ts
├── lib/
│   ├── api.ts                  # Axios instance + interceptors
│   ├── queryClient.ts          # TanStack Query config
│   ├── utils.ts                # Shadcn utils + helpers
│   └── constants.ts
├── types/
│   ├── customer.ts
│   ├── order.ts
│   ├── segment.ts
│   ├── campaign.ts
│   └── agent.ts
└── styles/
    ├── globals.css
    └── salesforce-theme.css
```

---

### 5.3 Page Specifications

#### PAGE: Dashboard (`/`)
**Purpose:** Command center — top-level KPIs, recent activity, AI insight card.

**Components rendered:**
- `GlobalHeader` with brand logo, notification bell, user avatar
- `MetricsBar` — 4 stat cards:
  - Total Customers (with % growth vs last month)
  - Active Campaigns
  - Messages Sent (rolling 30d)
  - Average Open Rate (rolling 30d)
- `EngagementChart` — Recharts AreaChart, 30-day time series of sent/delivered/opened/clicked
- `RecentCampaigns` — last 5 campaigns with status pill and quick action buttons
- `AIInsightCard` — AI-generated summary: "Your best performing segment last week was Premium Buyers (38% open rate). Consider sending to Lapsed-90d segment — they haven't been reached in 3 months."

**Data fetching:**
```typescript
// TanStack Query keys
['dashboard', 'metrics']        → GET /api/analytics/overview
['dashboard', 'engagement']     → GET /api/analytics/engagement?days=30
['campaigns', 'recent']         → GET /api/campaigns?limit=5&sort=createdAt:desc
['dashboard', 'ai-insight']     → GET /api/agents/insights/dashboard
```

**Salesforce UI Pattern:** Uses SLDS "Lightning Home Page" layout — full-width header band, 2-column below (content + sidebar).

---

#### PAGE: Customers (`/customers`)
**Purpose:** Browse, filter, search, import all shoppers.

**Layout:** SLDS List View pattern — header with "New Customer" + "Import CSV" buttons, filter bar, paginated DataTable.

**Columns:**
- Name (with avatar initials), Email, Phone, Total Orders, Total Spent (LTV), Last Order Date, Tags, Actions

**Features:**
- Global search (debounced, 300ms, hits `/api/customers?search=`)
- Filter sidebar: by LTV range, order count range, last order date range, tags, channel preference
- Row click → Customer Detail side sheet (SLDS Panel pattern)
- Bulk select → bulk tag / bulk export
- Import CSV button → `CSVImportModal` (maps columns, preview 5 rows, confirm import)
- Pagination (server-side, 50 per page)

**Customer Detail Panel (Sheet):**
- Profile header (name, email, phone, avatar, tags)
- Order history mini-table (last 10 orders)
- Engagement history (last 5 communications + status)
- Segment membership list
- "Add to Segment" quick action

---

#### PAGE: Segments (`/segments`)
**Purpose:** Create and manage shopper audiences.

**Layout:** SLDS Card grid of segment cards + "New Segment" button.

**SegmentCard shows:**
- Segment name, description, audience count (with last-evaluated timestamp)
- Rule summary in plain English ("Bought ≥ 2 times in last 90 days, spent ≥ ₹5000")
- Last campaign that used it
- Quick actions: Edit, Evaluate, Create Campaign

**Segment Builder page (`/segments/new` and `/segments/:id/edit`):**
This is the most AI-native page.

Layout: Split view — left is the rule builder / AI input, right is live audience preview.

**AI Input Panel (`AISegmentInput`):**
```
┌──────────────────────────────────────────────────┐
│ 🤖 Describe your audience in plain English       │
│ ┌────────────────────────────────────────────┐   │
│ │ "Customers who bought coffee at least 3    │   │
│ │  times in the past 60 days but haven't     │   │
│ │  ordered in the last 2 weeks"              │   │
│ └────────────────────────────────────────────┘   │
│              [Generate Rules →]                  │
└──────────────────────────────────────────────────┘
```
→ POST `/api/agents/segments/build` → LangGraph SegmentBuilderAgent
→ Returns structured `SegmentRuleSet` JSON
→ Rules populate the visual `RuleBuilder` component
→ Marketer can edit/override each rule

**Visual Rule Builder (`RuleBuilder`):**
- AND/OR rule groups
- Each rule: `[field] [operator] [value]`
- Fields: `total_orders`, `total_spent`, `last_order_date`, `first_order_date`, `days_since_last_order`, `average_order_value`, `tags`, `preferred_channel`, `city`, `product_category_bought`
- Operators: `equals`, `not_equals`, `greater_than`, `less_than`, `between`, `in`, `not_in`, `contains`, `after`, `before`, `within_last_n_days`
- Live count: debounced POST to `/api/segments/evaluate` shows audience size as rules change

**Audience Preview (`AudiencePreview`):**
- Shows count: "**1,247** customers match this segment"
- Sample table: 5 random matching customers
- LTV distribution mini chart

---

#### PAGE: Campaigns (`/campaigns`)
**Purpose:** Create, launch, and monitor campaigns.

**Campaign List:** Table with columns: Name, Segment, Channel, Status, Audience Size, Sent, Delivered, Opened, Clicked, Revenue Attributed, Created At, Actions.

**Status pills:** `DRAFT` (grey), `SCHEDULED` (blue), `SENDING` (orange animated), `SENT` (green), `FAILED` (red)

**Campaign Create Wizard (`/campaigns/new`):**
Multi-step SLDS wizard with progress indicator.

**Step 1 — Audience:**
- Dropdown to select existing segment OR create segment inline
- Shows audience size + preview
- AI suggestion: "Based on your last 3 campaigns, 'Loyal Buyers' has 42% open rate — try them next"

**Step 2 — Message:**
- Channel selector (WhatsApp / SMS / Email / RCS) — with icons
- Message editor (textarea for SMS/WhatsApp, rich HTML editor for Email)
- **AI Draft button** → POST `/api/agents/messages/draft` with segment + channel → returns 3 message variants
- Variants shown as clickable cards; user picks one or edits
- Variable interpolation: `{{first_name}}`, `{{last_order_date}}`, `{{product_name}}` with live preview

**Step 3 — Schedule:**
- Send Now vs Schedule (datetime picker)
- Estimated send time based on audience size

**Step 4 — Review & Launch:**
- Summary of all choices
- Estimated reach, estimated cost (notional)
- "Launch Campaign" → POST `/api/campaigns/:id/launch`

**Campaign Detail (`/campaigns/:id`):**
The analytics command center.

Tabs: Overview | Communications | Live Feed | AI Report

**Overview tab:**
- `AnalyticsFunnel` component: Recharts FunnelChart — Sent → Delivered → Opened → Clicked → Converted
  - Numbers and percentages at each stage
- `TimeSeriesChart` — hourly engagement over campaign lifecycle
- Channel breakdown pie chart
- Key metrics: Delivery Rate, Open Rate, Click Rate, Revenue Attributed

**Communications tab:**
- Full table of all individual communications
- Columns: Recipient Name, Phone/Email, Channel, Status, Sent At, Delivered At, Opened At, Clicked At
- Filter by status; export CSV

**Live Feed tab:**
- Real-time feed of webhook events as they come in
- "✅ Delivered to Priya S. (WhatsApp) — just now"
- "👆 Clicked by Rahul M. (Email) — 2s ago"
- Auto-scrolling; pause button; 200-event buffer

**AI Report tab:**
- AI-generated paragraph insights: "This campaign achieved a 34% open rate, outperforming your brand average by 11%. The WhatsApp channel drove 2.3x more clicks than Email for this audience. Customers who clicked within the first hour had a 68% conversion rate."
- Recommendations: "Consider a follow-up message to the 456 customers who opened but didn't click."

---

#### PAGE: AI Assistant (`/ai-assistant`)
**Purpose:** Full conversational interface to the CRM — query data, create segments, launch campaigns in natural language.

```
┌──────────────────────────────────────────────────────┐
│  🤖 Xeno AI Assistant                                │
│  ─────────────────────────────────────────────────  │
│                                                      │
│  [AI]: Hi! I can help you understand your shoppers,  │
│  build segments, draft messages, and run campaigns.  │
│  What would you like to do today?                    │
│                                                      │
│  [User]: How many customers haven't ordered in the   │
│  past 30 days?                                       │
│                                                      │
│  [AI]: 📊 1,847 customers haven't ordered in the    │
│  last 30 days. That's 23% of your total base.       │
│  ┌──────────────────────────────────────────┐       │
│  │ [Create a re-engagement segment →]       │       │
│  └──────────────────────────────────────────┘       │
│                                                      │
└──────────────────────────────────────────────────────┘
│ Type a message...                      [Send ↵]     │
└──────────────────────────────────────────────────────┘
```

**Capabilities shown in UI as suggestion chips:**
- "Show me top customers by LTV"
- "Build a segment of lapsed buyers"
- "Draft a WhatsApp message for loyal customers"
- "What's my best-performing campaign?"
- "How many customers are in the Premium Buyers segment?"

**Backend:** POST `/api/agents/chat` → NLQueryAgent (LangGraph) → streams SSE response

---

### 5.4 Global Layout Components

#### `GlobalHeader.tsx` — Salesforce Top Navigation Bar
```tsx
// SLDS Global Header pattern
// Height: 52px, Background: var(--sf-brand-primary)
// Left: App switcher icon + "Xeno CRM" wordmark
// Center: Global search (500ms debounce, searches customers + campaigns)
// Right: Help icon, Notification bell (with unread badge), User avatar dropdown

interface GlobalHeaderProps {
  onSearchChange: (query: string) => void
}
```
Visual: Full-width blue bar (#0176d3), white text and icons, Salesforce Sans font.

#### `SideNav.tsx` — Salesforce Lightning Navigation
```tsx
// SLDS Vertical Navigation pattern
// Width: 240px (collapsible to 52px on mobile)
// Top: Brand logo area
// Nav items with icons (Lucide icons):
//   ● Dashboard        (LayoutDashboard)
//   ● Customers        (Users)
//   ● Orders           (ShoppingCart)
//   ● Segments         (Filter)
//   ● Campaigns        (Megaphone)
//   ● AI Assistant     (Bot) — highlighted with gradient badge "AI"
// Bottom: Settings (Settings icon), Account
// Active state: left blue border + blue text + light blue bg
```

#### `PageHeader.tsx` — SLDS Record Page Header
```tsx
// Top of every content page
// Pattern: breadcrumb above, title + subtitle row, action buttons right
interface PageHeaderProps {
  title: string
  subtitle?: string
  breadcrumbs: { label: string; href?: string }[]
  actions?: ReactNode
  badge?: { label: string; variant: 'success' | 'warning' | 'error' | 'info' }
}
```

#### `AIAssistantPanel.tsx` — Floating AI Panel
A slide-over Sheet (right side, 400px wide) accessible from any page via a fixed floating button (bottom-right, blue circle with Bot icon). Context-aware: on the Segment Builder page it suggests segment ideas; on Campaign Detail it suggests follow-up actions.

---

### 5.5 State Management

#### Zustand Stores

**`authStore.ts`**
```typescript
interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  login: (credentials: LoginDto) => Promise<void>
  logout: () => void
  refreshTokens: () => Promise<void>
}
```

**`uiStore.ts`**
```typescript
interface UIState {
  sideNavCollapsed: boolean
  aiPanelOpen: boolean
  activeModal: string | null
  toasts: Toast[]
  toggleSideNav: () => void
  openAIPanel: () => void
  closeAIPanel: () => void
  showToast: (toast: Omit<Toast, 'id'>) => void
}
```

**`campaignStore.ts`** (wizard state)
```typescript
interface CampaignWizardState {
  step: 1 | 2 | 3 | 4
  segmentId: string | null
  messageContent: string
  messageVariants: MessageVariant[]
  channel: Channel
  scheduledAt: Date | null
  setStep: (step: number) => void
  setSegment: (id: string) => void
  setMessage: (content: string) => void
  setChannel: (channel: Channel) => void
  reset: () => void
}
```

#### TanStack Query Configuration
```typescript
// lib/queryClient.ts
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2,      // 2 minutes
      gcTime: 1000 * 60 * 10,         // 10 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

// Cache invalidation strategy:
// - On campaign launch: invalidate ['campaigns', id], ['analytics', ...]
// - On customer import: invalidate ['customers', ...]
// - On segment save: invalidate ['segments', ...]
```

---

## 6. MAIN BACKEND — Express.js + Prisma + PostgreSQL

### 6.1 Project Structure

```
packages/backend/
├── src/
│   ├── index.ts                  # Entry point
│   ├── app.ts                    # Express app factory
│   ├── config/
│   │   ├── env.ts                # Zod-validated env vars
│   │   ├── redis.ts              # Redis client init
│   │   └── prisma.ts             # Prisma client singleton
│   ├── middleware/
│   │   ├── auth.ts               # JWT verification middleware
│   │   ├── rateLimit.ts          # Redis-backed rate limiter
│   │   ├── errorHandler.ts       # Global error handler
│   │   ├── requestLogger.ts      # Morgan + structured logs
│   │   └── validateRequest.ts    # Zod request validation
│   ├── routes/
│   │   ├── auth.routes.ts
│   │   ├── customer.routes.ts
│   │   ├── order.routes.ts
│   │   ├── segment.routes.ts
│   │   ├── campaign.routes.ts
│   │   ├── communication.routes.ts
│   │   ├── analytics.routes.ts
│   │   ├── webhook.routes.ts      # Channel service callbacks
│   │   └── agent.routes.ts        # Proxy to Python agent service
│   ├── controllers/
│   │   ├── auth.controller.ts
│   │   ├── customer.controller.ts
│   │   ├── order.controller.ts
│   │   ├── segment.controller.ts
│   │   ├── campaign.controller.ts
│   │   ├── communication.controller.ts
│   │   ├── analytics.controller.ts
│   │   ├── webhook.controller.ts
│   │   └── agent.controller.ts
│   ├── services/
│   │   ├── auth.service.ts
│   │   ├── customer.service.ts
│   │   ├── order.service.ts
│   │   ├── segment.service.ts
│   │   ├── campaign.service.ts
│   │   ├── communication.service.ts
│   │   ├── analytics.service.ts
│   │   ├── channelClient.service.ts  # HTTP calls to Channel Service
│   │   └── agentClient.service.ts    # HTTP calls to Agent Service
│   ├── jobs/
│   │   ├── queue.ts              # BullMQ queue definitions
│   │   ├── workers/
│   │   │   ├── campaignSend.worker.ts    # Picks up send jobs
│   │   │   └── analyticsRefresh.worker.ts
│   │   └── schedulers/
│   │       └── campaignScheduler.ts     # Cron for scheduled campaigns
│   ├── cache/
│   │   ├── keys.ts               # All Redis key templates
│   │   └── helpers.ts            # getOrSet, invalidate helpers
│   ├── validators/
│   │   ├── customer.schema.ts
│   │   ├── segment.schema.ts
│   │   ├── campaign.schema.ts
│   │   └── webhook.schema.ts
│   └── types/
│       └── express.d.ts          # Augment req.user
├── prisma/
│   ├── schema.prisma
│   ├── migrations/
│   └── seed.ts
├── package.json
└── tsconfig.json
```

### 6.2 Express App Bootstrap

#### `src/app.ts`
```typescript
import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import compression from 'compression'
import morgan from 'morgan'
import { authRouter } from './routes/auth.routes'
import { customerRouter } from './routes/customer.routes'
import { orderRouter } from './routes/order.routes'
import { segmentRouter } from './routes/segment.routes'
import { campaignRouter } from './routes/campaign.routes'
import { analyticsRouter } from './routes/analytics.routes'
import { webhookRouter } from './routes/webhook.routes'
import { agentRouter } from './routes/agent.routes'
import { errorHandler } from './middleware/errorHandler'
import { requestLogger } from './middleware/requestLogger'

export function createApp() {
  const app = express()

  // Security middleware
  app.use(helmet())
  app.use(cors({
    origin: process.env.FRONTEND_URL,
    credentials: true
  }))
  app.use(compression())
  app.use(express.json({ limit: '10mb' }))  // For CSV upload as base64
  app.use(express.urlencoded({ extended: true }))

  // Logging
  app.use(morgan('combined'))
  app.use(requestLogger)

  // Health check
  app.get('/health', (req, res) => res.json({ status: 'ok', ts: Date.now() }))

  // API Routes
  app.use('/api/auth', authRouter)
  app.use('/api/customers', customerRouter)
  app.use('/api/orders', orderRouter)
  app.use('/api/segments', segmentRouter)
  app.use('/api/campaigns', campaignRouter)
  app.use('/api/analytics', analyticsRouter)
  app.use('/api/webhooks', webhookRouter)      // No auth — called by channel service
  app.use('/api/agents', agentRouter)           // Proxy to Python service

  // Global error handler
  app.use(errorHandler)

  return app
}
```

---

### 6.3 Route Definitions

#### Auth Routes (`/api/auth`)
```
POST   /api/auth/register          Register brand account
POST   /api/auth/login             Login → returns JWT + refresh token
POST   /api/auth/refresh           Refresh JWT using refresh token
POST   /api/auth/logout            Invalidate refresh token (store in Redis blocklist)
GET    /api/auth/me                Get current user profile (auth required)
```

#### Customer Routes (`/api/customers`) — All require auth
```
GET    /api/customers              List customers (paginated, filterable, searchable)
POST   /api/customers              Create single customer
GET    /api/customers/:id          Get customer + order history + segment membership
PUT    /api/customers/:id          Update customer
DELETE /api/customers/:id          Soft delete customer
POST   /api/customers/import       Bulk CSV import (up to 10,000 rows)
GET    /api/customers/:id/orders   Get customer's order history
GET    /api/customers/:id/communications  Get customer's communication history
POST   /api/customers/export       Export filtered customers as CSV
```

**Query params for GET /api/customers:**
```
?search=          Full text search (name, email, phone)
?page=1           Page number (default 1)
?limit=50         Page size (default 50, max 200)
?sort=ltv:desc    Sort field:direction
?minLtv=          Minimum lifetime value
?maxLtv=          Maximum lifetime value
?minOrders=       Minimum order count
?maxOrders=       Maximum order count
?lastOrderAfter=  ISO date string
?lastOrderBefore= ISO date string
?tags=tag1,tag2   Comma-separated tags (OR logic)
?city=            Filter by city
```

#### Order Routes (`/api/orders`) — All require auth
```
GET    /api/orders                 List orders (paginated, filterable)
POST   /api/orders                 Create single order
GET    /api/orders/:id             Get order + line items
PUT    /api/orders/:id             Update order
DELETE /api/orders/:id             Delete order
POST   /api/orders/import          Bulk order CSV import
```

#### Segment Routes (`/api/segments`) — All require auth
```
GET    /api/segments               List all segments with stats
POST   /api/segments               Create segment (with rules)
GET    /api/segments/:id           Get segment + rules
PUT    /api/segments/:id           Update segment rules
DELETE /api/segments/:id           Delete segment
POST   /api/segments/evaluate      Preview audience count for rule set (no save)
POST   /api/segments/:id/evaluate  Re-evaluate segment, update audience count
GET    /api/segments/:id/customers Paginated customers in segment
```

#### Campaign Routes (`/api/campaigns`) — All require auth
```
GET    /api/campaigns              List campaigns (paginated)
POST   /api/campaigns              Create campaign (status: DRAFT)
GET    /api/campaigns/:id          Get campaign + stats
PUT    /api/campaigns/:id          Update campaign (only if DRAFT)
DELETE /api/campaigns/:id          Delete campaign (only if DRAFT)
POST   /api/campaigns/:id/launch   Launch campaign → creates Communications → sends
POST   /api/campaigns/:id/schedule Schedule campaign for later
POST   /api/campaigns/:id/cancel   Cancel scheduled/sending campaign
GET    /api/campaigns/:id/analytics Detailed analytics (cached in Redis)
GET    /api/campaigns/:id/communications Paginated list of individual communications
GET    /api/campaigns/:id/events   SSE stream of real-time communication events
```

#### Analytics Routes (`/api/analytics`) — All require auth
```
GET    /api/analytics/overview     Dashboard KPIs (cached 5min)
GET    /api/analytics/engagement   Time series engagement data
GET    /api/analytics/channels     Channel performance breakdown
GET    /api/analytics/segments     Segment performance comparison
GET    /api/analytics/customers    Customer growth over time
```

#### Webhook Routes (`/api/webhooks`) — No auth, HMAC signature verification
```
POST   /api/webhooks/channel/:communicationId   Channel service event callback
```

#### Agent Proxy Routes (`/api/agents`) — All require auth
```
POST   /api/agents/segments/build      NL → segment rules (stream)
POST   /api/agents/messages/draft      Segment context → message variants
POST   /api/agents/insights/campaign   Campaign data → insight paragraph
GET    /api/agents/insights/dashboard  Dashboard AI insight card
POST   /api/agents/chat                NL query chat (SSE stream)
```

---

### 6.4 Key Service Logic

#### Campaign Launch Service (`campaign.service.ts`)
```typescript
async function launchCampaign(campaignId: string, brandId: string): Promise<void> {
  // 1. Lock campaign in Redis to prevent double-launch
  const lockKey = `lock:campaign:${campaignId}`
  const locked = await redis.set(lockKey, '1', 'EX', 300, 'NX')
  if (!locked) throw new Error('Campaign is already being launched')

  // 2. Get campaign + segment
  const campaign = await prisma.campaign.findUniqueOrThrow({
    where: { id: campaignId, brandId },
    include: { segment: { include: { rules: true } } }
  })

  if (campaign.status !== 'DRAFT' && campaign.status !== 'SCHEDULED') {
    throw new Error('Campaign cannot be launched in current state')
  }

  // 3. Evaluate segment to get current customer IDs
  const customerIds = await segmentService.evaluateSegment(campaign.segment)

  // 4. Create Communication records in bulk
  await prisma.communication.createMany({
    data: customerIds.map(customerId => ({
      campaignId,
      customerId,
      brandId,
      channel: campaign.channel,
      status: 'QUEUED',
      messageContent: campaign.messageTemplate,
    }))
  })

  // 5. Update campaign status
  await prisma.campaign.update({
    where: { id: campaignId },
    data: {
      status: 'SENDING',
      audienceSize: customerIds.length,
      launchedAt: new Date()
    }
  })

  // 6. Invalidate analytics cache
  await redis.del(`cache:campaign:${campaignId}:analytics`)

  // 7. Enqueue send job in BullMQ
  await campaignSendQueue.add('send-campaign', {
    campaignId,
    brandId
  }, {
    attempts: 3,
    backoff: { type: 'exponential', delay: 2000 },
    removeOnComplete: 100,
    removeOnFail: 50
  })

  // 8. Release lock
  await redis.del(lockKey)
}
```

#### Campaign Send Worker (`jobs/workers/campaignSend.worker.ts`)
```typescript
// BullMQ worker — picks up 'send-campaign' jobs
// Batches communications in chunks of 100 for the channel service
const worker = new Worker('campaign-send', async (job) => {
  const { campaignId, brandId } = job.data

  // Get all QUEUED communications for this campaign
  const communications = await prisma.communication.findMany({
    where: { campaignId, status: 'QUEUED' },
    include: { customer: true, campaign: true }
  })

  // Process in batches of 100
  const BATCH_SIZE = 100
  for (let i = 0; i < communications.length; i += BATCH_SIZE) {
    const batch = communications.slice(i, i + BATCH_SIZE)

    // Build personalised messages (replace template vars)
    const sendRequests = batch.map(comm => ({
      communicationId: comm.id,
      recipient: {
        name: comm.customer.name,
        phone: comm.customer.phone,
        email: comm.customer.email,
      },
      channel: comm.channel,
      message: personaliseMessage(comm.campaign.messageTemplate, comm.customer),
    }))

    // Call channel service
    await channelClientService.sendBatch(sendRequests)

    // Mark as SENT
    await prisma.communication.updateMany({
      where: { id: { in: batch.map(c => c.id) } },
      data: { status: 'SENT', sentAt: new Date() }
    })

    await job.updateProgress(Math.round((i + batch.length) / communications.length * 100))
  }

  // Update campaign analytics (refresh cache)
  await analyticsService.refreshCampaignAnalytics(campaignId)
}, {
  connection: redis,
  concurrency: 5
})
```

#### Segment Evaluation Service (`segment.service.ts`)
```typescript
// Dynamically builds Prisma WHERE clause from segment rules
async function evaluateSegment(segment: SegmentWithRules): Promise<string[]> {
  const where = buildPrismaWhereFromRules(segment.ruleSet, segment.brandId)

  const customers = await prisma.customer.findMany({
    where,
    select: { id: true }
  })

  return customers.map(c => c.id)
}

function buildPrismaWhereFromRules(ruleSet: RuleSet, brandId: string): Prisma.CustomerWhereInput {
  const operator = ruleSet.operator  // 'AND' | 'OR'
  const conditions = ruleSet.rules.map(rule => {
    switch (rule.field) {
      case 'total_orders':
        return buildOrderCountCondition(rule, brandId)
      case 'total_spent':
        return buildSpentCondition(rule, brandId)
      case 'days_since_last_order':
        return buildDaysSinceLastOrderCondition(rule, brandId)
      case 'average_order_value':
        return buildAOVCondition(rule, brandId)
      case 'tags':
        return { tags: { hasSome: rule.value as string[] } }
      case 'city':
        return { city: { equals: rule.value, mode: 'insensitive' } }
      default:
        throw new Error(`Unknown rule field: ${rule.field}`)
    }
  })

  return operator === 'AND' ? { AND: conditions } : { OR: conditions }
}

// Example: days_since_last_order > 30
function buildDaysSinceLastOrderCondition(rule: Rule, brandId: string): Prisma.CustomerWhereInput {
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - Number(rule.value))

  if (rule.operator === 'greater_than') {
    return { lastOrderDate: { lt: cutoff } }
  }
  if (rule.operator === 'less_than') {
    return { lastOrderDate: { gt: cutoff } }
  }
  // etc.
}
```

#### Webhook Controller (`webhook.controller.ts`)
```typescript
// Called by Channel Service to report delivery events
// No auth — verified by HMAC signature
async function handleChannelCallback(req: Request, res: Response) {
  // 1. Verify HMAC signature
  const signature = req.headers['x-channel-signature'] as string
  if (!verifyHMAC(req.body, signature, process.env.CHANNEL_WEBHOOK_SECRET)) {
    return res.status(401).json({ error: 'Invalid signature' })
  }

  // Respond immediately to prevent channel service timeout
  res.status(202).json({ received: true })

  // 2. Async processing — enqueue in BullMQ
  await webhookProcessingQueue.add('process-event', req.body, {
    attempts: 5,
    backoff: { type: 'exponential', delay: 1000 }
  })
}

// Worker processes webhook events
const webhookWorker = new Worker('webhook-processing', async (job) => {
  const event: ChannelEvent = job.data

  // Map event type to status
  const STATUS_MAP: Record<string, CommunicationStatus> = {
    'delivered': 'DELIVERED',
    'failed': 'FAILED',
    'opened': 'OPENED',
    'read': 'READ',
    'clicked': 'CLICKED',
    'converted': 'CONVERTED',
  }

  const newStatus = STATUS_MAP[event.eventType]
  if (!newStatus) return

  // Update communication (only if new status is "later" in the funnel)
  const comm = await prisma.communication.findUnique({
    where: { id: event.communicationId }
  })

  if (!comm || isEarlierStatus(newStatus, comm.status)) return

  // Build update payload
  const updateData: Partial<Communication> = { status: newStatus }
  if (newStatus === 'DELIVERED') updateData.deliveredAt = new Date(event.timestamp)
  if (newStatus === 'OPENED') updateData.openedAt = new Date(event.timestamp)
  if (newStatus === 'READ') updateData.readAt = new Date(event.timestamp)
  if (newStatus === 'CLICKED') updateData.clickedAt = new Date(event.timestamp)

  await prisma.communication.update({
    where: { id: event.communicationId },
    data: updateData
  })

  // Invalidate campaign analytics cache
  await redis.del(`cache:campaign:${comm.campaignId}:analytics`)
  await redis.del(`cache:analytics:overview:${comm.brandId}`)

  // Publish to SSE stream for Live Feed
  await redis.publish(
    `campaign:${comm.campaignId}:events`,
    JSON.stringify({ type: event.eventType, communicationId: comm.id, timestamp: event.timestamp })
  )
})
```

#### SSE Live Feed (`campaign.routes.ts`)
```typescript
// GET /api/campaigns/:id/events — Server-Sent Events
router.get('/:id/events', auth, async (req, res) => {
  const campaignId = req.params.id

  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
  res.flushHeaders()

  // Subscribe to Redis pub/sub channel
  const subscriber = redis.duplicate()
  await subscriber.subscribe(`campaign:${campaignId}:events`)

  subscriber.on('message', (channel, message) => {
    res.write(`data: ${message}\n\n`)
  })

  // Heartbeat every 30s
  const heartbeat = setInterval(() => {
    res.write(': heartbeat\n\n')
  }, 30000)

  req.on('close', () => {
    clearInterval(heartbeat)
    subscriber.unsubscribe()
    subscriber.disconnect()
  })
})
```

---

### 6.5 Analytics Service with Redis Caching

```typescript
// analytics.service.ts
async function getCampaignAnalytics(campaignId: string): Promise<CampaignAnalytics> {
  const cacheKey = `cache:campaign:${campaignId}:analytics`

  // Try Redis cache first (TTL: 60s during active send, 5min after)
  const cached = await redis.get(cacheKey)
  if (cached) return JSON.parse(cached)

  // Compute from DB
  const stats = await prisma.communication.groupBy({
    by: ['status'],
    where: { campaignId },
    _count: { _all: true }
  })

  const analytics = {
    total: stats.reduce((sum, s) => sum + s._count._all, 0),
    queued: stats.find(s => s.status === 'QUEUED')?._count._all ?? 0,
    sent: stats.find(s => s.status === 'SENT')?._count._all ?? 0,
    delivered: stats.find(s => s.status === 'DELIVERED')?._count._all ?? 0,
    failed: stats.find(s => s.status === 'FAILED')?._count._all ?? 0,
    opened: stats.find(s => s.status === 'OPENED')?._count._all ?? 0,
    read: stats.find(s => s.status === 'READ')?._count._all ?? 0,
    clicked: stats.find(s => s.status === 'CLICKED')?._count._all ?? 0,
    converted: stats.find(s => s.status === 'CONVERTED')?._count._all ?? 0,
    deliveryRate: 0,
    openRate: 0,
    clickRate: 0,
    computedAt: new Date().toISOString()
  }

  // Compute rates
  if (analytics.sent > 0) {
    analytics.deliveryRate = analytics.delivered / analytics.sent
    analytics.openRate = analytics.opened / analytics.delivered || 0
    analytics.clickRate = analytics.clicked / analytics.opened || 0
  }

  // Cache: 60s if campaign is still SENDING, 5min if SENT
  const campaign = await prisma.campaign.findUnique({ where: { id: campaignId } })
  const ttl = campaign?.status === 'SENDING' ? 60 : 300
  await redis.setex(cacheKey, ttl, JSON.stringify(analytics))

  return analytics
}
```

---

## 7. AGENT BACKEND — FastAPI + LangGraph

### 7.1 Project Structure

```
packages/agent-service/
├── src/
│   ├── main.py                  # FastAPI app entry
│   ├── config.py                # Settings (Pydantic BaseSettings)
│   ├── dependencies.py          # FastAPI DI (redis, db clients)
│   ├── routers/
│   │   ├── segments.py          # Segment builder agent routes
│   │   ├── messages.py          # Message drafter agent routes
│   │   ├── insights.py          # Insight generation routes
│   │   └── chat.py              # Conversational NL query routes
│   ├── agents/
│   │   ├── base.py              # Shared agent utilities
│   │   ├── segment_builder/
│   │   │   ├── agent.py         # LangGraph StateGraph definition
│   │   │   ├── nodes.py         # Individual graph nodes
│   │   │   ├── state.py         # TypedDict state schema
│   │   │   └── tools.py         # Tools available to agent
│   │   ├── message_crafter/
│   │   │   ├── agent.py
│   │   │   ├── nodes.py
│   │   │   └── state.py
│   │   ├── campaign_orchestrator/
│   │   │   ├── agent.py
│   │   │   ├── nodes.py
│   │   │   └── state.py
│   │   ├── insight_summary/
│   │   │   ├── agent.py
│   │   │   └── state.py
│   │   └── nl_query/
│   │       ├── agent.py
│   │       ├── nodes.py
│   │       └── tools.py
│   ├── cache/
│   │   ├── redis_client.py
│   │   └── agent_cache.py       # Cache agent outputs
│   └── schemas/
│       ├── segment.py
│       ├── message.py
│       └── chat.py
├── requirements.txt
└── Dockerfile
```

---

### 7.2 FastAPI Main Application

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from .routers import segments, messages, insights, chat
from .cache.redis_client import init_redis, close_redis
from .config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()

app = FastAPI(
    title="Xeno CRM Agent Service",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.BACKEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(segments.router, prefix="/agents/segments", tags=["Segments"])
app.include_router(messages.router, prefix="/agents/messages", tags=["Messages"])
app.include_router(insights.router, prefix="/agents/insights", tags=["Insights"])
app.include_router(chat.router, prefix="/agents/chat", tags=["Chat"])

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

### 7.3 LangGraph Agent Definitions

#### AGENT 1: SegmentBuilderAgent

**Purpose:** Takes a natural language description of a target audience and returns a structured rule set that the CRM segment builder understands.

**State:**
```python
# agents/segment_builder/state.py
from typing import TypedDict, Optional, Annotated
from operator import add

class SegmentBuilderState(TypedDict):
    # Input
    user_description: str
    brand_context: dict          # Available fields, sample data
    existing_segments: list[str] # Names, for dedup

    # Working
    clarification_needed: bool
    clarification_questions: list[str]
    extracted_intent: Optional[str]
    candidate_rules: Optional[dict]

    # Output
    rule_set: Optional[dict]     # Final structured rules
    explanation: str             # Human-readable explanation
    confidence: float            # 0.0-1.0
    messages: Annotated[list, add]  # LangGraph message history
```

**Graph:**
```python
# agents/segment_builder/agent.py
from langgraph.graph import StateGraph, END
from .nodes import (
    parse_intent_node,
    clarify_if_needed_node,
    build_rules_node,
    validate_rules_node,
    explain_rules_node
)
from .state import SegmentBuilderState

def build_segment_agent():
    graph = StateGraph(SegmentBuilderState)

    # Add nodes
    graph.add_node("parse_intent", parse_intent_node)
    graph.add_node("clarify", clarify_if_needed_node)
    graph.add_node("build_rules", build_rules_node)
    graph.add_node("validate_rules", validate_rules_node)
    graph.add_node("explain_rules", explain_rules_node)

    # Entry
    graph.set_entry_point("parse_intent")

    # Conditional: if clarification needed, ask; else proceed
    graph.add_conditional_edges(
        "parse_intent",
        lambda state: "clarify" if state["clarification_needed"] else "build_rules",
        {
            "clarify": "clarify",
            "build_rules": "build_rules"
        }
    )

    graph.add_edge("clarify", END)          # Return questions to user
    graph.add_edge("build_rules", "validate_rules")

    # Conditional: if rules are valid, explain; else rebuild
    graph.add_conditional_edges(
        "validate_rules",
        lambda state: "explain_rules" if state["candidate_rules"] else "build_rules",
        {
            "explain_rules": "explain_rules",
            "build_rules": "build_rules"
        }
    )

    graph.add_edge("explain_rules", END)

    return graph.compile()
```

**Nodes:**
```python
# agents/segment_builder/nodes.py
from anthropic import Anthropic
from .state import SegmentBuilderState

client = Anthropic()

SEGMENT_FIELDS = [
    "total_orders", "total_spent", "last_order_date",
    "first_order_date", "days_since_last_order",
    "average_order_value", "tags", "preferred_channel",
    "city", "product_category_bought"
]

OPERATORS = [
    "equals", "not_equals", "greater_than", "less_than",
    "between", "in", "not_in", "contains", "within_last_n_days",
    "more_than_n_days_ago"
]

async def parse_intent_node(state: SegmentBuilderState) -> dict:
    """Understand the user's intent; flag if clarification is needed."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system="""You are a CRM segment builder assistant.
Your job is to understand a marketer's description of a customer segment.

Available fields: """ + ", ".join(SEGMENT_FIELDS) + """
Available operators: """ + ", ".join(OPERATORS) + """

If the description is clear enough to build rules, set "clarification_needed": false.
If ambiguous (e.g. "good customers" — what does "good" mean?), set "clarification_needed": true
and provide specific questions.

Respond ONLY with valid JSON:
{
  "clarification_needed": false,
  "clarification_questions": [],
  "extracted_intent": "clear description of what segment to build"
}""",
        messages=[{
            "role": "user",
            "content": f"Segment description: {state['user_description']}"
        }]
    )

    import json
    result = json.loads(response.content[0].text)
    return {
        "clarification_needed": result["clarification_needed"],
        "clarification_questions": result.get("clarification_questions", []),
        "extracted_intent": result.get("extracted_intent"),
        "messages": [{"role": "assistant", "content": response.content[0].text}]
    }

async def build_rules_node(state: SegmentBuilderState) -> dict:
    """Convert extracted intent into structured segment rules."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system="""You are a CRM rule builder.
Convert a segment intent into structured rules.

Output ONLY valid JSON matching this schema:
{
  "operator": "AND" | "OR",
  "rules": [
    {
      "field": "<field_name>",
      "operator": "<operator>",
      "value": "<value or [array]>",
      "label": "Human readable description of this rule"
    }
  ]
}

Available fields: """ + str(SEGMENT_FIELDS) + """
Available operators: """ + str(OPERATORS),
        messages=[{
            "role": "user",
            "content": f"Build rules for: {state['extracted_intent']}"
        }]
    )

    import json
    rules = json.loads(response.content[0].text)
    return {
        "candidate_rules": rules,
        "messages": state["messages"] + [{"role": "assistant", "content": response.content[0].text}]
    }

async def validate_rules_node(state: SegmentBuilderState) -> dict:
    """Validate that rules are syntactically correct and use valid fields/operators."""
    rules = state["candidate_rules"]
    if not rules:
        return {"candidate_rules": None}

    valid_fields = set(SEGMENT_FIELDS)
    valid_ops = set(OPERATORS)

    for rule in rules.get("rules", []):
        if rule["field"] not in valid_fields:
            return {"candidate_rules": None}  # Force rebuild
        if rule["operator"] not in valid_ops:
            return {"candidate_rules": None}

    return {"candidate_rules": rules}  # Valid

async def explain_rules_node(state: SegmentBuilderState) -> dict:
    """Generate a human-readable explanation of the segment rules."""
    rules = state["candidate_rules"]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system="Convert CRM segment rules into a friendly one-sentence plain-English summary for a marketer. Be concise.",
        messages=[{"role": "user", "content": f"Rules: {str(rules)}"}]
    )

    return {
        "rule_set": state["candidate_rules"],
        "explanation": response.content[0].text,
        "confidence": 0.92
    }
```

---

#### AGENT 2: MessageCrafterAgent

**Purpose:** Generates 3 personalised message variants for a given audience segment and channel.

**State:**
```python
class MessageCrafterState(TypedDict):
    segment_description: str
    segment_stats: dict          # {size, avg_ltv, avg_orders, top_categories}
    channel: str                 # 'whatsapp' | 'sms' | 'email' | 'rcs'
    campaign_goal: Optional[str] # 're-engagement' | 'promotion' | 'announcement'
    brand_name: str
    available_variables: list[str]

    # Output
    variants: list[dict]         # 3 message variants
    recommended_variant: int     # 0, 1, or 2
    messages: Annotated[list, add]
```

**Key Node — `generate_variants_node`:**
```python
async def generate_variants_node(state: MessageCrafterState) -> dict:
    channel_constraints = {
        "whatsapp": "160 chars max, conversational, can use 1-2 emojis, no HTML",
        "sms": "160 chars max, no emojis, include opt-out text",
        "email": "Subject line + body, can use HTML, 200-400 words, professional",
        "rcs": "Rich message, can include title + description + CTA button text"
    }

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=f"""You are an expert CRM copywriter for a retail/D2C brand.
Generate 3 distinct message variants for a marketing campaign.

Brand: {state['brand_name']}
Channel: {state['channel']} — {channel_constraints.get(state['channel'], '')}
Goal: {state.get('campaign_goal', 'engagement')}
Available template variables: {', '.join(state['available_variables'])}

Segment context: {state['segment_description']}
Segment stats: avg order value ₹{state['segment_stats'].get('avg_ltv', 0):.0f},
               {state['segment_stats'].get('avg_orders', 0):.0f} orders avg

Generate 3 variants with different tones (friendly, urgent, value-focused).
Use {{variable_name}} syntax for personalisation.

Respond ONLY with JSON:
{{
  "variants": [
    {{
      "label": "Friendly",
      "tone": "warm and personal",
      "subject": "Email subject if applicable",
      "content": "message content here",
      "cta": "Shop Now",
      "estimated_length": 145
    }}
  ],
  "recommendation": 0,
  "reasoning": "Why variant 0 is recommended"
}}""",
        messages=[{"role": "user", "content": "Generate message variants"}]
    )

    import json
    result = json.loads(response.content[0].text)
    return {
        "variants": result["variants"],
        "recommended_variant": result["recommendation"]
    }
```

**Caching:** Cache output in Redis keyed by `hash(segment_id + channel + goal)` for 1 hour (message variants are reusable).

---

#### AGENT 3: InsightSummaryAgent

**Purpose:** Takes campaign analytics data and generates a natural-language insight paragraph + recommendations.

```python
async def generate_insight_node(state: InsightSummaryState) -> dict:
    stats = state["campaign_stats"]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system="""You are a marketing analytics expert for a retail CRM.
Analyse campaign performance and provide:
1. A 2-3 sentence performance summary
2. 2-3 actionable recommendations
Be specific with numbers. Compare against benchmarks if provided.
Industry benchmarks: Email open rate 25%, WhatsApp open rate 60%, SMS delivery 95%

Respond with JSON:
{
  "summary": "...",
  "highlights": ["positive finding 1", "positive finding 2"],
  "recommendations": [
    {"action": "...", "rationale": "...", "urgency": "high|medium|low"}
  ]
}""",
        messages=[{
            "role": "user",
            "content": f"""Campaign: {state['campaign_name']}
Stats: Sent {stats['sent']}, Delivered {stats['delivered']} ({stats.get('deliveryRate', 0):.1%}),
Opened {stats['opened']} ({stats.get('openRate', 0):.1%}),
Clicked {stats['clicked']} ({stats.get('clickRate', 0):.1%}),
Channel: {stats['channel']},
Segment: {stats['segmentName']}"""
        }]
    )

    import json
    return {"insight": json.loads(response.content[0].text)}
```

---

#### AGENT 4: NLQueryAgent (Conversational CRM Assistant)

**Purpose:** Allow marketers to query the CRM in plain English. Routes intents to the right tool calls.

**Tools available to agent:**
```python
# agents/nl_query/tools.py
from langchain_core.tools import tool
import httpx

@tool
async def get_customer_count(filters: dict = {}) -> str:
    """Get count of customers matching criteria. Filters: min_ltv, max_ltv, min_orders, city, tags, days_since_last_order_gt"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/customers",
            params={"count_only": "true", **filters},
            headers={"Authorization": f"Bearer {get_internal_token()}"}
        )
    data = response.json()
    return f"{data['total']} customers match the criteria"

@tool
async def get_campaign_performance(campaign_id: str = None) -> str:
    """Get performance stats for a campaign or all recent campaigns"""
    if campaign_id:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BACKEND_URL}/api/campaigns/{campaign_id}/analytics")
        return str(r.json())
    else:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BACKEND_URL}/api/analytics/overview")
        return str(r.json())

@tool
async def list_segments() -> str:
    """List all available segments with their audience sizes"""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND_URL}/api/segments")
    segments = r.json()["data"]
    return "\n".join([f"- {s['name']}: {s['audienceSize']} customers" for s in segments])

@tool
async def suggest_segment_for_goal(goal: str) -> str:
    """Suggest which existing segment to target for a given campaign goal"""
    # Returns best matching segment name + rationale
    ...

@tool
async def get_top_customers(n: int = 10, by: str = "ltv") -> str:
    """Get top N customers by LTV or order count"""
    ...
```

**LangGraph ReAct agent:**
```python
# agents/nl_query/agent.py
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from .tools import get_customer_count, get_campaign_performance, list_segments, suggest_segment_for_goal, get_top_customers

llm = ChatAnthropic(model="claude-sonnet-4-20250514")

tools = [
    get_customer_count,
    get_campaign_performance,
    list_segments,
    suggest_segment_for_goal,
    get_top_customers
]

nl_query_agent = create_react_agent(
    llm,
    tools,
    state_modifier="""You are a helpful CRM assistant for a retail brand.
Help marketers understand their customer data and campaign performance.
When asked about specific numbers, use the available tools to get real data.
Always cite specific numbers from tool results.
When appropriate, suggest next actions (e.g. "Would you like me to build a segment for these customers?")
Keep responses concise and actionable. Use markdown for structure."""
)
```

**Streaming endpoint:**
```python
# routers/chat.py
@router.post("/")
async def chat_with_agent(request: ChatRequest, brand_id: str = Depends(get_brand_from_token)):

    async def event_generator():
        # Check Redis cache for identical recent queries (5 min cache)
        cache_key = f"chat:{brand_id}:{hash(request.message)}"
        cached = await redis.get(cache_key)
        if cached:
            yield f"data: {cached}\n\n"
            return

        full_response = ""
        async for event in nl_query_agent.astream_events(
            {"messages": [("user", request.message)]},
            version="v1"
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            elif event["event"] == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"

            elif event["event"] == "on_tool_end":
                yield f"data: {json.dumps({'type': 'tool_result', 'tool': event['name'], 'result': str(event['data']['output'])[:200]})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # Cache for 5 minutes
        await redis.setex(cache_key, 300, json.dumps({"type": "cached", "content": full_response}))

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## 8. CHANNEL SERVICE — Stubbed Delivery Simulator

### 8.1 Architecture & Purpose

A completely separate Express.js service that:
1. Receives send requests from the CRM backend
2. Simulates the async delivery lifecycle (DELIVERED, FAILED, OPENED, READ, CLICKED)
3. Calls back to the CRM's webhook endpoint with events at randomised intervals

This mirrors real-world messaging providers like Twilio (SMS), Meta (WhatsApp), SendGrid (Email).

```
packages/channel-service/
├── src/
│   ├── index.ts
│   ├── app.ts
│   ├── routes/
│   │   ├── send.routes.ts         # POST /send (receive from CRM)
│   │   └── health.routes.ts
│   ├── simulator/
│   │   ├── eventSimulator.ts      # Core simulation logic
│   │   ├── probabilityModels.ts   # Channel-specific success rates
│   │   └── scheduler.ts           # setTimeout-based event scheduling
│   ├── queue/
│   │   └── simulationQueue.ts     # BullMQ queue for simulation jobs
│   └── callbacks/
│       └── crmCallback.ts         # HTTP client to call CRM webhook
├── package.json
└── tsconfig.json
```

### 8.2 Send Endpoint

```typescript
// POST /send — called by CRM backend
// Body: { communications: [{ communicationId, recipient, channel, message }] }

router.post('/send', async (req, res) => {
  // Verify HMAC from CRM
  const signature = req.headers['x-crm-signature']
  if (!verifyHMAC(req.body, signature, process.env.CRM_SEND_SECRET)) {
    return res.status(401).json({ error: 'Unauthorized' })
  }

  const { communications } = req.body

  // Acknowledge immediately
  res.status(202).json({
    accepted: communications.length,
    message: 'Communications queued for simulation'
  })

  // Enqueue each communication for simulation
  for (const comm of communications) {
    await simulationQueue.add('simulate', comm, {
      delay: Math.random() * 2000,  // 0-2s before first event
      attempts: 1
    })
  }
})
```

### 8.3 Event Simulation Logic

```typescript
// simulator/probabilityModels.ts
export const CHANNEL_MODELS = {
  whatsapp: {
    deliveryRate: 0.97,
    openRate: 0.65,    // Conditional on delivery
    readRate: 0.55,    // Conditional on open
    clickRate: 0.18,   // Conditional on read
    conversionRate: 0.08
  },
  sms: {
    deliveryRate: 0.95,
    openRate: 0.40,
    readRate: 0.35,
    clickRate: 0.05,
    conversionRate: 0.03
  },
  email: {
    deliveryRate: 0.90,
    openRate: 0.25,
    readRate: 0.20,
    clickRate: 0.08,
    conversionRate: 0.05
  },
  rcs: {
    deliveryRate: 0.85,
    openRate: 0.45,
    readRate: 0.40,
    clickRate: 0.20,
    conversionRate: 0.10
  }
}

// simulator/eventSimulator.ts
export async function simulateCommunication(comm: SendRequest): Promise<void> {
  const model = CHANNEL_MODELS[comm.channel]

  // Event 1: DELIVERED or FAILED (1-5s delay)
  await sleep(randomBetween(1000, 5000))
  const delivered = Math.random() < model.deliveryRate
  await sendCallback(comm.communicationId, delivered ? 'delivered' : 'failed')

  if (!delivered) return

  // Event 2: OPENED (5-300s delay — simulates user opening their phone)
  if (Math.random() < model.openRate) {
    await sleep(randomBetween(5000, 300000))
    await sendCallback(comm.communicationId, 'opened')

    // Event 3: READ (0-60s after open)
    if (Math.random() < model.readRate) {
      await sleep(randomBetween(0, 60000))
      await sendCallback(comm.communicationId, 'read')

      // Event 4: CLICKED (0-120s after read)
      if (Math.random() < model.clickRate) {
        await sleep(randomBetween(0, 120000))
        await sendCallback(comm.communicationId, 'clicked')

        // Event 5: CONVERTED (0-3600s after click)
        if (Math.random() < model.conversionRate) {
          await sleep(randomBetween(0, 3600000))
          await sendCallback(comm.communicationId, 'converted')
        }
      }
    }
  }
}

// callbacks/crmCallback.ts
async function sendCallback(communicationId: string, eventType: string): Promise<void> {
  const payload = {
    communicationId,
    eventType,
    timestamp: new Date().toISOString(),
    metadata: {}
  }

  const signature = signHMAC(payload, process.env.CHANNEL_WEBHOOK_SECRET)

  await axios.post(
    `${process.env.CRM_URL}/api/webhooks/channel/${communicationId}`,
    payload,
    {
      headers: { 'x-channel-signature': signature },
      timeout: 5000
    }
  )
}
```

---

## 9. REDIS ARCHITECTURE — Caching, Queues & Pub/Sub

### 9.1 Redis Key Namespace

All keys follow the pattern: `{namespace}:{service}:{id}:{subkey}`

```
# Authentication
auth:tokens:{userId}:refresh          → refresh token (hash), TTL: 7d
auth:blocklist:{jti}                  → invalidated tokens, TTL: access token expiry

# Customer Cache
cache:customers:{brandId}:list:{hash} → paginated customer list, TTL: 2min
cache:customers:{brandId}:total       → total customer count, TTL: 5min
cache:customer:{id}:detail            → single customer detail, TTL: 5min

# Segment Cache
cache:segment:{id}:audience           → evaluated audience customer IDs, TTL: 10min
cache:segment:{id}:count              → audience count, TTL: 5min
cache:segments:{brandId}:list         → all segments list, TTL: 5min

# Campaign Cache
cache:campaign:{id}:analytics         → campaign analytics, TTL: 60s (SENDING), 5min (SENT)
cache:campaigns:{brandId}:list        → campaign list, TTL: 2min

# Analytics Cache
cache:analytics:overview:{brandId}    → dashboard KPIs, TTL: 5min
cache:analytics:engagement:{brandId}:{days} → time series, TTL: 10min

# Agent Cache
cache:agent:segment:{hash}            → SegmentBuilderAgent output, TTL: 1h
cache:agent:message:{hash}            → MessageCrafterAgent output, TTL: 1h
cache:agent:insight:{campaignId}      → InsightSummaryAgent output, TTL: 30min
cache:agent:chat:{brandId}:{hash}     → NL query response, TTL: 5min

# Rate Limiting
ratelimit:api:{ip}                    → request count, TTL: 1min (window)
ratelimit:api:{userId}                → per-user API rate limit

# BullMQ Queues (managed by BullMQ — do not set manually)
bull:campaign-send:{...}
bull:webhook-processing:{...}
bull:analytics-refresh:{...}

# Pub/Sub Channels (ephemeral — no persistence)
campaign:{id}:events                  → real-time event stream for SSE
```

### 9.2 Redis Helper Utilities

```typescript
// cache/helpers.ts

/**
 * Get from cache or compute and store
 */
export async function getOrSet<T>(
  key: string,
  ttl: number,
  compute: () => Promise<T>
): Promise<T> {
  const cached = await redis.get(key)
  if (cached) {
    return JSON.parse(cached) as T
  }

  const value = await compute()
  await redis.setex(key, ttl, JSON.stringify(value))
  return value
}

/**
 * Invalidate all keys matching a pattern
 */
export async function invalidatePattern(pattern: string): Promise<void> {
  const keys = await redis.keys(pattern)
  if (keys.length > 0) {
    await redis.del(...keys)
  }
}

/**
 * Cache invalidation hooks — call after mutations
 */
export const invalidators = {
  onCustomerChange: (brandId: string) =>
    invalidatePattern(`cache:customers:${brandId}:*`),

  onSegmentChange: (segmentId: string, brandId: string) =>
    Promise.all([
      redis.del(`cache:segment:${segmentId}:*`),
      invalidatePattern(`cache:segments:${brandId}:*`)
    ]),

  onCampaignLaunch: (campaignId: string, brandId: string) =>
    Promise.all([
      redis.del(`cache:campaign:${campaignId}:analytics`),
      invalidatePattern(`cache:campaigns:${brandId}:*`),
      invalidatePattern(`cache:analytics:*:${brandId}`)
    ])
}
```

### 9.3 BullMQ Queue Configuration

```typescript
// jobs/queue.ts
import { Queue, Worker, QueueEvents } from 'bullmq'

const connection = {
  host: process.env.REDIS_HOST,
  port: Number(process.env.REDIS_PORT),
  password: process.env.REDIS_PASSWORD,
}

// Campaign send queue — dispatches batches to channel service
export const campaignSendQueue = new Queue('campaign-send', {
  connection,
  defaultJobOptions: {
    attempts: 3,
    backoff: { type: 'exponential', delay: 2000 },
    removeOnComplete: { count: 100 },
    removeOnFail: { count: 50 }
  }
})

// Webhook processing queue — processes channel service callbacks
export const webhookProcessingQueue = new Queue('webhook-processing', {
  connection,
  defaultJobOptions: {
    attempts: 5,
    backoff: { type: 'exponential', delay: 1000 },
    removeOnComplete: { count: 500 }
  }
})

// Analytics refresh queue — scheduled analytics computation
export const analyticsRefreshQueue = new Queue('analytics-refresh', {
  connection,
  defaultJobOptions: {
    attempts: 2,
    removeOnComplete: { count: 50 }
  }
})

// Monitor queue events for observability
export const campaignSendEvents = new QueueEvents('campaign-send', { connection })
campaignSendEvents.on('failed', ({ jobId, failedReason }) => {
  console.error(`Campaign send job ${jobId} failed:`, failedReason)
  // TODO: Alert via Slack / email in production
})
```

---

## 10. COMPLETE DATABASE SCHEMA (Prisma)

```prisma
// prisma/schema.prisma
generator client {
  provider        = "prisma-client-js"
  previewFeatures = ["fullTextSearch", "fullTextIndex"]
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// ─────────────────────────────────────────────────────
// AUTH / BRAND
// ─────────────────────────────────────────────────────

model Brand {
  id             String    @id @default(cuid())
  name           String
  email          String    @unique
  passwordHash   String
  logoUrl        String?
  timezone       String    @default("Asia/Kolkata")
  currency       String    @default("INR")
  createdAt      DateTime  @default(now())
  updatedAt      DateTime  @updatedAt

  customers      Customer[]
  orders         Order[]
  segments       Segment[]
  campaigns      Campaign[]
  communications Communication[]
  refreshTokens  RefreshToken[]

  @@map("brands")
}

model RefreshToken {
  id         String   @id @default(cuid())
  token      String   @unique
  brandId    String
  brand      Brand    @relation(fields: [brandId], references: [id], onDelete: Cascade)
  expiresAt  DateTime
  createdAt  DateTime @default(now())

  @@index([brandId])
  @@map("refresh_tokens")
}

// ─────────────────────────────────────────────────────
// CUSTOMERS
// ─────────────────────────────────────────────────────

model Customer {
  id                  String    @id @default(cuid())
  brandId             String
  brand               Brand     @relation(fields: [brandId], references: [id], onDelete: Cascade)

  // Identity
  name                String
  email               String?
  phone               String?
  externalId          String?   // Brand's own customer ID for CSV imports

  // Demographics
  city                String?
  country             String    @default("India")
  dateOfBirth         DateTime?
  gender              String?

  // Computed fields (updated via triggers / cron)
  totalOrders         Int       @default(0)
  totalSpent          Decimal   @default(0) @db.Decimal(12, 2)
  averageOrderValue   Decimal   @default(0) @db.Decimal(10, 2)
  firstOrderDate      DateTime?
  lastOrderDate       DateTime?
  daysSinceLastOrder  Int?

  // Segmentation helpers
  tags                String[]  @default([])
  preferredChannel    Channel   @default(EMAIL)
  preferredCategories String[]  @default([])

  // Status
  isActive            Boolean   @default(true)
  isDeleted           Boolean   @default(false)
  deletedAt           DateTime?

  createdAt           DateTime  @default(now())
  updatedAt           DateTime  @updatedAt

  orders              Order[]
  communications      Communication[]
  segmentMemberships  SegmentMembership[]

  @@unique([brandId, email])
  @@unique([brandId, phone])
  @@unique([brandId, externalId])
  @@index([brandId, isDeleted])
  @@index([brandId, lastOrderDate])
  @@index([brandId, totalSpent])
  @@index([brandId, totalOrders])
  @@map("customers")
}

// ─────────────────────────────────────────────────────
// ORDERS
// ─────────────────────────────────────────────────────

model Order {
  id              String     @id @default(cuid())
  brandId         String
  brand           Brand      @relation(fields: [brandId], references: [id], onDelete: Cascade)
  customerId      String
  customer        Customer   @relation(fields: [customerId], references: [id], onDelete: Cascade)

  externalOrderId String?    // Brand's own order ID

  totalAmount     Decimal    @db.Decimal(12, 2)
  discountAmount  Decimal    @default(0) @db.Decimal(10, 2)
  netAmount       Decimal    @db.Decimal(12, 2)
  currency        String     @default("INR")

  status          OrderStatus @default(COMPLETED)
  channel         OrderChannel @default(ONLINE)  // online/in-store/app

  orderedAt       DateTime
  createdAt       DateTime   @default(now())
  updatedAt       DateTime   @updatedAt

  items           OrderItem[]

  @@index([brandId, customerId])
  @@index([brandId, orderedAt])
  @@index([customerId, orderedAt])
  @@map("orders")
}

model OrderItem {
  id          String   @id @default(cuid())
  orderId     String
  order       Order    @relation(fields: [orderId], references: [id], onDelete: Cascade)

  productId   String?
  productName String
  category    String?
  quantity    Int
  unitPrice   Decimal  @db.Decimal(10, 2)
  totalPrice  Decimal  @db.Decimal(10, 2)

  @@index([orderId])
  @@map("order_items")
}

// ─────────────────────────────────────────────────────
// SEGMENTS
// ─────────────────────────────────────────────────────

model Segment {
  id              String    @id @default(cuid())
  brandId         String
  brand           Brand     @relation(fields: [brandId], references: [id], onDelete: Cascade)

  name            String
  description     String?
  color           String    @default("#0176d3")

  // Rule set stored as JSONB for flexibility
  ruleSet         Json      // { operator: 'AND'|'OR', rules: Rule[] }
  ruleExplanation String?   // AI-generated plain English explanation

  // Stats (updated on evaluation)
  audienceSize    Int       @default(0)
  lastEvaluatedAt DateTime?

  isAiGenerated   Boolean   @default(false)
  isActive        Boolean   @default(true)

  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt

  memberships     SegmentMembership[]
  campaigns       Campaign[]

  @@index([brandId])
  @@map("segments")
}

model SegmentMembership {
  customerId  String
  customer    Customer @relation(fields: [customerId], references: [id], onDelete: Cascade)
  segmentId   String
  segment     Segment  @relation(fields: [segmentId], references: [id], onDelete: Cascade)
  addedAt     DateTime @default(now())

  @@id([customerId, segmentId])
  @@index([segmentId])
  @@map("segment_memberships")
}

// ─────────────────────────────────────────────────────
// CAMPAIGNS
// ─────────────────────────────────────────────────────

model Campaign {
  id               String         @id @default(cuid())
  brandId          String
  brand            Brand          @relation(fields: [brandId], references: [id], onDelete: Cascade)
  segmentId        String
  segment          Segment        @relation(fields: [segmentId], references: [id])

  name             String
  description      String?
  channel          Channel
  status           CampaignStatus @default(DRAFT)
  messageTemplate  String         // Raw template with {{variables}}
  subject          String?        // Email subject
  ctaText          String?        // CTA button text for RCS

  audienceSize     Int            @default(0)
  scheduledAt      DateTime?
  launchedAt       DateTime?
  completedAt      DateTime?

  // Aggregated stats (denormalized for fast reads)
  statQueued       Int            @default(0)
  statSent         Int            @default(0)
  statDelivered    Int            @default(0)
  statFailed       Int            @default(0)
  statOpened       Int            @default(0)
  statRead         Int            @default(0)
  statClicked      Int            @default(0)
  statConverted    Int            @default(0)

  createdAt        DateTime       @default(now())
  updatedAt        DateTime       @updatedAt

  communications   Communication[]

  @@index([brandId, status])
  @@index([brandId, launchedAt])
  @@map("campaigns")
}

// ─────────────────────────────────────────────────────
// COMMUNICATIONS (individual messages per recipient)
// ─────────────────────────────────────────────────────

model Communication {
  id              String              @id @default(cuid())
  brandId         String
  brand           Brand               @relation(fields: [brandId], references: [id], onDelete: Cascade)
  campaignId      String
  campaign        Campaign            @relation(fields: [campaignId], references: [id], onDelete: Cascade)
  customerId      String
  customer        Customer            @relation(fields: [customerId], references: [id], onDelete: Cascade)

  channel         Channel
  status          CommunicationStatus @default(QUEUED)
  messageContent  String              // Personalised message (vars replaced)

  // Event timestamps
  sentAt          DateTime?
  deliveredAt     DateTime?
  failedAt        DateTime?
  openedAt        DateTime?
  readAt          DateTime?
  clickedAt       DateTime?
  convertedAt     DateTime?

  failureReason   String?

  createdAt       DateTime            @default(now())
  updatedAt       DateTime            @updatedAt

  events          CommunicationEvent[]

  // Partitioning note: At scale, partition this table by brandId+createdAt (monthly)
  @@index([campaignId, status])
  @@index([customerId])
  @@index([brandId, createdAt])
  @@map("communications")
}

model CommunicationEvent {
  id              String    @id @default(cuid())
  communicationId String
  communication   Communication @relation(fields: [communicationId], references: [id], onDelete: Cascade)

  eventType       String    // delivered, failed, opened, read, clicked, converted
  timestamp       DateTime
  metadata        Json      @default("{}")  // IP, user agent, click URL, etc.

  createdAt       DateTime  @default(now())

  @@index([communicationId])
  @@map("communication_events")
}

// ─────────────────────────────────────────────────────
// ENUMS
// ─────────────────────────────────────────────────────

enum Channel {
  WHATSAPP
  SMS
  EMAIL
  RCS
}

enum CampaignStatus {
  DRAFT
  SCHEDULED
  SENDING
  SENT
  FAILED
  CANCELLED
}

enum CommunicationStatus {
  QUEUED
  SENT
  DELIVERED
  FAILED
  OPENED
  READ
  CLICKED
  CONVERTED
}

enum OrderStatus {
  PENDING
  COMPLETED
  CANCELLED
  REFUNDED
}

enum OrderChannel {
  ONLINE
  IN_STORE
  APP
  MARKETPLACE
}
```

---

## 11. FULL API CONTRACT REFERENCE

### Request/Response Schemas

#### `POST /api/auth/login`
```typescript
// Request
{ email: string, password: string }

// Response 200
{
  user: { id, name, email, brandId },
  token: string,           // JWT, 15min expiry
  refreshToken: string     // 7 day expiry
}
```

#### `GET /api/customers` (paginated)
```typescript
// Response 200
{
  data: Customer[],
  meta: {
    total: number,
    page: number,
    limit: number,
    totalPages: number
  }
}
```

#### `POST /api/customers/import`
```typescript
// Request
{
  rows: Array<{
    name: string,
    email?: string,
    phone?: string,
    externalId?: string,
    city?: string,
    tags?: string[]
  }>,
  options: {
    updateExisting: boolean   // Upsert if email/phone matches
  }
}

// Response 200
{
  created: number,
  updated: number,
  skipped: number,
  errors: Array<{ row: number, reason: string }>
}
```

#### `POST /api/segments/evaluate`
```typescript
// Request
{
  ruleSet: {
    operator: 'AND' | 'OR',
    rules: Array<{
      field: string,
      operator: string,
      value: string | number | string[]
    }>
  }
}

// Response 200
{
  count: number,
  sampleCustomers: Array<{ id, name, email, totalOrders, totalSpent }>
}
```

#### `POST /api/campaigns/:id/launch`
```typescript
// Request: No body required
// Response 200
{
  campaignId: string,
  status: 'SENDING',
  audienceSize: number,
  estimatedCompletionSeconds: number
}
```

#### `GET /api/campaigns/:id/analytics`
```typescript
// Response 200
{
  campaignId: string,
  status: CampaignStatus,
  audienceSize: number,
  stats: {
    queued: number,
    sent: number,
    delivered: number,
    failed: number,
    opened: number,
    read: number,
    clicked: number,
    converted: number
  },
  rates: {
    deliveryRate: number,     // delivered/sent
    openRate: number,         // opened/delivered
    readRate: number,         // read/delivered
    clickRate: number,        // clicked/opened
    conversionRate: number    // converted/clicked
  },
  hourlyBreakdown: Array<{
    hour: string,             // ISO timestamp
    sent: number,
    delivered: number,
    opened: number,
    clicked: number
  }>,
  computedAt: string
}
```

#### `POST /api/webhooks/channel/:communicationId`
```typescript
// Called BY channel service — headers: x-channel-signature: HMAC
// Request body
{
  communicationId: string,
  eventType: 'delivered' | 'failed' | 'opened' | 'read' | 'clicked' | 'converted',
  timestamp: string,          // ISO 8601
  metadata: {
    failureReason?: string,
    clickUrl?: string,
    userAgent?: string
  }
}

// Response 202 (always, to prevent retries)
{ received: true }
```

#### `POST /api/agents/segments/build`
```typescript
// Request
{
  description: string,          // NL segment description
  brandId: string,
  existingSegmentNames: string[]
}

// Response 200 (or stream)
{
  ruleSet: {
    operator: 'AND' | 'OR',
    rules: Array<{
      field: string,
      operator: string,
      value: any,
      label: string
    }>
  },
  explanation: string,
  confidence: number,
  clarificationNeeded: boolean,
  clarificationQuestions?: string[]
}
```

#### `POST /api/agents/messages/draft`
```typescript
// Request
{
  segmentId: string,
  channel: Channel,
  goal?: 're-engagement' | 'promotion' | 'announcement' | 'loyalty',
  brandName: string
}

// Response 200
{
  variants: Array<{
    label: string,
    tone: string,
    subject?: string,      // Email only
    content: string,
    cta?: string,
    estimatedLength: number
  }>,
  recommendedVariant: number,
  reasoning: string
}
```

#### `POST /api/agents/chat` (SSE Stream)
```typescript
// Request
{
  message: string,
  conversationHistory: Array<{ role: 'user' | 'assistant', content: string }>
}

// SSE events
data: { type: 'token', content: '...' }
data: { type: 'tool_start', tool: 'get_customer_count' }
data: { type: 'tool_result', tool: 'get_customer_count', result: '...' }
data: { type: 'done' }
```

---

## 12. LANGGRAPH AGENT DEFINITIONS

### Agent Execution Flow Summary

```
User Intent → Parse → Route → Execute → Cache → Respond

SegmentBuilderAgent:
  parse_intent → [clarify | build_rules] → validate_rules → explain_rules → END

MessageCrafterAgent:
  gather_context → generate_variants → rank_variants → END

CampaignOrchestratorAgent (Chat-driven):
  understand_goal → suggest_segment → suggest_channel → draft_message → confirm → dispatch → END

InsightSummaryAgent:
  fetch_stats → compute_metrics → generate_summary → add_recommendations → END

NLQueryAgent (ReAct pattern):
  reason → [tool_call]* → synthesize_response → END
```

### Agent Invocation from Express Backend

```typescript
// services/agentClient.service.ts
import axios from 'axios'

const agentClient = axios.create({
  baseURL: process.env.AGENT_SERVICE_URL,
  timeout: 30000,  // 30s for AI calls
  headers: {
    'x-internal-secret': process.env.INTERNAL_API_SECRET
  }
})

export async function invokeSegmentBuilder(
  description: string,
  context: BrandContext
): Promise<SegmentRuleSet> {
  const response = await agentClient.post('/agents/segments/build', {
    description,
    brandId: context.brandId,
    existingSegmentNames: context.existingSegmentNames
  })
  return response.data
}

export async function invokeMessageDrafter(
  segmentId: string,
  channel: Channel,
  goal: string,
  brandName: string
): Promise<MessageVariants> {
  const response = await agentClient.post('/agents/messages/draft', {
    segmentId, channel, goal, brandName
  })
  return response.data
}

export function streamChatResponse(
  message: string,
  history: ChatMessage[]
): EventSource {
  return new EventSource(
    `${process.env.AGENT_SERVICE_URL}/agents/chat/stream?message=${encodeURIComponent(message)}`
  )
}
```

---

## 13. ENVIRONMENT VARIABLES

### `packages/backend/.env`
```bash
# Database
DATABASE_URL="postgresql://xeno_user:password@localhost:5432/xeno_crm"

# Redis
REDIS_URL="redis://:password@localhost:6379"
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD="your_redis_password"

# JWT
JWT_SECRET="super-secret-jwt-key-32chars-min"
JWT_EXPIRES_IN="15m"
REFRESH_TOKEN_EXPIRES_IN="7d"

# Internal service secrets
INTERNAL_API_SECRET="internal-service-auth-key"
CHANNEL_WEBHOOK_SECRET="hmac-secret-for-channel-callbacks"
CRM_SEND_SECRET="hmac-secret-for-send-requests"

# Service URLs
FRONTEND_URL="http://localhost:5173"
AGENT_SERVICE_URL="http://localhost:8000"
CHANNEL_SERVICE_URL="http://localhost:3002"

# Server
PORT="3001"
NODE_ENV="development"
```

### `packages/agent-service/.env`
```bash
# Anthropic
ANTHROPIC_API_KEY="sk-ant-..."

# Redis
REDIS_URL="redis://:password@localhost:6379"

# Backend connection
BACKEND_URL="http://localhost:3001"
INTERNAL_API_SECRET="internal-service-auth-key"

# Server
PORT="8000"
ENV="development"
```

### `packages/channel-service/.env`
```bash
# Channel simulation
CRM_URL="http://localhost:3001"
CHANNEL_WEBHOOK_SECRET="hmac-secret-for-channel-callbacks"
CRM_SEND_SECRET="hmac-secret-for-send-requests"

# Redis (for simulation queue)
REDIS_URL="redis://:password@localhost:6379"

PORT="3002"
```

### `packages/frontend/.env`
```bash
VITE_API_URL="http://localhost:3001"
VITE_APP_NAME="Xeno CRM"
VITE_APP_VERSION="1.0.0"
```

---

## 14. SEED DATA STRATEGY

The seed script should create a realistic fashion/retail brand with compelling data.

### Seed Specification (`prisma/seed.ts`)

```typescript
// Brand: "Zara India" (fictional fashion brand)
// Customers: 500 seeded with realistic Indian names + purchase patterns
// Orders: ~1500 orders over 2 years
// Segments: 6 pre-built segments
// Campaigns: 4 historical campaigns with simulated analytics

const SEGMENTS_TO_SEED = [
  {
    name: "Loyal Champions",
    description: "Purchased 5+ times with LTV > ₹15,000",
    ruleSet: {
      operator: "AND",
      rules: [
        { field: "total_orders", operator: "greater_than", value: 4, label: "More than 4 orders" },
        { field: "total_spent", operator: "greater_than", value: 15000, label: "Spent over ₹15,000" }
      ]
    }
  },
  {
    name: "At-Risk Customers",
    description: "Previously active, haven't ordered in 60-120 days",
    ruleSet: {
      operator: "AND",
      rules: [
        { field: "days_since_last_order", operator: "between", value: [60, 120], label: "60-120 days inactive" },
        { field: "total_orders", operator: "greater_than", value: 1, label: "More than 1 order" }
      ]
    }
  },
  {
    name: "Lapsed Buyers",
    description: "No order in 120+ days",
    ruleSet: {
      operator: "AND",
      rules: [
        { field: "days_since_last_order", operator: "greater_than", value: 120, label: "Inactive 120+ days" }
      ]
    }
  },
  {
    name: "New Customers",
    description: "First order within last 30 days",
    ruleSet: {
      operator: "AND",
      rules: [
        { field: "total_orders", operator: "equals", value: 1, label: "Exactly 1 order" },
        { field: "days_since_last_order", operator: "less_than", value: 30, label: "Within last 30 days" }
      ]
    }
  },
  {
    name: "High-Value Prospects",
    description: "AOV > ₹5000, ordered 2-4 times",
    ruleSet: {
      operator: "AND",
      rules: [
        { field: "average_order_value", operator: "greater_than", value: 5000, label: "AOV above ₹5,000" },
        { field: "total_orders", operator: "between", value: [2, 4], label: "2-4 orders" }
      ]
    }
  },
  {
    name: "WhatsApp Engaged",
    description: "Preferred channel is WhatsApp, active in last 90 days",
    ruleSet: {
      operator: "AND",
      rules: [
        { field: "preferred_channel", operator: "equals", value: "WHATSAPP", label: "WhatsApp preferred" },
        { field: "days_since_last_order", operator: "less_than", value: 90, label: "Active in 90 days" }
      ]
    }
  }
]

// Customer name pool — realistic Indian names
const FIRST_NAMES = ["Priya", "Rahul", "Anjali", "Arjun", "Sneha", "Vikram", "Pooja", "Karan", "Divya", "Rohan", ...]
const CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Pune", "Chennai", "Jaipur", "Ahmedabad", ...]
const CATEGORIES = ["Women's Ethnic", "Men's Western", "Accessories", "Footwear", "Kids", "Home & Living"]
```

---

## 15. DEPLOYMENT ARCHITECTURE

### `docker-compose.yml` (Local Development)
```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: xeno_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: xeno_crm
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass password
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./packages/backend
    ports:
      - "3001:3001"
    environment:
      DATABASE_URL: postgresql://xeno_user:password@postgres:5432/xeno_crm
      REDIS_URL: redis://:password@redis:6379
    depends_on:
      - postgres
      - redis
    command: sh -c "npx prisma migrate deploy && npm run dev"

  agent-service:
    build: ./packages/agent-service
    ports:
      - "8000:8000"
    environment:
      REDIS_URL: redis://:password@redis:6379
    depends_on:
      - redis
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  channel-service:
    build: ./packages/channel-service
    ports:
      - "3002:3002"
    environment:
      CRM_URL: http://backend:3001
      REDIS_URL: redis://:password@redis:6379
    depends_on:
      - redis

  frontend:
    build: ./packages/frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://localhost:3001
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

### Production Deployment (Recommended: Railway)

```
Railway Project:
├── Service: postgres      → PostgreSQL plugin
├── Service: redis         → Redis plugin
├── Service: backend       → Deploy from /packages/backend, Dockerfile
├── Service: agent-service → Deploy from /packages/agent-service, Dockerfile
├── Service: channel-service → Deploy from /packages/channel-service, Dockerfile
└── Service: frontend      → Deploy from /packages/frontend, static build
```

**`packages/backend/Dockerfile`:**
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npx prisma generate
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/prisma ./prisma
EXPOSE 3001
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/index.js"]
```

**`packages/agent-service/Dockerfile`:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 16. ERROR HANDLING & OBSERVABILITY

### Global Error Handler (Express)
```typescript
// middleware/errorHandler.ts
import { Request, Response, NextFunction } from 'express'
import { ZodError } from 'zod'
import { Prisma } from '@prisma/client'

export class AppError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public code?: string
  ) {
    super(message)
  }
}

export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction) {
  // Zod validation errors
  if (err instanceof ZodError) {
    return res.status(400).json({
      error: 'Validation failed',
      code: 'VALIDATION_ERROR',
      details: err.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    })
  }

  // Prisma errors
  if (err instanceof Prisma.PrismaClientKnownRequestError) {
    if (err.code === 'P2002') {
      return res.status(409).json({ error: 'Record already exists', code: 'DUPLICATE' })
    }
    if (err.code === 'P2025') {
      return res.status(404).json({ error: 'Record not found', code: 'NOT_FOUND' })
    }
  }

  // App errors
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: err.message,
      code: err.code
    })
  }

  // Unhandled errors
  console.error('Unhandled error:', err)
  res.status(500).json({ error: 'Internal server error', code: 'INTERNAL_ERROR' })
}
```

### Structured Logging
```typescript
// middleware/requestLogger.ts
// Log format: { timestamp, requestId, method, path, statusCode, durationMs, brandId }
// In production: ship to Datadog / CloudWatch / Grafana Loki
```

---

## 17. SCALABILITY TRADEOFFS & NOTES

This section is intended to be discussed live in the interview.

| Decision | Current Approach | At Scale (10x) | At Scale (100x) |
|---|---|---|---|
| Communication delivery | BullMQ + Redis | Same + Redis Cluster | Migrate to Kafka |
| Analytics | Real-time DB groupBy + Redis cache | Pre-aggregate in materialized views | ClickHouse OLAP |
| Segment evaluation | Prisma dynamic WHERE | Same + result caching | Pre-compute + nightly refresh |
| Communications table | Single table, PostgreSQL | Monthly partitioning | Cassandra / TimescaleDB |
| Agent API | Single FastAPI | Multiple uvicorn workers | K8s horizontal pod autoscaling |
| Redis | Single instance | Sentinel (HA) | Redis Cluster |
| DB | Single instance | Read replica | PgBouncer + sharding |
| SSE (live feed) | Redis pub/sub | Same + sticky sessions | Replace with WebSockets + Socket.io cluster |
| Campaign send | BullMQ batches of 100 | Larger batches + concurrency | Kafka consumer groups |

### Explicit Tradeoffs Made for Assignment Scope

1. **No auth refresh token rotation** — production would rotate refresh tokens on use (sliding window)
2. **Segment evaluation is on-demand** — production would pre-compute and cache nightly
3. **Communications not partitioned** — at 10M rows, add monthly partitioning by `created_at`
4. **Agent service is synchronous** — streaming is implemented; at scale, add a job queue for long-running analysis
5. **No multi-tenancy isolation** — brand data is filtered by `brandId` but not row-level security (RLS)
6. **Channel service has no real retry** — production channel services have complex retry/dedup logic
7. **No dead letter queue** — failed webhook processing jobs would need DLQ + alerting in production

---

## APPENDIX A: CSV Import Format

### Customer Import CSV
```csv
name,email,phone,external_id,city,country,date_of_birth,gender,tags,preferred_channel
"Priya Sharma","priya@email.com","+919876543210","CUST001","Mumbai","India","1990-03-15","Female","vip,loyal","WHATSAPP"
```

### Order Import CSV
```csv
customer_email,customer_phone,external_order_id,total_amount,discount_amount,net_amount,status,channel,ordered_at,product_name,category,quantity,unit_price
"priya@email.com","",,"ORD001","2500","200","2300","COMPLETED","ONLINE","2024-01-15T10:30:00Z","Blue Kurta","Women's Ethnic","1","2500"
```

---

## APPENDIX B: Message Template Variables

Available variables for message templates:
```
{{first_name}}          → Customer's first name
{{full_name}}           → Customer's full name
{{last_order_date}}     → Formatted last order date
{{total_orders}}        → Order count
{{total_spent}}         → Lifetime spend (formatted with currency)
{{average_order_value}} → Formatted AOV
{{brand_name}}          → Brand name
{{campaign_name}}       → Campaign name
{{opt_out_text}}        → "Reply STOP to unsubscribe" (required for SMS)
```

---

## APPENDIX C: Frontend Component Props Reference

### `<StatCard />`
```tsx
interface StatCardProps {
  title: string
  value: string | number
  delta?: { value: number; label: string; positive: boolean }
  icon: LucideIcon
  loading?: boolean
  color?: 'blue' | 'green' | 'orange' | 'red'
}
```

### `<StatusBadge />`
```tsx
interface StatusBadgeProps {
  status: CampaignStatus | CommunicationStatus
  size?: 'sm' | 'md'
}
// Maps statuses to SLDS pill colors:
// DRAFT → grey, SENDING → orange, SENT → green, FAILED → red, etc.
```

### `<DataTable<T> />`
```tsx
interface DataTableProps<T> {
  columns: ColumnDef<T>[]        // TanStack Table column definitions
  data: T[]
  totalCount: number             // Server-side total
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onRowClick?: (row: T) => void
  loading?: boolean
  emptyMessage?: string
  selectable?: boolean
  onSelectionChange?: (rows: T[]) => void
}
```

---

*This document constitutes the complete engineering specification for the Xeno AI-Native Mini CRM.*
*Build exactly this. Every section is intentional. Start with docker-compose + DB schema + backend routes, then agent service, then frontend page by page.*
*Estimated build time with AI-native development workflow: 3-4 days.*
```
