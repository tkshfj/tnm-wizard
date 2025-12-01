from pathlib import Path
import json
import yaml
import re
from typing import Mapping, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"

app = FastAPI(title="TNM Wizard")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


class OrganConfig:
    def __init__(self, cfg: dict):
        self.organ = cfg["organ"]
        self.display_name = cfg.get("display_name", self.organ)
        self.version = cfg.get("version", "")
        self.sections = cfg["sections"]
        self.template_name = cfg["template"]
        # TNM stage table: can be dict or JSON file
        self.stage_table = {}
        tnm = cfg.get("tnm_stage_table")
        if isinstance(tnm, dict):
            self.stage_table = tnm
        elif isinstance(tnm, str):
            # if we later want JSON/YAML files, handle here
            path = CONFIG_DIR / tnm
            if path.suffix == ".json":
                self.stage_table = json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix in (".yaml", ".yml"):
                self.stage_table = yaml.safe_load(path.read_text(encoding="utf-8"))


def load_all_configs():
    configs = {}
    for path in CONFIG_DIR.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        oc = OrganConfig(data)
        configs[oc.organ] = oc
    return configs


FORM_CONFIGS = load_all_configs()


def derive_stage(organ_cfg: OrganConfig, pT: str, pN: str, pM: str) -> str:
    """TNM -> stage lookup with simple wildcard support.
    - Exact match has priority (e.g. 'T1a,N0,M0')
    - If no exact match, try patterns with '*' such as 'T*,N*,M1*'
    """
    t = pT.replace("p", "")
    n = pN.replace("p", "")
    m = pM.replace("p", "")
    key = f"{t},{n},{m}"
    table = organ_cfg.stage_table
    # 1. Exact match
    if key in table:
        return table[key]
    # 2. Wildcard patterns: treat '*' as '.*' in a regex
    for pattern, stage in table.items():
        if "*" not in pattern:
            continue
        # Escape regex special chars except '*', then replace '*' with '.*'
        # Split not strictly necessary here; simple global replace is enough:
        regex_pattern = "^" + re.escape(pattern).replace("\\*", ".*") + "$"
        if re.match(regex_pattern, key):
            return stage
    # 3. Fallback
    return "Stage ?"


def extract_fields(form, organ_cfg: OrganConfig) -> dict:
    data = {}
    for section in organ_cfg.sections:
        for field in section["fields"]:
            name = field["name"]
            ftype = field.get("type")
            has_options = bool(field.get("options"))
            if ftype == "checkbox":
                if has_options:
                    # multi-select
                    value = form.getlist(name)
                else:
                    value = form.get(name) == "true"
            else:
                value = form.get(name)
            if ftype == "number" and value not in (None, "", []):
                try:
                    value = float(value)
                except ValueError:
                    value = None
            data[name] = value
    return data


def build_nodal_summary(form_data: Mapping[str, str]) -> str:
    """
    Parse LNxx_positive / LNxx_total pairs from the form data and build a
    compact summary like: '1R (1/3), 3p (2/4)'.

    Expected field names:
      - LN1R_positive, LN1R_total
      - LN1L_positive, LN1L_total
      - LN2R_positive, LN2R_total
      - ...
    and so on, for all stations defined in lung.yaml.
    """
    summary_parts = []

    POS_SUFFIX = "_positive"
    TOTAL_SUFFIX = "_total"

    for key, pos_val in form_data.items():
        # Only keys ending with "_positive" are of interest
        if not key.endswith(POS_SUFFIX):
            continue

        pos_val = (pos_val or "").strip()
        if pos_val == "":
            # nothing entered, skip
            continue

        base = key[:-len(POS_SUFFIX)]  # e.g. "LN1R" from "LN1R_positive"
        total_key = f"{base}{TOTAL_SUFFIX}"
        total_val = (form_data.get(total_key) or "").strip()

        # Optional: only include stations that were *checked* (LNxx = "true")
        checkbox_val = (form_data.get(base) or "").strip()
        if checkbox_val.lower() not in {"true", "on", "1"}:
            # If we *only* want stations where the checkbox was checked, uncomment:
            # continue
            # For now we allow it if positive is filled, even if checkbox missing
            pass

        # Human label: strip "LN" prefix if present → "1R", "3p" etc.
        label = base[2:] if base.startswith("LN") else base

        if total_val:
            summary_parts.append(f"{label} ({pos_val}/{total_val})")
        else:
            # If total is missing, still show positives
            summary_parts.append(f"{label}({pos_val}/?)")

    return ", ".join(summary_parts)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    organs = [
        {"code": k, "label": cfg.display_name}
        for k, cfg in FORM_CONFIGS.items()
    ]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "organs": organs},
    )


@app.get("/{organ}", response_class=HTMLResponse)
async def show_form(request: Request, organ: str):
    cfg = FORM_CONFIGS.get(organ)
    if not cfg:
        return HTMLResponse("Unknown organ", status_code=404)

    return templates.TemplateResponse(
        "form_generic.html",
        {"request": request, "config": cfg},
    )


@app.post("/{organ}/generate", response_class=HTMLResponse)
async def generate_report(request: Request, organ: str):
    # 1. Look up form configuration
    cfg = FORM_CONFIGS.get(organ)
    if cfg is None:
        return HTMLResponse("Unknown organ", status_code=404)

    # 2. Read raw form data once
    form = await request.form()
    form_dict: Dict[str, Any] = dict(form)

    # 3. Extract structured fields according to config
    data = extract_fields(form, cfg)

    # 4. Version (supports cfg.version or cfg["version"])
    version = getattr(cfg, "version", None)
    if version is None and isinstance(cfg, dict):
        version = cfg.get("version")
    if version is not None:
        data["version"] = version

    # 5. Detect whether this organ has nodal_stations and build summary
    #    cfg.sections is a list of dicts; each section is like {"id": ..., "title": ..., "fields": [...]}
    sections = getattr(cfg, "sections", None)
    if sections is None and isinstance(cfg, dict):
        sections = cfg.get("sections", [])

    has_nodal_stations = any(
        isinstance(field, dict) and field.get("type") == "nodal_stations"
        for section in (sections or [])
        if isinstance(section, dict)
        for field in section.get("fields", [])
    )

    if has_nodal_stations:
        data["nodal_summary"] = build_nodal_summary(form_dict)
    else:
        data["nodal_summary"] = ""

    # 6. Derive TNM stage if all components are present
    pT = data.get("pT")
    pN = data.get("pN")
    pM = data.get("pM")
    if pT and pN and pM:
        data["stage"] = derive_stage(cfg, pT, pN, pM)

    # 7. Render diagnostic text
    template = templates.get_template(
        getattr(cfg, "template_name", None)
        if not isinstance(cfg, dict)
        else cfg.get("template_name")
    )
    report_text = template.render(data=data)

    # 8. Render result page
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "report_text": report_text,
            "organ": organ,
        },
    )
