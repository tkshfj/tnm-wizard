from pathlib import Path
import json
import yaml
import re
from typing import Mapping, List, Dict, Any
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


def _getlist(form_like: Mapping[str, Any], name: str) -> List[str]:
    """
    Helper that returns a list of values for a field:
    - If the object has .getlist (Starlette FormData / MultiDict), use it.
    - Otherwise, accept list, comma-separated string, or single value.
    """
    if hasattr(form_like, "getlist"):
        return [v for v in form_like.getlist(name) if v not in (None, "")]
    value = form_like.get(name)
    if value is None:
        return []
    if isinstance(value, list):
        return [v for v in value if v not in (None, "")]
    # e.g. "AD_mucinous,AD_micropap"
    if isinstance(value, str) and "," in value:
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(value)]


def build_histologic_summary(form_data: Mapping[str, Any], cfg: Any) -> str:
    """
    New unified version: read rows of:
      histologic_type_i, histologic_subtype_i, histologic_percent_i (i=1..N)

    Decide the primary combination as the row with the largest percentage,
    then return a text like:

      '腺癌, 乳頭腺癌 (主 50%), 腺房腺癌 30%, 非浸潤性腺癌 粘液非産生 20%'
    """

    # 1) find histologic_mix field in cfg to get type/subtype labels and row count
    sections = getattr(cfg, "sections", None)
    if sections is None and isinstance(cfg, dict):
        sections = cfg.get("sections", [])

    mix_field = None
    for section in sections or []:
        if not isinstance(section, dict):
            continue
        for field in section.get("fields", []):
            if isinstance(field, dict) and field.get("type") == "histologic_mix":
                mix_field = field
                break
        if mix_field:
            break

    if not mix_field:
        # fallback to previous logic or empty string
        return ""

    max_rows = mix_field.get("rows", 4)
    types_cfg = mix_field.get("types", [])

    # Build label maps
    type_labels: Dict[str, str] = {}
    subtype_labels: Dict[str, Dict[str, str]] = {}

    for t in types_cfg:
        t_code = t.get("code")
        t_label = t.get("label", t_code)
        if not t_code:
            continue
        type_labels[t_code] = t_label
        sub_map: Dict[str, str] = {}
        for st in t.get("subtypes", []):
            s_code = st.get("code")
            s_label = st.get("label", s_code)
            if s_code:
                sub_map[s_code] = s_label
        subtype_labels[t_code] = sub_map

    # 2) Collect rows from the form
    rows: List[Dict[str, Any]] = []
    for i in range(1, max_rows + 1):
        t_code = (form_data.get(f"histologic_type_{i}") or "").strip()
        s_code = (form_data.get(f"histologic_subtype_{i}") or "").strip()
        pct_str = (form_data.get(f"histologic_percent_{i}") or "").strip()

        if not (t_code or s_code or pct_str):
            # fully empty row, skip
            continue

        try:
            pct = float(pct_str) if pct_str else 0.0
        except ValueError:
            pct = 0.0

        rows.append(
            {
                "type_code": t_code,
                "subtype_code": s_code,
                "pct": pct,
            }
        )

    if not rows:
        return ""

    # 3) find primary row: the one with the largest pct
    primary_row = max(rows, key=lambda r: r["pct"])
    primary_type_code = primary_row["type_code"]
    primary_sub_code = primary_row["subtype_code"]
    primary_pct = primary_row["pct"]

    primary_type_label = type_labels.get(primary_type_code, primary_type_code or "")
    primary_sub_label = subtype_labels.get(primary_type_code, {}).get(
        primary_sub_code, primary_sub_code or ""
    )

    # 4) build sentence
    parts: List[str] = []

    # Top-level type label if available
    if primary_type_label:
        parts.append(primary_type_label)

    # Primary subtype with "(主 xx%)"
    if primary_sub_label:
        parts.append(f"{primary_sub_label} (主 {primary_pct:.0f}%)")
    elif primary_pct > 0:
        parts.append(f"(主 {primary_pct:.0f}%)")

    # Non-primary rows
    for r in rows:
        if r is primary_row:
            continue

        t_code = r["type_code"]
        s_code = r["subtype_code"]
        pct = r["pct"]

        t_label = type_labels.get(t_code, t_code or "")
        s_label = subtype_labels.get(t_code, {}).get(s_code, s_code or "")

        if not pct:
            continue

        # same type as primary: no need to repeat type label
        if t_code == primary_type_code and t_label:
            if s_label:
                parts.append(f"{s_label} {pct:.0f}%")
            else:
                parts.append(f"{pct:.0f}%")
        else:
            # different histologic type: show both type and subtype
            if t_label and s_label:
                parts.append(f"{t_label} {s_label} {pct:.0f}%")
            elif t_label:
                parts.append(f"{t_label} {pct:.0f}%")
            elif s_label:
                parts.append(f"{s_label} {pct:.0f}%")

    return ", ".join(parts)


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
    # Look up form configuration
    cfg = FORM_CONFIGS.get(organ)
    if cfg is None:
        return HTMLResponse("Unknown organ", status_code=404)

    # Read raw form data once
    form = await request.form()
    form_dict: Dict[str, Any] = dict(form)

    # Extract structured fields according to config
    data = extract_fields(form, cfg)

    # Version (supports cfg.version or cfg["version"])
    version = getattr(cfg, "version", None)
    if version is None and isinstance(cfg, dict):
        version = cfg.get("version")
    if version is not None:
        data["version"] = version

    # Detect whether this organ has nodal_stations and build summary
    #    cfg.sections is a list of dicts; each section is like {"id": ..., "title": ..., "fields": [...]}
    sections = getattr(cfg, "sections", None)
    if sections is None and isinstance(cfg, dict):
        sections = cfg.get("sections", [])

    # histologic summary
    data["histologic_summary"] = build_histologic_summary(form, cfg)

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

    # Derive TNM stage if all components are present
    pT = data.get("pT")
    pN = data.get("pN")
    pM = data.get("pM")
    if pT and pN and pM:
        data["stage"] = derive_stage(cfg, pT, pN, pM)

    # Render diagnostic text
    template = templates.get_template(
        getattr(cfg, "template_name", None)
        if not isinstance(cfg, dict)
        else cfg.get("template_name")
    )
    report_text = template.render(data=data)

    # Render result page
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "report_text": report_text,
            "organ": organ,
        },
    )
