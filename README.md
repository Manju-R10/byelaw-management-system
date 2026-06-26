# Cooperative Society Bye-law Digitization & Clause Management System

A production-grade, government-oriented web application that digitizes Cooperative
Society bye-law documents: secure upload, automated clause-level extraction,
review/correction, full-text search, an approval workflow and version management.

Built for the **Centre for Development of Imaging Technology (C-DIT)**, Government of
Kerala, per the uploaded Functional Requirements Specification (FRS v1.0, FR-01…FR-10).

---

## Technology stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13 · **FastAPI** (async) · SQLAlchemy 2.0 (async + sync) · Alembic |
| Database | **MySQL 8** (InnoDB, utf8mb4) |
| Auth | JWT (python-jose) · bcrypt · refresh-token rotation (hashed at rest) |
| Parsing/Export | python-docx · pdfplumber/pypdf · reportlab |
| Frontend | **React 18 + Vite 5** · Bootstrap 5 · Bootstrap Icons · react-toastify · axios |

## Repository layout

```
byelaw_management_system/
├── backend/
│   ├── app/
│   │   ├── core/          # security, logging, exceptions, dependencies, file storage, extraction rules
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic DTOs
│   │   ├── repositories/  # data-access layer
│   │   ├── services/      # business logic
│   │   ├── api/v1/        # versioned REST routers
│   │   ├── config.py · database.py · main.py
│   ├── alembic/           # migrations
│   ├── create_db.py · seed.py · requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/           # axios client + endpoint modules
│   │   ├── context/       # AuthContext
│   │   ├── components/    # layout, ui, clauses, workflow, ErrorBoundary
│   │   ├── hooks/         # usePagedList, useDebounce
│   │   ├── pages/         # login, dashboard, users, roles, byelaws, search, approvals, notifications, profile, settings
│   │   ├── routes/ · config/ · utils/
│   ├── package.json · vite.config.js · .env.example
└── README.md
```

---

## Prerequisites

- Python 3.11+ (tested on 3.13)
- Node.js 18+ (tested on 22) and npm
- MySQL 8.x running locally or reachable over the network

## 1. Backend setup

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/../.env` (project root) — see the keys below — then:

```bash
python create_db.py        # creates the database if missing
python -m alembic upgrade head   # applies all migrations
python seed.py             # seeds roles, permissions and default users
uvicorn app.main:app --host 127.0.0.1 --port 8000   # add --reload for dev
```

Interactive API docs: <http://127.0.0.1:8000/docs> · Health: `/health`.

### Environment (`.env` at project root)

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=byelaw_db

JWT_SECRET_KEY=change-me-to-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

UPLOAD_DIR=/absolute/path/to/uploads
MAX_UPLOAD_SIZE_MB=25
ALLOWED_UPLOAD_EXTENSIONS=pdf,doc,docx

ENV=development
LOG_LEVEL=INFO
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Default seeded users

| Username | Password | Role |
|----------|----------|------|
| admin | AdminPassword123 | Administrator |
| operator | OperatorPassword123 | Data Entry Operator |
| verifier | VerifierPassword123 | Verifying Officer |
| viewer | ViewerPassword123 | Viewer |

> Change these credentials before any real deployment.

## 2. Frontend setup

```bash
cd frontend
cp .env.example .env        # set VITE_API_BASE_URL if the backend is elsewhere
npm install
npm run dev                 # http://localhost:5173
```

Production bundle:

```bash
npm run build               # outputs to frontend/dist
npm run preview             # serve the built bundle locally
```

---

## Features

- **Authentication & RBAC** (FR-01): JWT login, refresh-token rotation, logout,
  granular permission-based access enforced on every endpoint and in the UI.
- **User & Role management** (§2.3): CRUD with search/filter/pagination, permission
  assignment, last-admin and system-role safeguards.
- **Upload & validation** (FR-02/03): PDF/DOC/DOCX intake, size/type/duplicate checks,
  structured storage, readability validation.
- **Extraction engine** (FR-04/05/06): configurable, Malayalam-aware numbering rules;
  DOCX + PDF parsing; hierarchy construction with anomaly flagging; transactional
  persistence of Head + clause records.
- **Review & correction** (FR-07): editable clause tree — add/edit/delete, move,
  indent/outdent (re-parent), mark reviewed.
- **Search** (FR-08): MySQL full-text clause search with snippets/highlighting plus
  bye-law metadata search.
- **Approval workflow** (FR-07): Draft → Submitted → Under Review → Verified → Approved
  → Published, with reject/return paths, history and notifications.
- **Version management** (FR-09): one active version per society, full version history.

## Production deployment notes

- Serve the backend behind a TLS-terminating reverse proxy (nginx) with HTTPS; run
  uvicorn under a process manager (e.g. `uvicorn` workers via `gunicorn -k uvicorn.workers.UvicornWorker`).
- Set a strong, secret `JWT_SECRET_KEY`; rotate periodically. Restrict `BACKEND_CORS_ORIGINS`
  to the deployed frontend origin only.
- Build the frontend (`npm run build`) and serve `dist/` as static files (nginx/CDN);
  point `VITE_API_BASE_URL` at the public API URL at build time.
- Put the MySQL `UPLOAD_DIR` on durable storage with backups; scan uploads with AV in
  hardened environments. Keep DB migrations under Alembic.
- Consider running the extraction engine as an async worker if upload volume grows
  (the engine is already isolated from the web layer).
```
