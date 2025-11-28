"""TNM staging definitions following Japanese General Rules."""

# TNM staging values based on Japanese General Rules for Clinical and
# Pathological Study of Cancer

T_STAGES = {
    "TX": "Primary tumor cannot be assessed",
    "T0": "No evidence of primary tumor",
    "Tis": "Carcinoma in situ",
    "T1": "Tumor limited to mucosa or submucosa",
    "T1a": "Tumor invades mucosa",
    "T1b": "Tumor invades submucosa",
    "T2": "Tumor invades muscularis propria",
    "T3": "Tumor invades subserosa or adventitia",
    "T4": "Tumor directly invades other organs or structures",
    "T4a": "Tumor perforates visceral peritoneum",
    "T4b": "Tumor directly invades other organs or structures",
}

N_STAGES = {
    "NX": "Regional lymph nodes cannot be assessed",
    "N0": "No regional lymph node metastasis",
    "N1": "Metastasis in 1-2 regional lymph nodes",
    "N2": "Metastasis in 3-6 regional lymph nodes",
    "N3": "Metastasis in 7 or more regional lymph nodes",
    "N3a": "Metastasis in 7-15 regional lymph nodes",
    "N3b": "Metastasis in 16 or more regional lymph nodes",
}

M_STAGES = {
    "MX": "Distant metastasis cannot be assessed",
    "M0": "No distant metastasis",
    "M1": "Distant metastasis present",
}

HISTOLOGICAL_TYPES = {
    "adenocarcinoma": "Adenocarcinoma",
    "squamous": "Squamous cell carcinoma",
    "adenosquamous": "Adenosquamous carcinoma",
    "undifferentiated": "Undifferentiated carcinoma",
    "other": "Other histological type",
}

DIFFERENTIATION_GRADES = {
    "G1": "Well differentiated",
    "G2": "Moderately differentiated",
    "G3": "Poorly differentiated",
    "G4": "Undifferentiated",
    "GX": "Grade cannot be assessed",
}

LYMPHATIC_INVASION = {
    "ly0": "No lymphatic invasion",
    "ly1": "Lymphatic invasion present",
    "lyX": "Lymphatic invasion cannot be assessed",
}

VENOUS_INVASION = {
    "v0": "No venous invasion",
    "v1": "Venous invasion present",
    "vX": "Venous invasion cannot be assessed",
}

MARGIN_STATUS = {
    "R0": "No residual tumor",
    "R1": "Microscopic residual tumor",
    "R2": "Macroscopic residual tumor",
    "RX": "Presence of residual tumor cannot be assessed",
}


def get_stage_group(t_stage: str, n_stage: str, m_stage: str) -> str:
    """Determine the stage group based on TNM staging.

    This is a simplified staging system. Actual staging depends on cancer type.
    """
    if m_stage == "M1":
        return "Stage IV"
    if t_stage == "Tis" and n_stage == "N0":
        return "Stage 0"
    if t_stage in ("T1", "T1a", "T1b") and n_stage == "N0":
        return "Stage I"
    if t_stage == "T2" and n_stage == "N0":
        return "Stage IIA"
    if t_stage in ("T3", "T4", "T4a", "T4b") and n_stage == "N0":
        return "Stage IIB"
    # Stage III: Any T1-T4 with positive lymph nodes (N1-N3)
    n_positive = n_stage in ("N1", "N2", "N3", "N3a", "N3b")
    t_valid = t_stage in ("T1", "T1a", "T1b", "T2", "T3", "T4", "T4a", "T4b")
    if t_valid and n_positive:
        return "Stage III"
    return "Stage cannot be determined"


def generate_diagnostic_paragraph(data: dict) -> str:
    """Generate a synoptic diagnostic paragraph from the input data.

    Args:
        data: Dictionary containing the staging and pathology data.

    Returns:
        Formatted diagnostic paragraph.
    """
    t_stage = data.get("t_stage", "TX")
    n_stage = data.get("n_stage", "NX")
    m_stage = data.get("m_stage", "MX")
    histological_type = data.get("histological_type", "other")
    differentiation = data.get("differentiation", "GX")
    lymphatic = data.get("lymphatic_invasion", "lyX")
    venous = data.get("venous_invasion", "vX")
    margin = data.get("margin_status", "RX")
    tumor_size = data.get("tumor_size", "")
    location = data.get("location", "")
    additional_findings = data.get("additional_findings", "")

    # Get descriptions
    t_desc = T_STAGES.get(t_stage, "Primary tumor status unknown")
    n_desc = N_STAGES.get(n_stage, "Regional lymph node status unknown")
    m_desc = M_STAGES.get(m_stage, "Distant metastasis status unknown")
    hist_desc = HISTOLOGICAL_TYPES.get(histological_type, "Histological type unspecified")
    diff_desc = DIFFERENTIATION_GRADES.get(differentiation, "Grade unspecified")
    ly_desc = LYMPHATIC_INVASION.get(lymphatic, "Lymphatic invasion status unknown")
    v_desc = VENOUS_INVASION.get(venous, "Venous invasion status unknown")
    margin_desc = MARGIN_STATUS.get(margin, "Margin status unknown")

    stage_group = get_stage_group(t_stage, n_stage, m_stage)

    # Build the synoptic paragraph
    lines = [
        "【病理診断報告書 / Pathological Diagnosis Report】",
        "",
        "■ 組織型 / Histological Type:",
        f"  {hist_desc}",
        f"  分化度 / Differentiation: {diff_desc}",
        "",
    ]

    if location:
        lines.extend([f"■ 占拠部位 / Location: {location}", ""])

    if tumor_size:
        lines.extend([f"■ 腫瘍最大径 / Tumor Size: {tumor_size}", ""])

    lines.extend(
        [
            "■ 進行度 / TNM Classification:",
            f"  T: {t_stage} - {t_desc}",
            f"  N: {n_stage} - {n_desc}",
            f"  M: {m_stage} - {m_desc}",
            f"  pStage: {stage_group}",
            "",
            "■ 脈管侵襲 / Vascular Invasion:",
            f"  リンパ管侵襲 / Lymphatic invasion: {lymphatic} - {ly_desc}",
            f"  静脈侵襲 / Venous invasion: {venous} - {v_desc}",
            "",
            "■ 切除断端 / Resection Margin:",
            f"  {margin} - {margin_desc}",
            "",
        ]
    )

    if additional_findings:
        lines.extend(
            ["■ その他の所見 / Additional Findings:", f"  {additional_findings}", ""]
        )

    lines.append("---")
    lines.append("本報告書は癌取扱い規約に準拠して作成されています。")
    lines.append(
        "This report follows the Japanese General Rules for Clinical and Pathological Study of Cancer."
    )

    return "\n".join(lines)
