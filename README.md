# 🛒 AI Grocery Shopper

A full-stack, hardware-connected grocery inventory system: a **Raspberry Pi camera** or **phone photo** of your fridge is turned into a structured inventory, cross-referenced against scan history to figure out what's running low, and turned into a **priced, web-grounded shopping list** — powered by a multi-agent Claude pipeline.

This project was built end-to-end (mobile app, backend API, database, cloud storage, and embedded hardware integration) as a way to learn production system design, not just a single framework.

---

## What It Does

1. **Capture** — a Raspberry Pi (camera + Sense HAT for a capture-in-progress light) or a phone photo captures the inside of a fridge/pantry.
2. **Analyze** — a vision agent identifies every edible item in the photo, with a confidence score and estimated quantity, and a second agent independently reviews and corrects that analysis before it's trusted.
3. **Reason** — a third agent looks across the *history* of scans (not just the latest one) to decide what's actually running low and worth restocking.
4. **Shop** — a fourth agent performs live web searches (restricted to real grocery/retail domains) to find a store and a real price for each item — it is never allowed to fabricate a link.
5. **Persist & serve** — inventory, the recommended shopping list, and the original scan photos are stored in **AWS RDS (Postgres)** and **AWS S3**, and served to a **React Native / Expo** app with three screens: Inventory, Shop, and Scan History.

---

## Architecture

```
┌─────────────────┐        ┌──────────────────┐
│  Raspberry Pi    │        │   Mobile App      │
│  (Camera +       │        │   (Expo / RN)     │
│   Sense HAT)     │        │  Camera + Gallery │
└────────┬─────────┘        └─────────┬─────────┘
         │  poll /scan-requested       │
         │  POST /manualscan (image)   │  POST /manualscan (image)
         └──────────────┬──────────────┘
                         ▼
              ┌────────────────────┐
              │   FastAPI backend   │
              │  (single ingestion  │
              │   path — no source  │
              │   branching)        │
              └──────────┬──────────┘
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
┌───────────────┐ ┌─────────────┐  ┌───────────────┐
│ Claude Agent   │ │  AWS S3     │  │  AWS RDS       │
│ Pipeline       │ │ (raw scan   │  │  (PostgreSQL)  │
│ (analyze →     │ │  photos,    │  │  inventory /   │
│  reflect →     │ │  presigned  │  │  shopping /    │
│  reason → shop)│ │  URLs)      │  │  scans tables  │
└───────────────┘ └─────────────┘  └───────────────┘
```

The Raspberry Pi and the phone hit the **exact same endpoint** (`/manualscan`) — the backend doesn't care whether the photo came from embedded hardware or a human tapping a button. That single-ingestion-path design is deliberate: it means the AI pipeline, persistence, and API surface only had to be written once.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Mobile app** | React Native, Expo SDK 54, Expo Router (file-based routing), TypeScript |
| **Backend API** | Python, FastAPI, Uvicorn |
| **AI / Agents** | Anthropic Claude (Opus 4.8 for vision, Sonnet for reasoning/research, Haiku for structured formatting), Claude web search tool, JSON Schema structured outputs |
| **Database** | AWS RDS (PostgreSQL), `psycopg2` |
| **Object storage** | AWS S3 (`boto3`), presigned URLs for private-bucket image delivery |
| **External data** | Open Food Facts public API (grocery product photo lookup) |
| **Hardware / IoT** | Raspberry Pi, Camera Module (`picamera2`), Sense HAT |
| **Auth / config** | IAM-scoped AWS credentials, environment-based secrets (`python-dotenv`) |

---

## The Agent Pipeline

The core of the backend isn't a single LLM call — it's four agents with distinct, narrow responsibilities, each using **structured JSON Schema outputs** so agents can reliably hand data to one another without brittle text parsing:

| Agent | Model | Job |
|---|---|---|
| `image_analyze` | Claude Opus 4.8 (vision) | Detects every edible food/drink item in the photo with a confidence score and estimated count. Explicitly instructed to *exclude* non-food items rather than refuse the whole image. |
| `reflect` | Claude Sonnet | Independently re-examines the same image against the first agent's output — catches hallucinated items, missed items, and misclassified non-food items. Runs in a **retry loop (up to 3 passes)** until it accepts the analysis. |
| `reason` | Claude Sonnet | Looks at the **full inventory history** (not just the current scan) to determine what's trending low or missing, and decides what should be restocked. |
| `shop` | Claude Sonnet + web search tool → Claude Haiku (formatting) | Performs a real, domain-restricted web search per item to find a store and price, then a second pass formats the findings into strict schema — required to copy URLs **verbatim** from search results, never invent one. |

Deduplication of detected items is done in **application code** (a `set`, case-insensitive) rather than trusted to the model — a deliberate choice to keep correctness guarantees out of the LLM's hands where a simpler, deterministic tool exists.

---

## What I Learned

This project was as much about backend/infrastructure fundamentals as it was about AI.

### AWS RDS + S3
- Provisioned and connected to a real PostgreSQL instance on **AWS RDS**, including working through public-access networking (VPC security groups, public accessibility) and authentication (IAM vs. plain password auth) from scratch.
- Designed a schema around **time-series history rather than latest-state-only** (`inventory_items` keeps every scan, not just the newest) specifically because a downstream agent needed to reason over trends — a concrete example of a data-modeling decision driven by a consumer's actual query pattern.
- Used **S3 for object storage** with a private bucket + **presigned URLs**, rather than public objects — trading a small amount of complexity (URLs expire, must be regenerated per request) for meaningfully better default security.
- Wrote **retention/cleanup logic** (parameterized `DELETE ... WHERE scanned_at < now() - interval`) to keep the operational dataset bounded instead of growing forever.

### Backend Architecture & System Design
- Designed a **single ingestion endpoint** shared by two very different clients (an IoT device and a mobile app) instead of duplicating logic per source — a small decision that significantly simplified the whole system.
- Learned the practical difference between **sync and async** in a FastAPI service: blocking calls (Postgres via `psycopg2`, `boto3`, the `requests`-based Anthropic/Open Food Facts calls) will stall the entire event loop if awaited directly, so all of them are offloaded via `run_in_threadpool` to keep the API responsive under concurrent load.
- Split **cache vs. persistence** correctly for different data shapes — e.g., recognizing that a "latest shopping list" doesn't need historical storage the way inventory does, and that an in-memory flag is the right tool for an ephemeral "scan requested" signal versus a durable database row.
- Used **all SQL parameterized** (`%(name)s` placeholders, never string interpolation) as a default habit, not an afterthought — closing off SQL injection by construction.
- Practiced **schema evolution on a live database** — learning the hard way that `CREATE TABLE IF NOT EXISTS` does not add columns to an existing table, and that real migrations need explicit `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.

### React Native + Expo
- Built a multi-screen app with **Expo Router's file-based routing** and a tab navigator, including camera and photo-library integration (`expo-image-picker`) with proper runtime permission handling.
- Learned the **Expo Go vs. custom dev client** tradeoff the hard way: started on a bleeding-edge SDK that outran Expo Go's supported version, hit the Apple Developer Program paywall trying to build a native dev client, and made a pragmatic call to downgrade the whole dependency tree to a supported SDK rather than pay for infrastructure a side project didn't need yet.
- Implemented **polling and focus-based refetching** (`useFocusEffect`) to keep screens in sync with server-side state that changes asynchronously and out-of-band — e.g. showing a loading state on the home screen that only clears once the Raspberry Pi's scan has actually landed in the database, not just when the request was accepted.

### Agentic Workflow Design
- Learned to treat **structured outputs (JSON Schema) as the contract** between agents instead of parsing free-form text — this made a 4-agent pipeline reliable enough to run unattended.
- Designed a **self-correcting loop** (analyze → independent review → retry) as a cheap quality gate, rather than trusting a single model pass for a task (vision + counting) that's genuinely error-prone.
- Learned to **ground LLM output in real data** rather than trained knowledge — forcing the shopping agent to use a live web-search tool restricted to an allowlist of real retailer domains, and to copy source URLs verbatim instead of ever generating one, closes off a whole class of hallucination.
- Practiced **model tiering for cost/latency** — using the most capable (and expensive) model only for the hardest task (vision), and cheaper/faster models for structured reformatting and research where they're just as reliable.
- Iterated on prompt design against real failure modes (e.g., an over-eager "reject non-food images" instruction that caused the model to refuse entire valid scans) — a concrete lesson that prompt wording has to be tested against edge cases, not just the happy path.

### Also Relevant
- **IAM least-privilege**: scoped the backend's AWS credentials to only the S3 permissions it needs, rather than a broad/admin key — and confirmed the boundary by deliberately testing that those credentials *can't* read RDS metadata.
- **Debugging across the full stack** — diagnosed issues spanning DNS/networking (RDS public access, security groups), native toolchains (Xcode/Swift version mismatches blocking native builds), and application logic (a data-shape bug in a JSON schema causing silent API rejections) — all real production-style debugging, not just "fix the failing test."
- **Secrets hygiene** — all credentials (API keys, DB password, AWS keys) live in a git-ignored `.env`, never hardcoded or committed.

---

## Getting Started

### Prerequisites
- Node.js + npm
- Python 3.11+
- An Anthropic API key
- An AWS account (RDS PostgreSQL instance + S3 bucket)

### Backend

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn anthropic psycopg2-binary boto3 python-dotenv requests python-multipart

# create server/.env with:
# ANTHROPIC_API_KEY=...
# DB_HOST=... DB_PORT=5432 DB_NAME=... DB_USER=... DB_PASSWORD=...
# AWS_REGION=... S3_BUCKET=... AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...

uvicorn server:app --host 0.0.0.0 --port 8000
```

### Mobile app

```bash
npm install

# create .env in the project root with:
# EXPO_PUBLIC_SERVER_URL=http://<your-backend-ip>:8000

npx expo start
```
Scan the QR code with **Expo Go** (SDK 54).

### Raspberry Pi (optional)
Requires a Pi Camera Module and a Sense HAT. See `server/raspberry_example.py` — it polls the backend for a scan request, captures a photo, and posts it to the same `/manualscan` endpoint the app uses.

---

## Project Structure

```
├── src/app/
│   ├── (tabs)/
│   │   ├── index.tsx       # Home — current inventory
│   │   ├── Shop.tsx        # AI-recommended shopping list
│   │   └── Scans.tsx       # Scan history (photos)
│   └── components/
│       ├── ReportCard.tsx      # Inventory item card
│       ├── ShopList.tsx        # Shopping item card
│       └── ScannedImage.tsx    # Scan photo card
└── server/
    ├── server.py    # FastAPI app, routes, S3 upload
    ├── agents.py    # Claude agent pipeline (analyze/reflect/reason/shop)
    ├── db.py        # PostgreSQL access layer
    └── raspberry_example.py   # Pi capture-and-poll script
```

---

## Future Plans
- Migrate raw SQL to an ORM (SQLModel) + Alembic migrations as the schema grows
- Add a `scans` → `inventory` foreign key so a photo and its detected items are explicitly linked
- Move the in-memory "latest shopping list" cache to durable storage for multi-instance deployment
- Containerize the backend with docker for deployment beyond local development
