# TIQC AI Client Intake & Project Scoping Bot

An intelligent, decoupled discovery chatbot designed for the **Tech Incubator at Queens College (TIQC)**. The system automates prospective client discovery interviews, applies defensive scoping boundaries, and auto-generates a standardized `ProjectBrief` for incubator staff before discovery calls.

---

## Architecture Overview

The system uses a decoupled client-server architecture:

```text
tiqc-intake-bot/
├── .github/workflows/ci.yml       # Automated CI (Python checks + Vite build)
├── backend/                       # FastAPI async application
│   ├── app/
│   │   ├── api/routes/            # Endpoints: /api/chat, /api/brief
│   │   ├── core/                  # Configuration & system prompts
│   │   ├── models/                # Pydantic schemas (ProjectBrief, ChatMessage)
│   │   └── services/              # LLM logic, storage, and delivery pipeline
│   ├── data/deliveries/           # Timestamped local JSON delivery records
│   └── requirements.txt
└── frontend/                      # React (Vite) embeddable widget
    ├── src/                       # App.jsx, chat UI, brief presentation card
    └── package.json
```

## Key Features

* **Adaptive Diagnostic Drill-Downs:** Dynamically branches based on client input (Shopify, WordPress, custom web apps, mobile apps, or URLs) without repetitive questions.
* **Defensive Guardrails:** Strictly maintains intake discovery boundaries—never quotes pricing, guarantees delivery timelines, or makes binding commitments.
* **Standardized Brief Generation:** Translates unstructured transcripts into TIQC service categories (e.g., E-commerce & Transactional Platform, Custom Web App, MVP Build) with flagged technical unknowns for staff discovery calls.
* **Resilient Delivery Pipeline:** Automatically dispatches briefs on completion to local audit storage (`data/deliveries/*.json`) with built-in adapters for Airtable and email.
* **Zero-Token Local Development:** Fully functional out-of-the-box using an intelligent local fallback engine (`LLM_PROVIDER=mock`), allowing new contributors to test without paid API keys.

---

## Getting Started

### Prerequisites

* Python 3.11+
* Node.js 18+ and npm

### 1. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create your local `.env` inside `backend/`:

```bash
cp ../.env.example .env
```

Start the API server:

```bash
uvicorn app.main:app --reload
```

* **API Base:** `http://localhost:8000`
* **Interactive Swagger Docs:** `http://localhost:8000/docs`

### 2. Frontend Setup

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/` in your browser.

---

## Configuration Reference

Key variables in `backend/.env`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `mock` | Switch between mock and openai |
| `OPENAI_API_KEY` | `""` | OpenAI secret key (e.g., sk-...) |
| `OPENAI_MODEL` | `gpt-4o` | Model name for chat and structured parsing |
| `DELIVERY_CHANNELS` | `local` | Active channels: local, airtable, or local,airtable |
| `AIRTABLE_API_KEY` | `""` | Airtable Personal Access Token |
| `AIRTABLE_BASE_ID` | `""` | Target Base ID (app...) |
| `AIRTABLE_TABLE_NAME` | `Intake Submissions` | Target table name |

---

## Modifying the Flow & Schemas

* **Update Discovery Prompts:** Edit `backend/app/core/prompts.py` (`SYSTEM_INTAKE_PROMPT` and `BRIEF_GENERATION_PROMPT`).
* **Update Brief Fields:** Add or adjust fields in `backend/app/models/brief.py` (`ProjectBrief` class).
* **Extend Delivery:** Add new destinations (e.g., HubSpot, Slack) in `backend/app/services/delivery.py` by subclassing `BaseDeliveryHandler`.

---

## Continuous Integration

Every push and pull request to `main` is validated by GitHub Actions (`.github/workflows/ci.yml`):

* Python dependency resolution and FastAPI app import validation.
* Node.js dependency resolution, ESLint checks, and production Vite compilation.