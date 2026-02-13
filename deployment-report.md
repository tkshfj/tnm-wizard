# Comprehensive Deployment Report: Dual Pathology Application Server

## Deploying TNM Wizard and Cytology Reporting System on a Single Intranet Raspberry Pi

---

## 1. Project Overview

### 1.1 Objective

Deploy two pathology web applications — **TNM Wizard** and **Cytology Reporting System** — on a single Raspberry Pi server accessible via a unified URL on an intranet, with nginx path-based routing providing a single entry point for all users.

### 1.2 Target URL Structure

| URL | Purpose |
|---|---|
| `http://192.168.1.121/` | Landing page with links to both apps |
| `http://192.168.1.121/tnm-wizard/` | TNM Wizard application |
| `http://192.168.1.121/cytology/` | Cytology Reporting System application |

### 1.3 Internal Architecture

| Component | Internal Address | Role |
|---|---|---|
| nginx | `0.0.0.0:80` | Reverse proxy, SPA file server, landing page |
| TNM Wizard | `127.0.0.1:8000` | FastAPI + Jinja2 backend |
| Cytology Backend | `127.0.0.1:8001` | FastAPI + async SQLAlchemy backend |
| Cytology Frontend | Served from disk by nginx | React SPA (pre-built static files) |
| PostgreSQL | `127.0.0.1:5432` | Database for Cytology system only |

---

## 2. Application Analysis

### 2.1 TNM Wizard

- **Repository:** https://github.com/tkshfj/tnm-wizard
- **Description:** A small intranet web application that converts structured input choices into standardized synoptic cancer pathology diagnostic paragraphs, in line with the Japanese General Rules for Clinical and Pathological Study of Cancer.
- **License:** MIT

**Tech stack:**

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Jinja2, PyYAML |
| Frontend | Tailwind CSS 3 + DaisyUI 4, TypeScript |
| Server | Uvicorn |
| Database | None (stateless, YAML-based config) |

**Project structure:**

```
tnm-wizard/
├── app.py                  # FastAPI application entry point
├── config/                 # YAML organ configs (e.g. lung.yaml)
├── templates/
│   ├── index.html          # Organ selection page
│   ├── form_generic.html   # Data entry form (Jinja2 macros)
│   ├── result.html         # Generated report display
│   └── lung_report.j2      # Lung-specific report template
├── static-src/
│   ├── app.css             # Tailwind directives + custom rules
│   ├── visibility.ts       # Form field visibility / histologic mix logic
│   ├── copy.ts             # Clipboard copy handler
│   └── dom.ts              # DOM query helpers
├── static/                 # Built assets (output.css, *.js)
├── tests/                  # Pytest unit tests
├── requirements.txt
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

### 2.2 Cytology Reporting System

- **Repository:** https://github.com/tkshfj/cytology-reporting-system
- **Description:** An intranet-based browser-accessible cytology reporting system for managing medical specimen intake, OCR extraction from scanned documents, report generation, and case search. Handles Japanese and English source documents.
- **License:** MIT

**Tech stack:**

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic |
| Frontend | TypeScript, React, Vite, MUI (Material UI), React Router, TanStack Query |
| Database | PostgreSQL |
| Package manager | uv (Python), npm (frontend) |

**Project structure:**

```
cytology-reporting-system/
├── src/app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings via pydantic-settings (.env)
│   ├── database.py          # Async engine + session factory
│   ├── dependencies.py      # DBSession type alias
│   ├── models/              # SQLAlchemy ORM models (6 tables)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── crud/                # Database query logic per entity
│   └── routers/             # FastAPI route handlers per entity
├── frontend/src/
│   ├── api/                 # API client functions (axios)
│   ├── features/            # Feature modules
│   │   ├── cases/           # Case list, search, create, edit, detail
│   │   ├── reports/         # Report create, detail, edit (versioning)
│   │   ├── documents/       # Document upload dialog
│   │   ├── master/          # Clinical lab & hospital master data
│   │   └── dashboard/       # Dashboard with quick-access links
│   ├── components/          # Shared components (Layout, DocumentViewer, etc.)
│   ├── types/               # TypeScript interfaces
│   └── App.tsx              # Root component with routing
├── alembic/                 # Database migration scripts
├── alembic.ini
├── .env.example
├── pyproject.toml
└── uv.lock
```

**Database schema (6 tables managed via Alembic):**

| Table | Purpose |
|---|---|
| `clinical_labs` | Clinical laboratory master data (name, name_kana, address, phone) |
| `hospitals` | Hospital master data (hospital_id, hospital_name, name_kana, address, phone) |
| `cases` | Case records with embedded patient data (patient_name, patient_id_str, date_of_birth, sex, age, accession_number, specimen_name, clinical_diagnosis, collection_date, examination_date, screening_result). Composite unique constraint on (clinical_lab_id, accession_number). |
| `reports` | One report per case, links case to its report versions |
| `report_versions` | Immutable version rows (version_number auto-increments per report; stores interpretation_category, cytologic_findings, comments, created_by) |
| `scanned_documents` | Uploaded document metadata (document_type, original/stored filenames, file_path, content_type, file_size) |

**API endpoints (all under `/api/v1/`):**

| Resource | Endpoints |
|---|---|
| Clinical Labs | `GET /clinical-labs/`, `GET /{id}`, `POST /`, `PATCH /{id}`, `DELETE /{id}` |
| Hospitals | `GET /hospitals/`, `GET /{id}`, `POST /`, `PATCH /{id}`, `DELETE /{id}` |
| Cases | `GET /cases/`, `GET /cases/search`, `GET /{id}`, `POST /`, `PATCH /{id}`, `DELETE /{id}` |
| Reports | `GET /reports/`, `GET /{id}`, `POST /`, `DELETE /{id}`, `POST /{id}/versions`, `GET /{id}/versions/{num}` |
| Documents | `GET /documents/`, `GET /{id}`, `POST /documents/upload`, `GET /{id}/file`, `DELETE /{id}` |
| Health | `GET /health` |

**Implementation status:**

| Requirement | Status |
|---|---|
| R-001 Intake | Implemented |
| R-002 Report issuance | Implemented |
| R-003 Minimum input fields | Implemented |
| R-004 Bilingual documents | Implemented |
| R-005 Scan image acquisition | Implemented |
| R-006 OCR and extraction | **Not implemented** |
| R-007 Database persistence | Implemented |
| R-008 Post-OCR file handling | **Not implemented** (depends on R-006) |
| R-009 File path registration | Implemented |
| R-010 Document display | Implemented |
| R-011 Report creation screen | Implemented |
| R-012 Final interpretation | Implemented |
| R-013 Report versioning | Implemented |
| R-014 Formal report output (PDF/DOCX) | **Not implemented** |
| R-015 Printer output | **Not implemented** |
| R-016 Search criteria | Implemented |
| R-017 Backend technology | Implemented |
| R-018 Frontend technology | Implemented |

---

## 3. Hardware Considerations

### 3.1 Raspberry Pi 4 (8GB) vs Raspberry Pi 5 (16GB)

| Specification | Pi 4 (8GB) | Pi 5 (16GB) |
|---|---|---|
| CPU | Cortex-A72 (1.5 GHz) | Cortex-A76 (2.4 GHz) |
| RAM | 8 GB | 16 GB |
| Storage interface | USB 3.0 SSD (external enclosure) | Native PCIe 2.0 x1 via M.2 HAT (NVMe) |
| Approximate throughput gain | Baseline | ~2× for Python/Node workloads |
| Cytology backend workers | 2 | 3–4 |
| PostgreSQL shared_buffers | 256 MB | 2 GB |
| Future OCR workloads | Tight | Comfortable |
| NVMe boot | Not native | Supported via `raspi-config` |

### 3.2 Recommended Configuration

| Component | Recommendation |
|---|---|
| Board | Raspberry Pi 5, 16GB |
| Storage | M.2 NVMe SSD via official Pi 5 M.2 HAT; boot OS from NVMe |
| Network | Ethernet (not WiFi) for reliability |
| OS | Raspberry Pi OS 64-bit (Bookworm) |
| IP | Static: `192.168.1.121` |

### 3.3 Pi 5 NVMe Boot Setup

Boot from NVMe so all data (OS, apps, PostgreSQL) lives on fast storage:

```bash
sudo raspi-config
# Advanced Options → Boot Order → NVMe/USB Boot
# Flash Pi OS directly to the NVMe SSD using Raspberry Pi Imager
```

### 3.4 PostgreSQL Tuning by Hardware

**Pi 4 (8GB)** — `/etc/postgresql/*/main/postgresql.conf`:

```ini
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 8MB
```

**Pi 5 (16GB)** — `/etc/postgresql/*/main/postgresql.conf`:

```ini
shared_buffers = 2GB
effective_cache_size = 8GB
work_mem = 32MB
maintenance_work_mem = 256MB
```

---

## 4. Codebase Refactoring

Both applications must be refactored to work under path prefixes (`/tnm-wizard/` and `/cytology/`) instead of running at the URL root.

### 4.1 Files Requiring Revision — TNM Wizard

| File | Change | Reason |
|---|---|---|
| `templates/index.html` | Replace all hardcoded `href="/"`, `href="/..."`, and `src="/static/..."` with `{{ url_for(...) }}` calls | Links and static assets must resolve under `/tnm-wizard/` prefix |
| `templates/form_generic.html` | Fix `<form action="...">`, `href`, `src` attributes and any Jinja2 macros that generate URLs | Form submissions and asset loads break without prefix |
| `templates/result.html` | Fix navigation links and static asset references | Back/home links would point to `/` instead of `/tnm-wizard/` |
| `templates/lung_report.j2` | Audit for any links or embedded asset references | May need changes if it links to other pages |
| `static-src/copy.ts` | Audit for `fetch()` or `window.location` calls using absolute paths | JS may post to wrong URL |
| `static-src/visibility.ts` | Audit for `fetch()` calls with absolute paths | Same reason |

**Files that do NOT need changes:** `app.py`, `config/*.yaml`, `static-src/dom.ts`, `static-src/app.css`, `requirements.txt`, `package.json`, `tailwind.config.js`, `tsconfig.json`

**How to find all instances requiring changes:**

```bash
cd /opt/tnm-wizard

# Find hardcoded paths in templates
grep -rn 'href="/' templates/
grep -rn 'src="/' templates/
grep -rn 'action="/' templates/
grep -rn 'url_for' templates/

# Find hardcoded paths in TypeScript
grep -rn "fetch('/" static-src/
grep -rn 'fetch("/' static-src/
grep -rn 'window.location' static-src/
```

**Template fix patterns:**

Static file references:
```html
<!-- BEFORE (broken under /tnm-wizard/) -->
<link rel="stylesheet" href="/static/output.css">
<script src="/static/visibility.js"></script>

<!-- AFTER — url_for respects --root-path automatically -->
<link rel="stylesheet" href="{{ url_for('static', path='output.css') }}">
<script src="{{ url_for('static', path='visibility.js') }}"></script>
```

Navigation links:
```html
<!-- BEFORE -->
<a href="/">Home</a>
<form action="/generate" method="post">

<!-- AFTER (option A — url_for, preferred) -->
<a href="{{ url_for('index') }}">Home</a>
<form action="{{ url_for('generate') }}" method="post">

<!-- AFTER (option B — manual prefix) -->
<a href="{{ request.scope['root_path'] }}/">Home</a>
```

JavaScript fetch calls:
```typescript
// BEFORE
fetch('/generate', { method: 'POST', body: formData })

// AFTER — relative URL works because the page is served under /tnm-wizard/
fetch('generate', { method: 'POST', body: formData })
```

After any TypeScript changes: `npm run build`

### 4.2 Files Requiring Revision — Cytology Reporting System

| File | Change | Reason |
|---|---|---|
| `frontend/vite.config.ts` | Add `base: '/cytology/'` and update dev proxy | All built asset paths must include the `/cytology/` prefix |
| `frontend/src/App.tsx` | Add `basename="/cytology"` to `<BrowserRouter>` | Client-side routing must know the prefix |
| `frontend/src/api/*.ts` | Change axios `baseURL` from `/api/v1` to `/cytology/api/v1` | API calls must route through nginx correctly |
| `src/.env` | Create from `.env.example`; set `DATABASE_URL` | Points backend to local PostgreSQL |

**Files that do NOT need changes:** `src/app/main.py`, `src/app/config.py`, `src/app/database.py`, `src/app/routers/*.py`, `src/app/crud/*.py`, `src/app/models/*.py`, `src/app/schemas/*.py`, `frontend/src/features/**/*.tsx`, `frontend/src/components/*.tsx`, `alembic.ini`, `alembic/`, `pyproject.toml`, `uv.lock`

**How to find all instances requiring changes:**

```bash
cd /opt/cytology-reporting-system

grep -rn 'baseURL' frontend/src/
grep -rn "'/api" frontend/src/
grep -rn '"/api' frontend/src/
```

**Detailed code changes:**

**`frontend/vite.config.ts`:**
```typescript
// BEFORE
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})

// AFTER
export default defineConfig({
  base: '/cytology/',
  plugins: [react()],
  server: {
    proxy: {
      '/cytology/api': {
        target: 'http://localhost:8001',
        rewrite: (path) => path.replace(/^\/cytology/, ''),
      },
    },
  },
})
```

**`frontend/src/App.tsx`:**
```tsx
// BEFORE
<BrowserRouter>
  <Routes>
    {/* ... */}
  </Routes>
</BrowserRouter>

// AFTER
<BrowserRouter basename="/cytology">
  <Routes>
    {/* ... */}
  </Routes>
</BrowserRouter>
```

**`frontend/src/api/*.ts` (axios client):**
```typescript
// BEFORE
const api = axios.create({
  baseURL: '/api/v1',
})

// AFTER (option A — hardcoded)
const api = axios.create({
  baseURL: '/cytology/api/v1',
})

// AFTER (option B — Vite environment variable, more flexible)
const api = axios.create({
  baseURL: `${import.meta.env.BASE_URL}api/v1`,
})
```

**`src/.env`:**
```
DATABASE_URL=postgresql+asyncpg://cytology_user:CHANGE_THIS_PASSWORD@localhost:5432/cytology
```

After frontend changes: `cd frontend && npm run build`

---

## 5. Server Setup Procedure

### 5.1 System Package Installation

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y postgresql postgresql-contrib nginx git
```

### 5.2 Node.js 22 LTS

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node --version   # should show v22.x
```

### 5.3 uv (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv --version
```

### 5.4 PostgreSQL Database

```bash
sudo -u postgres createuser --createdb cytology_user
sudo -u postgres psql -c "ALTER USER cytology_user WITH PASSWORD 'CHANGE_THIS_PASSWORD';"
sudo -u postgres createdb -O cytology_user cytology
```

### 5.5 Static IP

Edit `/etc/dhcpcd.conf` (or use NetworkManager on newer Pi OS):

```
interface eth0
static ip_address=192.168.1.121/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

Reboot or restart networking after changes.

---

## 6. Application Deployment

### 6.1 TNM Wizard

```bash
cd /opt
sudo mkdir tnm-wizard && sudo chown $USER:$USER tnm-wizard
git clone https://github.com/tkshfj/tnm-wizard.git /opt/tnm-wizard
cd /opt/tnm-wizard

# Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Node dependencies and build
npm install
npm run build

# Apply template fixes (Section 4.1)
# ... edit templates and static-src as described

# If TypeScript was changed, rebuild
npm run build

# Verify
uvicorn app:app --host 127.0.0.1 --port 8000 --root-path /tnm-wizard
# Test at http://192.168.1.121:8000/tnm-wizard/
# Ctrl+C to stop
```

### 6.2 Cytology Reporting System

```bash
cd /opt
sudo mkdir cytology-reporting-system && sudo chown $USER:$USER cytology-reporting-system
git clone https://github.com/tkshfj/cytology-reporting-system.git /opt/cytology-reporting-system
cd /opt/cytology-reporting-system

# Configure environment
cp .env.example src/.env
# Edit src/.env → DATABASE_URL=postgresql+asyncpg://cytology_user:CHANGE_THIS_PASSWORD@localhost:5432/cytology

# Apply frontend refactoring (Section 4.2)
# ... edit vite.config.ts, App.tsx, api client

# Backend: install dependencies and run migrations
uv sync
uv run alembic upgrade head

# Frontend: install and build
cd frontend
npm install
npm run build
cd ..

# Verify
uv run uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8001 --root-path /cytology
# Test at http://192.168.1.121:8001/cytology/api/v1/health
# Ctrl+C to stop
```

---

## 7. Systemd Service Configuration

### 7.1 TNM Wizard — `/etc/systemd/system/tnm-wizard.service`

```ini
[Unit]
Description=TNM Wizard
After=network.target

[Service]
User=pi
WorkingDirectory=/opt/tnm-wizard
ExecStart=/opt/tnm-wizard/.venv/bin/uvicorn app:app \
    --host 127.0.0.1 \
    --port 8000 \
    --root-path /tnm-wizard
Restart=always
RestartSec=5
Environment=PATH=/opt/tnm-wizard/.venv/bin:/usr/bin

[Install]
WantedBy=multi-user.target
```

### 7.2 Cytology Backend — `/etc/systemd/system/cytology-backend.service`

```ini
[Unit]
Description=Cytology Reporting System Backend
After=network.target postgresql.service

[Service]
User=pi
WorkingDirectory=/opt/cytology-reporting-system
ExecStart=/home/pi/.local/bin/uv run uvicorn app.main:app \
    --app-dir src \
    --host 127.0.0.1 \
    --port 8001 \
    --root-path /cytology \
    --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Note: For Pi 5 (16GB), increase `--workers 2` to `--workers 4`.

### 7.3 Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable tnm-wizard cytology-backend
sudo systemctl start tnm-wizard cytology-backend

# Verify
sudo systemctl status tnm-wizard
sudo systemctl status cytology-backend
```

---

## 8. Nginx Reverse Proxy Configuration

### 8.1 Configuration File — `/etc/nginx/sites-available/pathology-apps`

```nginx
server {
    listen 80;
    server_name _;

    # ── Landing page ──────────────────────────────────
    location = / {
        default_type text/html;
        return 200 '<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pathology Intranet</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
           background: #f8f9fa; color: #333; }
    .container { max-width: 640px; margin: 80px auto; padding: 0 24px; }
    h1 { font-size: 1.8em; margin-bottom: 8px; }
    p.subtitle { color: #666; margin-bottom: 32px; }
    a.card { display: block; padding: 24px; margin-bottom: 16px;
             background: #fff; border: 1px solid #e0e0e0; border-radius: 12px;
             text-decoration: none; color: inherit; transition: box-shadow 0.15s; }
    a.card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
    .card-title { font-size: 1.2em; font-weight: 600; margin-bottom: 4px; }
    .card-desc { font-size: 0.9em; color: #888; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Pathology Intranet</h1>
    <p class="subtitle">192.168.1.121</p>
    <a class="card" href="/tnm-wizard/">
      <div class="card-title">TNM Wizard</div>
      <div class="card-desc">Synoptic cancer pathology diagnostic reports</div>
    </a>
    <a class="card" href="/cytology/">
      <div class="card-title">Cytology Reporting System</div>
      <div class="card-desc">Cytology case management, document intake, and reporting</div>
    </a>
  </div>
</body>
</html>';
    }

    # ── TNM Wizard ────────────────────────────────────
    location /tnm-wizard/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /tnm-wizard;
    }

    # ── Cytology Reporting System ─────────────────────

    # API requests → FastAPI backend on port 8001
    location /cytology/api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /cytology;
        client_max_body_size 50M;
    }

    # Frontend SPA → serve pre-built static files
    location /cytology/ {
        alias /opt/cytology-reporting-system/frontend/dist/;
        try_files $uri $uri/ /cytology/index.html;
    }
}
```

### 8.2 Enable Nginx Configuration

```bash
sudo ln -sf /etc/nginx/sites-available/pathology-apps /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 8.3 How the Routing Works

**TNM Wizard (`/tnm-wizard/`):**
The `proxy_pass http://127.0.0.1:8000/` directive (note the trailing slash) strips the `/tnm-wizard/` prefix before forwarding. So a request to `/tnm-wizard/generate` becomes `/generate` at the backend. The `--root-path /tnm-wizard` flag on Uvicorn tells FastAPI that its true external prefix is `/tnm-wizard`, so `url_for()` in templates generates correct prefixed URLs.

**Cytology API (`/cytology/api/`):**
The `proxy_pass http://127.0.0.1:8001/api/` directive strips `/cytology` and forwards to the backend's `/api/` routes. So `/cytology/api/v1/health` becomes `/api/v1/health` at the backend.

**Cytology Frontend (`/cytology/`):**
The `alias` directive serves pre-built files from `frontend/dist/`. The `try_files` directive with fallback to `/cytology/index.html` ensures that React Router client-side routes (e.g., `/cytology/cases/123`) serve `index.html` instead of returning a 404.

---

## 9. Verification Checklist

After all services are running, test from another machine on the intranet:

| Test | Expected Result | Command |
|---|---|---|
| Landing page | HTML page with two card links | `curl http://192.168.1.121/` |
| TNM Wizard loads | HTML with styles and JS | Open `http://192.168.1.121/tnm-wizard/` in browser |
| TNM Wizard forms work | Form submission returns report | Submit a form in the TNM Wizard UI |
| Cytology SPA loads | React app renders dashboard | Open `http://192.168.1.121/cytology/` in browser |
| Cytology client-side routing | Page renders, no 404 | Navigate to `http://192.168.1.121/cytology/cases` |
| Cytology API health check | JSON response | `curl http://192.168.1.121/cytology/api/v1/health` |
| Cytology case creation | API returns 201 | Create a case through the UI |
| Document upload | File stored, metadata in DB | Upload a scanned document in the UI |

---

## 10. Troubleshooting

### 10.1 Common Errors and Fixes

| Symptom | Likely Cause | Fix |
|---|---|---|
| TNM Wizard loads but no CSS/JS | Templates hardcode `/static/` | Replace with `{{ url_for('static', path='...') }}` in templates |
| TNM Wizard form submits to wrong URL | `<form action="/">` hardcoded | Replace with `{{ url_for('route_name') }}` |
| Cytology SPA shows blank white page | Vite `base` not set to `/cytology/` | Set `base: '/cytology/'` in `vite.config.ts` and rebuild |
| Cytology pages 404 on browser refresh | nginx `try_files` not falling back to `index.html` | Verify the `location /cytology/` block uses `alias` + `try_files` with `/cytology/index.html` fallback |
| Cytology API calls return 404 | Axios `baseURL` still `/api/v1` without prefix | Change to `/cytology/api/v1` in API client and rebuild |
| 502 Bad Gateway | Backend process not running | `sudo systemctl status tnm-wizard` or `sudo systemctl status cytology-backend` |
| Database connection refused | PostgreSQL not started or wrong credentials | Check `src/.env` and run `sudo systemctl status postgresql` |
| `nginx -t` fails with config error | Syntax error in nginx config | Check for mismatched braces or quotes in `/etc/nginx/sites-available/pathology-apps` |
| Cytology migration fails | Database doesn't exist or user lacks permissions | Re-run `createdb` and verify user permissions |
| Static assets load with wrong MIME type | nginx `alias` path incorrect or missing trailing `/` | Verify the `alias` path ends with `/` and matches the actual `dist/` directory |

### 10.2 Diagnostic Commands

```bash
# Check service status
sudo systemctl status tnm-wizard
sudo systemctl status cytology-backend
sudo systemctl status postgresql
sudo systemctl status nginx

# View application logs
sudo journalctl -u tnm-wizard -f
sudo journalctl -u cytology-backend -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Test backend connectivity directly (bypassing nginx)
curl http://127.0.0.1:8000/          # TNM Wizard
curl http://127.0.0.1:8001/api/v1/health  # Cytology

# Test through nginx
curl http://192.168.1.121/tnm-wizard/
curl http://192.168.1.121/cytology/api/v1/health

# Check what's listening on which ports
sudo ss -tlnp | grep -E ':(80|8000|8001|5432)'

# Test PostgreSQL connection
psql -U cytology_user -d cytology -h localhost -c "SELECT 1;"
```

---

## 11. Maintenance Operations

### 11.1 Database Backup

Create `/etc/cron.d/cytology-backup`:

```
0 2 * * * pi pg_dump cytology | gzip > /home/pi/backups/cytology-$(date +\%Y\%m\%d).sql.gz
```

```bash
mkdir -p /home/pi/backups
```

### 11.2 Updating Applications

**TNM Wizard:**
```bash
cd /opt/tnm-wizard
git pull
source .venv/bin/activate
pip install -r requirements.txt
npm run build
sudo systemctl restart tnm-wizard
```

**Cytology System:**
```bash
cd /opt/cytology-reporting-system
git pull
uv sync
uv run alembic upgrade head
cd frontend && npm install && npm run build && cd ..
sudo systemctl restart cytology-backend
```

### 11.3 Service Management

```bash
# Stop both apps
sudo systemctl stop tnm-wizard cytology-backend

# Start both apps
sudo systemctl start tnm-wizard cytology-backend

# Restart after config or code changes
sudo systemctl restart tnm-wizard
sudo systemctl restart cytology-backend

# Restart nginx after config changes
sudo nginx -t && sudo systemctl restart nginx

# Disable auto-start on boot
sudo systemctl disable tnm-wizard cytology-backend
```

### 11.4 Resource Monitoring

```bash
# Real-time process monitoring
htop

# Disk usage
df -h

# PostgreSQL database size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('cytology'));"

# Uploaded document storage size
du -sh /opt/cytology-reporting-system/uploads/ 2>/dev/null || echo "No uploads directory yet"
```

---

## 12. References

| Resource | URL |
|---|---|
| TNM Wizard repository | https://github.com/tkshfj/tnm-wizard |
| Cytology Reporting System repository | https://github.com/tkshfj/cytology-reporting-system |
| FastAPI root_path documentation | https://fastapi.tiangolo.com/advanced/behind-a-proxy/ |
| Vite base option documentation | https://vite.dev/config/shared-options.html#base |
| React Router basename | https://reactrouter.com/en/main/router-components/browser-router |
| nginx reverse proxy guide | https://nginx.org/en/docs/http/ngx_http_proxy_module.html |
| Raspberry Pi 5 NVMe boot | https://www.raspberrypi.com/documentation/computers/raspberry-pi.html |
| uv package manager | https://docs.astral.sh/uv/ |
| Alembic migrations | https://alembic.sqlalchemy.org/ |
| PostgreSQL tuning for small servers | https://pgtune.leopard.in.ua/ |
