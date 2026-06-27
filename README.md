# Cooperative Society Bye-law Digitization & Clause Management System

A production-grade, government-oriented web application that digitizes Cooperative
Society bye-law documents end-to-end: secure upload, automated clause-level
extraction, review/correction, full-text search, an approval workflow and version
management.

Built for the **Centre for Development of Imaging Technology (C-DIT)**, Government of
Kerala, per the Functional Requirements Specification (FRS v1.0, FR-01…FR-10).

> Repository: <https://github.com/Manju-R10/byelaw-management-system>

---

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Folder structure](#folder-structure)
- [Prerequisites](#prerequisites)
- [Getting started](#getting-started)
- [Database setup](#database-setup)
- [Backend setup](#backend-setup)
- [Frontend setup](#frontend-setup)
- [Environment variables](#environment-variables)
- [Login credentials](#login-credentials)
- [API documentation (Swagger)](#api-documentation-swagger)
- [Screenshots](#screenshots)
- [Deployment notes](#deployment-notes)
- [License](#license)

---

## Overview

The system allows authorized Cooperative Department staff to upload a bye-law document
(PDF/DOC/DOCX), automatically extract its hierarchical structure (chapters, clauses and
sub-clauses) — including **Malayalam-script** documents — persist it into MySQL as a
master ("Head") record with linked child clause records, review/correct the extraction,
move it through a role-based approval workflow, search clauses full-text, and manage
multiple bye-law versions per society with a single active version at a time.

## Features

- **Authentication & RBAC** (FR-01): JWT login, refresh-token rotation (hashed at rest),
  logout; granular permission-based access enforced on **every endpoint and in the UI**.
- **User & Role management** (FRS §2.3): CRUD with search/filter/pagination, permission
  assignment, last-active-admin and system-role safeguards.
- **Upload & validation** (FR-02/03): PDF/DOC/DOCX intake with size/type/empty/duplicate
  checks, structured on-disk storage, and document-readability validation.
- **Extraction engine** (FR-04/05/06): configurable, **Malayalam-aware** numbering rules;
  DOCX (heading styles + regex) and PDF (pdfplumber) parsing; hierarchy construction with
  numbering-anomaly flagging; transactional persistence of Head + child clause records.
- **Review & correction** (FR-07): editable clause tree — add / edit / delete (with
  sub-tree), move up/down, indent/outdent (re-parent), mark reviewed.
- **Search** (FR-08): MySQL **FULLTEXT** clause search with contextual snippets and
  match highlighting, plus bye-law metadata search.
- **Approval workflow** (FR-07): Draft → Submitted → Under Review → Verified → Approved →
  Published, with reject/return paths, a history timeline and notifications.
- **Version management** (FR-09): exactly one active version per society, full version
  history.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend framework | Python 3.11+ · **FastAPI** (async) |
| ORM / migrations | SQLAlchemy 2.0 (async + sync) · Alembic |
| Database | **MySQL 8** (InnoDB, utf8mb4) |
| Auth & security | JWT (python-jose) · bcrypt · refresh-token rotation |
| Document parsing | python-docx · pdfplumber / pypdf · reportlab |
| Frontend | **React 18 + Vite 8** · Bootstrap 5 · Bootstrap Icons · react-toastify · axios |
| Routing / state | react-router-dom · React Context |

## Folder structure

```
byelaw-management-system/
├── backend/
│   ├── app/
│   │   ├── core/          # security, logging, exceptions, dependencies, file storage, extraction rules
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic DTOs
│   │   ├── repositories/  # data-access layer
│   │   ├── services/      # business logic
│   │   ├── api/v1/        # versioned REST routers
│   │   ├── config.py · database.py · main.py
│   ├── alembic/           # migration environment + versions/
│   ├── create_db.py · seed.py · requirements.txt · alembic.ini
├── frontend/
│   ├── src/
│   │   ├── api/           # axios client + endpoint modules
│   │   ├── context/       # AuthContext
│   │   ├── components/    # layout, ui, clauses, workflow, ErrorBoundary
│   │   ├── hooks/         # usePagedList, useDebounce
│   │   ├── pages/         # login, dashboard, users, roles, byelaws, search, approvals, notifications, profile, settings
│   │   ├── routes/ · config/ · utils/
│   ├── package.json · vite.config.js · .env.example
├── .gitignore
└── README.md
```

## Prerequisites

- **Python** 3.11+ (developed on 3.13)
- **Node.js** 20+ and npm (developed on Node 22)
- **MySQL** 8.x running locally or reachable over the network
- **Git**

## Getting started

```bash
git clone https://github.com/Manju-R10/byelaw-management-system.git
cd byelaw-management-system
```

Then follow **Database setup → Backend setup → Frontend setup** below.

## Database setup

1. Ensure MySQL 8 is running and you have credentials with rights to create a database.
2. Configure the `.env` file at the project root (see [Environment variables](#environment-variables)).
3. From `backend/`, create and migrate the schema, then seed reference data:

```bash
cd backend
python create_db.py              # creates the database (CREATE DATABASE IF NOT EXISTS)
python -m alembic upgrade head   # applies all migrations (tables, indexes, FULLTEXT)
python seed.py                   # seeds roles, permissions and default users
```

The schema includes `users`, `roles`, `permissions`, `role_permissions`, `user_sessions`,
`byelaw_master`, `byelaw_clause` (self-referencing, MEDIUMTEXT clause body + FULLTEXT
index), `byelaw_comments`, `workflow_history`, `upload_history`, `audit_log`, and
`notifications`.

## Backend setup

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    |    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# (run the Database setup steps above the first time)
uvicorn app.main:app --host 127.0.0.1 --port 8000        # add --reload for development
```

Backend runs at <http://127.0.0.1:8000> · health probe at `/health`.

## Frontend setup

```bash
cd frontend
cp .env.example .env          # set VITE_API_BASE_URL if the backend is not on localhost:8000
npm install
npm run dev                   # http://localhost:5173
```

Production bundle:

```bash
npm run build                 # outputs static assets to frontend/dist
npm run preview               # locally serve the built bundle
```

## Environment variables

Create a `.env` file in the **project root** (consumed by the backend; it is gitignored):

```ini
# Database
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=byelaw_db

# Security / JWT
JWT_SECRET_KEY=change-me-to-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# File uploads
UPLOAD_DIR=/absolute/path/to/uploads
MAX_UPLOAD_SIZE_MB=25
ALLOWED_UPLOAD_EXTENSIONS=pdf,doc,docx

# Application
ENV=development
LOG_LEVEL=INFO
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

The frontend reads a single variable from `frontend/.env`:

```ini
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Login credentials

Default accounts created by `seed.py` (development only — **change before deployment**):

| Username | Password | Role |
|----------|----------|------|
| `admin` | `AdminPassword123` | Administrator |
| `operator` | `OperatorPassword123` | Data Entry Operator |
| `verifier` | `VerifierPassword123` | Verifying Officer |
| `viewer` | `ViewerPassword123` | Viewer |

## API documentation (Swagger)

Interactive, auto-generated API documentation is available while the backend is running:

- **Swagger UI** — <http://127.0.0.1:8000/docs>
- **ReDoc** — <http://127.0.0.1:8000/redoc>
- **OpenAPI schema** — <http://127.0.0.1:8000/openapi.json>

All endpoints are under the `/api/v1` prefix (auth, users, roles, permissions, byelaws,
clauses/extraction, search, workflow, notifications). Most require a `Bearer` access
token obtained from `POST /api/v1/auth/login`.

## Screenshots

> Add image files under `docs/screenshots/` and they will render here.

| Screen | Preview |
|--------|---------|
| Login | `docs/screenshots/login.png` |
| Dashboard | `docs/screenshots/dashboard.png` |
| Bye-law detail · clause tree | `docs/screenshots/byelaw-detail.png` |
| Search results | `docs/screenshots/search.png` |
| Approval workflow | `docs/screenshots/workflow.png` |

<!-- Example once images are added:
![Login](docs/screenshots/login.png)
![Dashboard](docs/screenshots/dashboard.png)
-->

## Deployment notes

- Serve the backend behind a TLS-terminating reverse proxy (nginx) over HTTPS; run uvicorn
  under a process manager, e.g. `gunicorn -k uvicorn.workers.UvicornWorker app.main:app`.
- Set a strong, secret `JWT_SECRET_KEY` and rotate it periodically. Restrict
  `BACKEND_CORS_ORIGINS` to the deployed frontend origin only.
- Build the frontend (`npm run build`) and serve `dist/` as static files (nginx/CDN);
  set `VITE_API_BASE_URL` to the public API URL at build time.
- Place `UPLOAD_DIR` on durable, backed-up storage; scan uploads with anti-virus in
  hardened environments. Keep all schema changes under Alembic.
- The extraction engine is isolated from the web layer and runs off the event loop; it can
  be promoted to an asynchronous worker if upload volume grows.

## License

Released under the **MIT License** — see [LICENSE](LICENSE).

> This project was developed for C-DIT / the Cooperative Department (classification:
> *Internal / Government Use*). Adjust the license to match your organization's policy
> before public distribution.
