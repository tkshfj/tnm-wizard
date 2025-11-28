"""Routes for TNM Wizard application."""

from flask import Blueprint, render_template, request

from app.tnm_staging import (
    DIFFERENTIATION_GRADES,
    HISTOLOGICAL_TYPES,
    LYMPHATIC_INVASION,
    M_STAGES,
    MARGIN_STATUS,
    N_STAGES,
    T_STAGES,
    VENOUS_INVASION,
    generate_diagnostic_paragraph,
)

bp = Blueprint("main", __name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    """Handle the main page with form and results."""
    result = None
    form_data = {}

    if request.method == "POST":
        form_data = {
            "t_stage": request.form.get("t_stage", "TX"),
            "n_stage": request.form.get("n_stage", "NX"),
            "m_stage": request.form.get("m_stage", "MX"),
            "histological_type": request.form.get("histological_type", "other"),
            "differentiation": request.form.get("differentiation", "GX"),
            "lymphatic_invasion": request.form.get("lymphatic_invasion", "lyX"),
            "venous_invasion": request.form.get("venous_invasion", "vX"),
            "margin_status": request.form.get("margin_status", "RX"),
            "tumor_size": request.form.get("tumor_size", ""),
            "location": request.form.get("location", ""),
            "additional_findings": request.form.get("additional_findings", ""),
        }
        result = generate_diagnostic_paragraph(form_data)

    return render_template(
        "index.html",
        t_stages=T_STAGES,
        n_stages=N_STAGES,
        m_stages=M_STAGES,
        histological_types=HISTOLOGICAL_TYPES,
        differentiation_grades=DIFFERENTIATION_GRADES,
        lymphatic_invasion=LYMPHATIC_INVASION,
        venous_invasion=VENOUS_INVASION,
        margin_status=MARGIN_STATUS,
        result=result,
        form_data=form_data,
    )
