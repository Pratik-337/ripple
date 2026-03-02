# Ripple — Change Impact Analyzer

> Know exactly what breaks before you merge.

Ripple is a change governance platform that automatically maps the blast radius of every code change across your codebase. Submit a change, see every component and contributor affected, get acknowledgements, then merge with confidence.

---

## What Ripple Does

When a developer modifies a function signature, updates a shared type, or refactors a module, Ripple:

1. **Analyzes** — runs Tree-sitter parsing to detect every file that imports the changed symbols, then runs an LLM (Deepseek-Coder) to catch semantic coupling the parser can't see
2. **Notifies** — sends personalized impact reports to every affected contributor, scoped to exactly their code
3. **Governs** — gates the merge behind contributor acknowledgements based on the project's strictness mode

---

## The Three Pillars

| Pillar | What it does |
|---|---|
| **Analyze** | Hybrid parser + LLM impact detection at the line level |
| **Notify** | Personalized per-contributor impact reports |
| **Merge** | Strictness-gated approval with full audit trail |

---

## Strictness Modes

| Mode | Behavior |
|---|---|
| **Visibility** | Maps impact and notifies. Owner can merge anytime. |
| **Soft Enforcement** | Nudges contributors. Auto-confirms after 24h if no response. |
| **Full Governance** | Hard blocks merge until all contributors acknowledge. |

---

## Tech Stack

### Frontend
| Tool | Purpose |
|---|---|
| React + Vite | UI framework |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| Zustand | Auth state management |
| React Query | Server state + caching |
| Monaco Editor | In-browser code editor (diff view + IDE) |
| React Flow | Live dependency graph visualization |
| dagre | Automatic graph layout |

### Backend
| Tool | Purpose |
|---|---|
| FastAPI | REST API + WebSocket server |
| PostgreSQL | Primary database |
| SQLAlchemy (async) | ORM |
| Alembic | Database migrations |
| Redis | Celery broker + WebSocket pub/sub bridge |
| Celery | Async task queue (parsing + LLM jobs) |
| MinIO | S3-compatible local file storage |
| Tree-sitter | Code parsing (TypeScript, JavaScript, Python, Go) |
| Ollama + Deepseek-Coder-7B | LLM semantic impact analysis |

---

## Project Structure

```
d:\Ripple\
├── frontend3\               # Vite + React frontend
│   ├── src\
│   │   ├── components\      # All UI components
│   │   ├── hooks\           # useRippleSocket, custom hooks
│   │   ├── lib\             # api.ts, authStore.ts
│   │   ├── pages\           # Page-level components
│   │   └── store\           # Zustand stores
│   └── .env                 # Frontend environment variables
│
├── backend\                 # FastAPI backend
│   ├── app\
│   │   ├── api\v1\routers\  # All API route handlers
│   │   ├── core\            # config, database, redis, storage, websocket
│   │   ├── models\          # SQLAlchemy ORM models
│   │   ├── schemas\         # Pydantic request/response schemas
│   │   ├── services\        # Business logic
│   │   │   └── impact\      # parser.py + llm.py
│   │   ├── tasks\           # Celery tasks (parsing, impact, autoconfirm)
│   │   ├── worker.py        # Celery app definition
│   │   └── main.py          # FastAPI app entry point
│   ├── alembic\             # Database migrations
│   ├── requirements.txt
│   └── .env                 # Backend environment variables
│
└── docker-compose.yml       # PostgreSQL + Redis + MinIO
```

---

## Database Schema

| Table | Purpose |
|---|---|
| `users` | User accounts (email/password + GitHub OAuth) |
| `projects` | Projects with strictness mode and status |
| `components` | Logical groupings of files within a project |
| `component_contributors` | Who owns which component |
| `component_dependencies` | Parser-detected dependency graph edges |
| `project_files` | Source files with S3 keys and parsed symbols (JSONB) |
| `file_drafts` | In-progress edits before impact submission |
| `change_requests` | Submitted changes awaiting review |
| `change_impacts` | Per-contributor impact records with LLM annotations |
| `notifications` | In-app notification feed |
| `invites` | Project/component invitations |
| `refresh_tokens` | JWT refresh token store |
| `project_snapshots` | Before/after snapshots for rollback |
| `snapshot_files` | Individual file versions within a snapshot |

---

## Local Development Setup

### Prerequisites

Install these before starting:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — for PostgreSQL, Redis, MinIO
- [Node.js 18+](https://nodejs.org/) — for the frontend
- [Python 3.11+](https://www.python.org/) — for the backend
- [Ollama](https://ollama.com/download) — for local LLM inference (optional)

### 1. Clone and install

```bash
# Frontend
cd d:\Ripple\frontend3
npm install

# Backend
cd d:\Ripple\backend
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
pip install -r requirements.txt
```

### 2. Environment variables

**`d:\Ripple\backend\.env`**
```env
DATABASE_URL=postgresql+asyncpg://ripple:ripple@localhost:5432/ripple
REDIS_URL=redis://localhost:6379/0
AWS_ACCESS_KEY_ID=ripple
AWS_SECRET_ACCESS_KEY=ripple123
AWS_S3_BUCKET=ripple-files
AWS_ENDPOINT_URL=http://localhost:9000
AWS_REGION=us-east-1
JWT_SECRET=your-64-char-random-string
JWT_REFRESH_SECRET=your-other-64-char-random-string
JWT_EXPIRES_IN=15m
JWT_ISSUER=ripple
JWT_AUDIENCE=ripple-users
GITHUB_CLIENT_ID=your-github-oauth-app-client-id
GITHUB_CLIENT_SECRET=your-github-oauth-app-client-secret
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:6.7b
ALLOWED_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

**`d:\Ripple\frontend3\.env`**
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1/ws
VITE_GITHUB_CLIENT_ID=your-github-oauth-app-client-id
```

Generate JWT secrets:
```powershell
python -c "import secrets; print(secrets.token_hex(32)); print(secrets.token_hex(32))"
```

### 3. GitHub OAuth App

Go to [github.com/settings/developers](https://github.com/settings/developers) → OAuth Apps → New OAuth App:

```
Homepage URL:              http://localhost:3000
Authorization callback URL: http://localhost:3000/auth/callback
```

Copy the Client ID and Client Secret into both `.env` files.

### 4. Run database migrations

```powershell
cd d:\Ripple\backend
.venv\Scripts\activate
alembic upgrade head
```

### 5. Pull the LLM model (optional)

```powershell
ollama pull deepseek-coder:6.7b
```

The app works without Ollama — it falls back to parser-only results automatically.

---

## Running the App

Open **6 terminals** and run one command in each.

| Terminal | Command | Notes |
|---|---|---|
| 1 — Infrastructure | `docker-compose up` | Start from `d:\Ripple\` |
| 2 — FastAPI | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | Activate venv first |
| 3 — Celery Worker | `celery -A app.worker worker --loglevel=info --pool=solo` | `--pool=solo` required on Windows |
| 4 — Celery Beat | `celery -A app.worker beat --loglevel=info` | Scheduled tasks (auto-confirm) |
| 5 — Ollama | `ollama serve` | Skip if not testing LLM |
| 6 — Frontend | `npm run dev` | Run from `d:\Ripple\frontend3\` |

**Activate the venv before every backend terminal:**
```powershell
cd d:\Ripple\backend
.venv\Scripts\activate
```

### Verify everything is running

```
http://localhost:3000       → Ripple frontend
http://localhost:8000/docs  → FastAPI Swagger UI
http://localhost:9001       → MinIO console (ripple / ripple123)
```

---

## API Overview

### Authentication
```
POST /api/v1/auth/register         Register with email + password
POST /api/v1/auth/login            Login, returns access token + sets refresh cookie
GET  /api/v1/auth/me               Validate refresh cookie, return new access token
POST /api/v1/auth/logout           Revoke refresh token
GET  /api/v1/auth/github           Redirect to GitHub OAuth
GET  /api/v1/auth/github/callback  GitHub OAuth callback
```

### Projects
```
POST   /api/v1/projects                    Create project
GET    /api/v1/projects                    List your projects
GET    /api/v1/projects/{id}               Full project detail
PATCH  /api/v1/projects/{id}              Update name/description/strictness
POST   /api/v1/projects/{id}/confirm       Set status → active
DELETE /api/v1/projects/{id}              Archive or delete
```

### Components
```
POST   /api/v1/projects/{id}/components                        Create component
GET    /api/v1/projects/{id}/components                        List components
PATCH  /api/v1/projects/{id}/components/{cid}                  Rename/lock
DELETE /api/v1/projects/{id}/components/{cid}                  Delete
POST   /api/v1/projects/{id}/components/{cid}/contributors     Add contributor
DELETE /api/v1/projects/{id}/components/{cid}/contributors/{uid} Remove
```

### Files
```
POST /api/v1/files/upload-url                      Get presigned S3 upload URLs
POST /api/v1/projects/{id}/files/confirm-batch     Confirm upload, trigger parsing
GET  /api/v1/projects/{id}/files                   List parsed files
POST /api/v1/projects/{id}/files/assign            Assign files to component
GET  /api/v1/files/{id}/content                    Get file content
POST /api/v1/files/{id}/draft                      Save draft (auto-save)
GET  /api/v1/files/{id}/draft                      Load active draft
POST /api/v1/projects/{id}/github-import/preview   Preview GitHub repo file tree
POST /api/v1/projects/{id}/github-import/confirm   Import from GitHub
```

### Changes
```
POST /api/v1/projects/{id}/changes        Submit change for impact analysis
GET  /api/v1/projects/{id}/changes        List project changes
GET  /api/v1/changes/{id}/impact          Full impact detail
POST /api/v1/changes/{id}/acknowledge     Contributor confirms impact
POST /api/v1/changes/{id}/approve         Owner merges
GET  /api/v1/changes?scope=mine           Global changes feed
```

### Notifications & Invites
```
GET  /api/v1/notifications              Paginated notification list
POST /api/v1/notifications/mark-read    Mark read (by ID or all)
POST /api/v1/projects/{id}/invites      Invite contributor by email
POST /api/v1/invites/{id}/accept        Accept invite
POST /api/v1/invites/{id}/decline       Decline invite
GET  /api/v1/invites/pending            Pending invites for current user
GET  /api/v1/users/collaborators        All collaborators across projects
GET  /api/v1/users/search?q=            Search users for assignment
```

---

## WebSocket Events

Connect: `ws://localhost:8000/api/v1/ws/{user_id}?token={access_token}`

| Event | Triggered by | Sent to |
|---|---|---|
| `impact:parser_complete` | Tree-sitter parsing finishes (~2s) | Author + affected contributors |
| `impact:llm_complete` | Ollama analysis finishes (~15-30s) | Author + affected contributors |
| `impact:llm_failed` | Ollama timeout or error | Author |
| `change:approved` | Owner approves merge | All project contributors |
| `change:acknowledged` | Contributor acknowledges | Change author |
| `change:auto_confirmed` | 24h auto-confirm fires | Contributor |
| `component:status_updated` | Any status change | All project contributors |
| `project:files_ready` | Parsing complete after upload | Project owner |
| `notification:new` | Any new notification created | Target user |
| `invite:received` | Invite sent to existing user | Invited user |

---

## How Impact Analysis Works

```
Developer edits file in Monaco IDE
        │
        ▼
Auto-save draft (debounced 2s) → POST /files/{id}/draft
        │
        ▼
Developer clicks "Map Impact"
        │
        ▼
POST /projects/{id}/changes → 202 Accepted
        │
        ├── FastAPI creates change_request (status: pending_analysis)
        ├── Creates "before" snapshot
        └── Enqueues analyze_impact Celery task
                │
                ├── Phase A: Tree-sitter (~2s)
                │   ├── Diffs draft vs stable S3 content
                │   ├── Extracts changed symbol names
                │   ├── Finds all files importing those symbols
                │   ├── Maps files → components → contributors
                │   ├── Creates change_impact rows
                │   └── Publishes impact:parser_complete via Redis → WebSocket
                │
                └── Phase B: Ollama (~15-30s)
                    ├── Sends diff + context to Deepseek-Coder-7B
                    ├── Gets semantic coupling annotations
                    ├── Updates change_impact rows with llm_annotation
                    └── Publishes impact:llm_complete via Redis → WebSocket
```

---

## Parsed Languages

| Language | Extensions | What's extracted |
|---|---|---|
| TypeScript | `.ts` `.tsx` | imports, exports, function/class definitions, call sites |
| JavaScript | `.js` `.jsx` | imports (ESM + CommonJS), exports, definitions |
| Python | `.py` | import/from statements, top-level definitions, `__all__` |
| Go | `.go` | import specs, exported (uppercase) functions and types |
| Rust | `.rs` | use declarations, pub functions/structs/enums |
| Java | `.java` | import declarations, public methods and classes |
| C/C++ | `.c` `.cpp` `.h` `.hpp` | `#include` directives, non-static top-level definitions |
| Ruby | `.rb` | require/include statements, public methods |
| C# | `.cs` | using directives, public members |
| PHP | `.php` | require/use statements, public functions and classes |

---

## Architecture Decisions

**Why Redis?**
Three reasons: (1) Celery task broker — queues parsing jobs between FastAPI and the worker process. (2) WebSocket pub/sub bridge — Celery workers publish events that FastAPI forwards to browser WebSocket connections. (3) Celery result backend — stores task state and results.

**Why not Neo4j?**
The dependency graph is small and bounded (20-50 components max per project). A `component_dependencies` table in PostgreSQL handles all graph queries with simple SQL. No need for a dedicated graph database.

**Why MinIO instead of AWS S3?**
Identical S3-compatible API — every `boto3` call works unchanged. MinIO runs locally in Docker with zero cost and zero cloud account required for development. Switch to real S3 or Cloudflare R2 for production by changing three environment variables.

**Why Celery + Redis instead of async FastAPI tasks?**
Tree-sitter parsing and Ollama inference can take 30+ seconds. Running them inside FastAPI's async event loop would block all other requests. Celery runs them in a completely separate process with proper retry logic, task state tracking, and scheduled tasks (auto-confirm).

**Why Monaco Editor instead of a custom editor?**
Monaco is the VS Code editor engine — it gives syntax highlighting, bracket matching, code folding, multi-cursor, and find/replace for free, across all supported languages, with zero implementation effort. The diff view (MonacoDiffEditor) is also built in.

---

## Shutdown

```powershell
# Stop each terminal with Ctrl+C, then:
docker-compose down    # stops containers, preserves data in volumes
docker-compose down -v # stops containers AND deletes all data
```

---

## Contributing

This is a sprint project (Feb 21 – Mar 6, 2026). Three-person team:

- **Frontend Lead** — React, TypeScript, Monaco, React Flow
- **Frontend Support** — Component wiring, React Query integration  
- **Backend** — FastAPI, SQLAlchemy, Celery, Tree-sitter, Ollama

---

*Built with FastAPI, React, Tree-sitter, and Ollama. Change governance for teams who care about what breaks.*