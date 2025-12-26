from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol, Tuple, runtime_checkable

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"

app = FastAPI(title="TNM Wizard")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ------------------------------
# Config
# ------------------------------
@dataclass(frozen=True)
class OrganConfig:
    organ: str
    display_name: str
    version: str
    sections: List[Dict[str, Any]]
    template: str
    stage_table: Dict[str, str]

    @staticmethod
    def from_dict(cfg: Dict[str, Any]) -> "OrganConfig":
        organ = cfg["organ"]
        display_name = cfg.get("display_name", organ)
        version = cfg.get("version", "")
        try:
            sections = cfg["sections"]
            template = cfg["template"]
        except KeyError as e:
            raise ValueError(f"Missing required key in config: {e}") from e

        stage_table: Dict[str, str] = {}
        tnm = cfg.get("tnm_stage_table")

        if isinstance(tnm, dict):
            stage_table = tnm
        elif isinstance(tnm, str):
            path = CONFIG_DIR / tnm
            if path.suffix == ".json":
                stage_table = json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix in (".yaml", ".yml"):
                stage_table = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        return OrganConfig(
            organ=organ,
            display_name=display_name,
            version=version,
            sections=sections,
            template=template,
            stage_table=stage_table,
        )


def load_all_configs() -> Dict[str, OrganConfig]:
    configs: Dict[str, OrganConfig] = {}
    for path in CONFIG_DIR.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        oc = OrganConfig.from_dict(data)
        configs[oc.organ] = oc
    return configs


FORM_CONFIGS: Dict[str, OrganConfig] = load_all_configs()


# ------------------------------
# Small helpers (keep functions simple for Sonar)
# ------------------------------
def iter_config_fields(cfg: OrganConfig) -> Iterable[Dict[str, Any]]:
    for section in cfg.sections:
        for field in section.get("fields", []):
            yield field


def has_field_type(cfg: OrganConfig, field_type: str) -> bool:
    return any(
        field.get("type") == field_type
        for section in cfg.sections
        for field in section.get("fields", [])
    )


def to_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "on", "1", "yes"}


def to_float_or_none(value: Any) -> Optional[float]:
    if value in (None, "", []):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@runtime_checkable
class SupportsGetList(Protocol):

    def getlist(self, key: str) -> List[Any]:
        ...


def getlist(form_like: Mapping[str, Any] | SupportsGetList, name: str) -> List[str]:
    if isinstance(form_like, SupportsGetList):
        return [str(v) for v in form_like.getlist(name) if v not in (None, "")]

    value = form_like.get(name)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v not in (None, "")]
    if isinstance(value, str) and "," in value:
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(value)]


# ------------------------------
# TNM stage
# ------------------------------
def normalize_tnm_component(value: str) -> str:
    s = (value or "").strip()
    return s[1:] if s.startswith("p") else s


def derive_stage(cfg: OrganConfig, pt: str, pn: str, pm: str) -> str:
    """
    TNM -> stage lookup with simple wildcard support.
    - Exact match has priority (e.g. 'T1a,N0,M0')
    - If no exact match, try patterns with '*' such as 'T*,N*,M1*'
    """
    key = ",".join(
        [
            normalize_tnm_component(pt),
            normalize_tnm_component(pn),
            normalize_tnm_component(pm),
        ]
    )

    table = cfg.stage_table

    # 1) exact
    exact = table.get(key)
    if exact:
        return exact

    # 2) wildcard
    for pattern, stage in table.items():
        if "*" not in pattern:
            continue
        regex_pattern = "^" + re.escape(pattern).replace("\\*", ".*") + "$"
        if re.match(regex_pattern, key):
            return stage

    return "Stage ?"


# ------------------------------
# Form extraction
# ------------------------------
def read_field_value(form: Mapping[str, Any], field: Dict[str, Any]) -> Any:
    name = field["name"]
    ftype = field.get("type")
    options = field.get("options")

    if ftype == "checkbox":
        # multi-choice checkbox group
        if options:
            return getlist(form, name)
        # single boolean checkbox
        return to_bool(form.get(name))

    return form.get(name)


def extract_fields(form: Mapping[str, Any], cfg: OrganConfig) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    for field in iter_config_fields(cfg):
        name = field["name"]
        ftype = field.get("type")

        value = read_field_value(form, field)

        if ftype == "number":
            value = to_float_or_none(value)

        data[name] = value

    return data


# ------------------------------
# Histology summary (mix table)
# ------------------------------
def find_histologic_mix_field(cfg: OrganConfig) -> Optional[Dict[str, Any]]:
    for field in iter_config_fields(cfg):
        if field.get("type") == "histologic_mix":
            return field
    return None


def parse_pct(value: Any) -> float:
    try:
        s = str(value or "").strip()
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


# ------------------------------
# Histology summary (mix table) - refactor for Sonar complexity
# ------------------------------
HistRow = Dict[str, Any]


def _build_histology_label_maps(types_cfg: List[Dict[str, Any]]) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    type_labels: Dict[str, str] = {}
    subtype_labels: Dict[str, Dict[str, str]] = {}

    for t in types_cfg:
        t_code = t.get("code")
        if not t_code:
            continue

        type_labels[t_code] = t.get("label", t_code)

        sub_map: Dict[str, str] = {}
        for st in t.get("subtypes", []):
            s_code = st.get("code")
            if s_code:
                sub_map[s_code] = st.get("label", s_code)
        subtype_labels[t_code] = sub_map

    return type_labels, subtype_labels


def _collect_histology_rows(form_data: Mapping[str, Any], max_rows: int) -> List[HistRow]:
    rows: List[HistRow] = []

    for i in range(1, max_rows + 1):
        t_code = (form_data.get(f"histologic_type_{i}") or "").strip()
        s_code = (form_data.get(f"histologic_subtype_{i}") or "").strip()

        pct_raw = form_data.get(f"histologic_percent_{i}")
        pct_str = str(pct_raw or "").strip()

        # skip fully empty rows
        if not (t_code or s_code or pct_str):
            continue

        rows.append(
            {
                "type_code": t_code,
                "subtype_code": s_code,
                "pct": parse_pct(pct_raw),
            }
        )

    return rows


def _pick_primary_row(rows: List[HistRow]) -> HistRow:
    def score(r: HistRow) -> tuple[float, int]:
        pct = float(r.get("pct") or 0.0)
        has_subtype = 1 if (r.get("subtype_code") or "").strip() else 0
        return (pct, has_subtype)
    return max(rows, key=score)


def _label_for_type(type_labels: Dict[str, str], type_code: str) -> str:
    return type_labels.get(type_code, type_code or "")


def _label_for_subtype(subtype_labels: Dict[str, Dict[str, str]], type_code: str, subtype_code: str) -> str:
    return subtype_labels.get(type_code, {}).get(subtype_code, subtype_code or "")


def _format_primary_parts(pt_label: str, ps_label: str, ppct: float) -> List[str]:
    """
    Same rule as your current code:
    - If subtype label starts with type label, avoid duplication.
    - Show '(主 xx%)' only if pct > 0.
    """
    parts: List[str] = []

    if pt_label and ps_label and ps_label.startswith(pt_label):
        parts.append(ps_label if ppct <= 0 else f"{ps_label} (主 {ppct:.0f}%)")
        return parts

    if pt_label:
        parts.append(pt_label)

    if ps_label:
        parts.append(ps_label if ppct <= 0 else f"{ps_label} (主 {ppct:.0f}%)")
    elif ppct > 0:
        parts.append(f"(主 {ppct:.0f}%)")

    return parts


def _format_non_primary_part(
    r: HistRow,
    pt_code: str,
    type_labels: Dict[str, str],
    subtype_labels: Dict[str, Dict[str, str]],
) -> str:
    """
    Returns '' if row should not contribute (pct <= 0).
    Otherwise returns one formatted fragment, same logic as your current code.
    """
    pct = float(r.get("pct") or 0.0)
    if pct <= 0:
        return ""

    t_code = r.get("type_code", "")
    s_code = r.get("subtype_code", "")

    t_label = _label_for_type(type_labels, t_code)
    s_label = _label_for_subtype(subtype_labels, t_code, s_code)

    pct_txt = f"{pct:.0f}%"

    if t_code == pt_code:
        return f"{s_label} {pct_txt}" if s_label else pct_txt

    if t_label and s_label:
        return f"{t_label} {s_label} {pct_txt}"
    if t_label:
        return f"{t_label} {pct_txt}"
    if s_label:
        return f"{s_label} {pct_txt}"

    return ""


def build_histologic_summary(form_data: Mapping[str, Any], cfg: OrganConfig) -> str:
    mix_field = find_histologic_mix_field(cfg)
    if not mix_field:
        return ""

    max_rows = int(mix_field.get("rows", 4))
    types_cfg = mix_field.get("types", [])

    type_labels, subtype_labels = _build_histology_label_maps(types_cfg)
    rows = _collect_histology_rows(form_data, max_rows)
    if not rows:
        return ""

    primary = _pick_primary_row(rows)
    pt_code = primary.get("type_code", "")
    ps_code = primary.get("subtype_code", "")
    ppct = float(primary.get("pct") or 0.0)

    pt_label = _label_for_type(type_labels, pt_code)
    ps_label = _label_for_subtype(subtype_labels, pt_code, ps_code)

    parts = _format_primary_parts(pt_label, ps_label, ppct)

    for r in rows:
        if r is primary:
            continue
        frag = _format_non_primary_part(r, pt_code, type_labels, subtype_labels)
        if frag:
            parts.append(frag)

    return ", ".join(parts)


# ------------------------------
# Nodal summary
# ------------------------------
def _first_nonempty(form_like: Mapping[str, Any] | SupportsGetList, key: str) -> str:
    if isinstance(form_like, SupportsGetList):
        for v in form_like.getlist(key):
            s = str(v or "").strip()
            if s:
                return s
        return ""
    return str(form_like.get(key) or "").strip()


def build_nodal_summary(form_data: Mapping[str, Any] | SupportsGetList) -> str:
    pos_suffix = "_positive"
    total_suffix = "_total"
    parts: List[str] = []

    # FormData iteration can include duplicates; use set for stability
    keys = sorted(set(form_data))
    for key in keys:
        if not key.endswith(pos_suffix):
            continue

        pos_val = _first_nonempty(form_data, key)
        if not pos_val:
            continue

        base = key[: -len(pos_suffix)]
        total_key = f"{base}{total_suffix}"
        total_val = _first_nonempty(form_data, total_key)

        label = base[2:] if base.startswith("LN") else base
        parts.append(f"{label} ({pos_val}/{total_val})" if total_val else f"{label} ({pos_val}/?)")

    return ", ".join(parts)


# ------------------------------
# Routes
# ------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    organs = [{"code": k, "label": cfg.display_name} for k, cfg in FORM_CONFIGS.items()]
    return templates.TemplateResponse("index.html", {"request": request, "organs": organs})


@app.get("/{organ}", response_class=HTMLResponse)
async def show_form(request: Request, organ: str):
    cfg = FORM_CONFIGS.get(organ)
    if not cfg:
        return HTMLResponse("Unknown organ", status_code=404)
    return templates.TemplateResponse("form_generic.html", {"request": request, "config": cfg})


@app.post("/{organ}/generate", response_class=HTMLResponse)
async def generate_report(request: Request, organ: str):
    cfg = FORM_CONFIGS.get(organ)
    if cfg is None:
        return HTMLResponse("Unknown organ", status_code=404)

    form = await request.form()
    # form_dict: Dict[str, Any] = dict(form)

    data = extract_fields(form, cfg)
    if cfg.version:
        data["version"] = cfg.version

    data["histologic_summary"] = build_histologic_summary(form, cfg)

    if has_field_type(cfg, "nodal_stations"):
        data["nodal_summary"] = build_nodal_summary(form)  # form_dict
    else:
        data["nodal_summary"] = ""

    # TNM stage (expects extracted keys pT/pN/pM)
    pt = data.get("pT")
    pn = data.get("pN")
    pm = data.get("pM")
    if pt and pn and pm:
        data["stage"] = derive_stage(cfg, pt, pn, pm)

    # FIX: use cfg.template (your YAML key is "template")
    report_template = templates.get_template(cfg.template)
    report_text = report_template.render(data=data)

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "report_text": report_text, "organ": organ},
    )
