from pathlib import Path
import json
import yaml

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"

app = FastAPI(title="TNM Wizard PoC")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


class OrganConfig:
    def __init__(self, cfg: dict):
        self.organ = cfg["organ"]
        self.display_name = cfg.get("display_name", self.organ)
        self.sections = cfg["sections"]
        self.template_name = cfg["template"]
        # TNM stage table: can be dict or JSON file
        self.stage_table = {}
        tnm = cfg.get("tnm_stage_table")
        if isinstance(tnm, dict):
            self.stage_table = tnm
        elif isinstance(tnm, str):
            # if you later want JSON/YAML files, handle here
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
    """Very simple TNM -> stage lookup for PoC."""
    # Normalize: pT1a -> T1a, pN0 -> N0 etc.
    t = pT.replace("p", "")
    n = pN.replace("p", "")
    m = pM.replace("p", "")
    key = f"{t},{n},{m}"
    return organ_cfg.stage_table.get(key, "Stage ?")


def extract_fields(form, organ_cfg: OrganConfig) -> dict:
    data = {}
    for section in organ_cfg.sections:
        for field in section["fields"]:
            name = field["name"]
            value = form.get(name)
            if field.get("type") == "number" and value not in (None, ""):
                try:
                    value = float(value)
                except ValueError:
                    value = None
            data[name] = value
    return data


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
    cfg = FORM_CONFIGS.get(organ)
    if not cfg:
        return HTMLResponse("Unknown organ", status_code=404)

    form = await request.form()
    data = extract_fields(form, cfg)

    if "pT" in data and "pN" in data and "pM" in data:
        data["stage"] = derive_stage(cfg, data["pT"], data["pN"], data["pM"])

    report_text = templates.get_template(cfg.template_name).render(data=data)

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "report_text": report_text, "organ": organ},
    )
