# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Dev server (auto-reload)
uvicorn app:app --reload

# Tests
python -m pytest tests/ -v                                    # all tests
python -m pytest tests/test_app.py::TestClassName -v           # one class
python -m pytest tests/test_app.py::TestClassName::test_name -v  # one test

# Build frontend assets (Tailwind CSS + TypeScript → static/)
npm run build        # both CSS and TS
npm run css:build    # CSS only
npm run ts:build     # TS only
```

## Architecture

TNM Wizard is a FastAPI app that generates structured pathology reports from form input. The pipeline:

**YAML config → HTML form → form submission → report template → plain-text report**

### Data flow for adding a new field

1. **`config/{organ}.yaml`** — define the field (name, label, type, options) in a section's `fields` list
2. **`templates/form_generic.html`** — the `render_input()` macro auto-renders standard types (`radio`, `select`, `checkbox`, `number`, `free_text`, `textarea`). Special types (`histologic_mix`, `nodal_stations`) have dedicated blocks.
3. **`app.py`** — `extract_fields()` auto-converts form data to typed Python dict. Special post-processing (histologic summary, nodal summary, stage derivation) happens in the `POST /{organ}/generate` route.
4. **`templates/{organ}_report.j2`** — reference the field as `{{ data.field_name }}` in the Jinja2 report template.

### Key backend functions (app.py)

| Function | Purpose |
|---|---|
| `extract_fields(form, cfg)` | Convert form submission to typed dict (handles checkbox→bool, number→float, etc.) |
| `build_histologic_summary(form_data, cfg)` | Collect histologic_mix rows → formatted text (AD shows subtypes with %, non-AD shows subtype only) |
| `build_nodal_summary(form_data)` | Collect LN station fields → "1R (2/5), 7 (1/3)" format |
| `derive_stage(cfg, pt, pn, pm)` | Look up stage from `tnm_stage_table` (exact match, then wildcard fallback) |

### Frontend (static-src/)

TypeScript in `static-src/` compiles to `static/`. Key client-side logic in `visibility.ts`:
- **`visible_if` toggling**: fields with `data-visible-if-field`/`data-visible-if-values` attributes show/hide based on other field values
- **Histologic mix table**: type→subtype filtering, AD vs non-AD rules (AD requires %, non-AD hides other rows), total % calculation
- **Nodal stations**: checkbox toggles positive/total input visibility

### YAML config structure

```yaml
organ: lung
display_name: "Lung Cancer"
version: "肺癌取扱い規約第9版"
template: "lung_report.j2"

sections:
  - id: section_id
    title: "Section Title"
    fields:
      - name: field_name
        label: "Label"
        type: radio|select|checkbox|number|free_text|textarea|histologic_mix|nodal_stations
        options: [...]          # for radio/select/checkbox
        visible_if:             # optional conditional visibility
          field: other_field
          values: ["val1", "val2"]

tnm_stage_table:
  "T1a,N0,M0": "Stage IA1"
  "T*,N*,M1*": "Stage IVB"     # wildcards supported
```

### Conventions

- Field names use English; UI labels use Japanese
- Medical abbreviations preserved as-is (pT, pN, AD, SQ, STAS, etc.)
- AD (Adenocarcinoma) type code `"AD"` is hardcoded in both frontend and backend for special handling
- All URLs use `url_for()` for reverse proxy compatibility (`--root-path /tnm-wizard`)
- Deployment via `git deploy` alias (push + rsync to Raspberry Pi + restart systemd service)
