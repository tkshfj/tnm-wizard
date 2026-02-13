# TNM Wizard

A small intranet web application that converts structured input choices into standardized synoptic cancer pathology diagnostic paragraphs, in line with the Japanese General Rules for Clinical and Pathological Study of Cancer. Accessed from any client via a web browser.

## Tech Stack

- **Backend:** Python (FastAPI, Jinja2, PyYAML)
- **Frontend:** Tailwind CSS 3 + DaisyUI 4, TypeScript
- **Server:** Uvicorn

## Project Structure

```
app.py                  # FastAPI application
config/                 # YAML organ configs (e.g. lung.yaml)
templates/
  index.html            # Organ selection page
  form_generic.html     # Data entry form (Jinja2 macros)
  result.html           # Generated report display
  lung_report.j2        # Lung-specific report template
static-src/
  app.css               # Tailwind directives + custom rules
  visibility.ts         # Form field visibility / histologic mix logic
  copy.ts               # Clipboard copy handler
  dom.ts                # DOM query helpers
static/                 # Built assets (output.css, *.js)
tests/                  # Pytest unit tests
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
```

## Build

```bash
npm run build          # builds CSS (Tailwind) and JS (TypeScript)
npm run css:build      # Tailwind only
npm run ts:build       # TypeScript only
```

## Run

```bash
uvicorn app:app --reload
# Open http://localhost:8000
```

### Running behind a reverse proxy

When deploying behind nginx at a subpath (e.g. `/tnm-wizard/`), use the `--root-path` flag so that all generated URLs include the prefix:

```bash
uvicorn app:app --root-path /tnm-wizard
```

### Production deployment

The app runs on a Raspberry Pi behind an nginx reverse proxy at `/tnm-wizard/`.

| Component | Detail |
|---|---|
| App directory | `/opt/tnm-wizard` |
| Systemd service | `tnm-wizard.service` (runs as `app` user) |
| Internal address | `127.0.0.1:8000` |
| nginx config | `/etc/nginx/sites-available/pathology-apps` |

```bash
# Service management
sudo systemctl status tnm-wizard
sudo systemctl restart tnm-wizard
sudo journalctl -u tnm-wizard -f
```

### Deploying changes

A git alias pushes to remote and syncs to the deployed instance in one step:

```bash
git deploy    # pushes, rsyncs to /opt/tnm-wizard, restarts service
```

## Test

```bash
python -m pytest tests/ -v
```

## License

MIT
