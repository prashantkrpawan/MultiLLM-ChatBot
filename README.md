# Multi-Model AI Chat

> Ask once. Compare responses from three free AI models side by side.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?style=flat-square&logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

---

## What it does

Type a single prompt and instantly compare responses from three AI providers running **concurrently**:

| # | Provider | Model | Free Tier |
|---|---|---|---|
| 1 | **Mistral AI** | `mistral-small-latest` | Rate-limited, no credit card |
| 2 | **Google Gemini** | `gemini-3.1-flash-lite` | 1,500 req/day, no credit card |
| 3 | **OpenRouter** | `nvidia/nemotron-3-ultra-550b-a55b:free` | Free models, no credit card |

All three requests fire simultaneously via `asyncio.gather()` — no waiting for one before starting another.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ · FastAPI · httpx (async) |
| Frontend | Vanilla HTML5 · CSS3 · ES Modules (no framework) |
| Markdown | marked.js · DOMPurify (via CDN) |
| Deployment | FastAPI serves the static frontend |

---

## Quick Start

### Step 1 — Get your free API keys

All three providers are free, no credit card needed.

#### 🟠 Mistral AI
1. Go to **[console.mistral.ai](https://console.mistral.ai)**
2. Sign up with email → verify email
3. Navigate to **API Keys** → **Create new key**
4. Copy the key (starts with a random string)

#### 🔵 Google Gemini
1. Go to **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**
2. Sign in with your Google account
3. Click **"Create API key"** → select any project
4. Copy the key (starts with `AIza...`)

#### 🟢 OpenRouter
1. Go to **[openrouter.ai](https://openrouter.ai)** → click **Sign In**
2. Sign up with email
3. Go to **[openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)**
4. Click **"Create Key"** → copy the key (starts with `sk-or-v1-...`)

---

### Step 2 — Configure environment

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in your three keys:

```env
MISTRAL_API_KEY=your_mistral_key_here
GEMINI_API_KEY=your_gemini_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

---

### Step 3 — Install & run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser.

> **Tip:** If you get `Address already in use`, run:
> ```bash
> lsof -ti :8000 | xargs kill -9
> ```

---

## Development

```bash
cd backend && source .venv/bin/activate

# Start server with auto-reload
python run.py

# Run test suite (16 tests, all mocked — no real API calls)
python -m pytest tests/ -v
```

---

## Docker

```bash
cp backend/.env.example backend/.env
# Fill in your API keys, then:
docker compose up --build
```

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/routes/chat.py         # POST /api/chat · /regenerate/{id} · /health · /providers
│   │   ├── providers/
│   │   │   ├── base.py                # Abstract LLMProvider (timing, error normalisation)
│   │   │   ├── mistral.py             # Mistral AI adapter
│   │   │   ├── gemini.py              # Google Gemini adapter (OpenAI-compat endpoint)
│   │   │   └── openrouter.py          # OpenRouter adapter
│   │   ├── services/chat_service.py   # asyncio.gather() orchestration
│   │   ├── middleware/rate_limit.py   # In-memory sliding-window rate limiter
│   │   ├── schemas/chat.py            # Pydantic request/response models
│   │   ├── config.py                  # pydantic-settings env config
│   │   └── main.py                    # FastAPI app factory
│   ├── tests/                         # 16 tests (respx mocks, zero real HTTP)
│   ├── pyproject.toml                 # pytest config
│   ├── requirements.txt
│   └── run.py                         # Uvicorn entry point
├── frontend/
│   ├── index.html                     # Semantic HTML5, a11y, SEO meta
│   ├── css/
│   │   ├── variables.css              # Design tokens (colours, spacing, typography)
│   │   ├── layout.css                 # 3 → 2 → 1 column responsive grid
│   │   └── components.css             # Cards, skeletons, markdown, toasts
│   └── js/
│       ├── app.js                     # Entry point — event wiring, submit flow
│       ├── api.js                     # fetch() wrappers
│       ├── ui.js                      # DOM + markdown rendering
│       └── state.js                   # Reactive state singleton
├── Dockerfile
├── docker-compose.yml
└── Product-Requirements-Document.md
```

---

## API Reference

| Endpoint | Method | Body | Description |
|---|---|---|---|
| `/api/health` | GET | — | Health check |
| `/api/providers` | GET | — | List providers + enabled status |
| `/api/chat` | POST | `{message, attachment?, attachment_mime?}` | Run all providers concurrently |
| `/api/chat/regenerate/{id}` | POST | `{message, attachment?, attachment_mime?}` | Re-run one provider |
| `/api/docs` | GET | — | Swagger UI |

---

## Adding a new provider

1. Create `backend/app/providers/myprovider.py` extending `LLMProvider`
2. Implement `_call_api()` — return the response text as a string
3. Add the provider to `_build_providers()` in `chat_service.py`
4. Add `MYPROVIDER_API_KEY` / `MYPROVIDER_MODEL` to `config.py` and `.env.example`
5. Add an entry to `PROVIDER_META` in `frontend/js/ui.js`

---

## Rate limiting

- Default: **5 requests / 60 seconds** per IP
- Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` in `.env`
- In-memory sliding window — no Redis or external service needed

---

## Security

- API keys live in `.env` — **never sent to the browser**
- Uploaded images validated by MIME type + size (max 10 MB)
- Markdown output sanitised with DOMPurify before rendering
- All provider requests have a configurable timeout (default 30 s)
- `.env` is in `.gitignore` — won't be committed accidentally
