"""Tests for TNM staging module."""

import pytest

from app.tnm_staging import (
    T_STAGES,
    N_STAGES,
    M_STAGES,
    generate_diagnostic_paragraph,
    get_stage_group,
)


class TestTNMStaging:
    """Test cases for TNM staging functionality."""

    def test_t_stages_defined(self):
        """Test that T stages are properly defined."""
        assert "TX" in T_STAGES
        assert "T0" in T_STAGES
        assert "Tis" in T_STAGES
        assert "T1" in T_STAGES
        assert "T2" in T_STAGES
        assert "T3" in T_STAGES
        assert "T4" in T_STAGES

    def test_n_stages_defined(self):
        """Test that N stages are properly defined."""
        assert "NX" in N_STAGES
        assert "N0" in N_STAGES
        assert "N1" in N_STAGES
        assert "N2" in N_STAGES
        assert "N3" in N_STAGES

    def test_m_stages_defined(self):
        """Test that M stages are properly defined."""
        assert "MX" in M_STAGES
        assert "M0" in M_STAGES
        assert "M1" in M_STAGES


class TestStageGroup:
    """Test cases for stage group determination."""

    def test_stage_0(self):
        """Test Stage 0 determination."""
        assert get_stage_group("Tis", "N0", "M0") == "Stage 0"

    def test_stage_1(self):
        """Test Stage I determination."""
        assert get_stage_group("T1", "N0", "M0") == "Stage I"
        assert get_stage_group("T1a", "N0", "M0") == "Stage I"
        assert get_stage_group("T1b", "N0", "M0") == "Stage I"

    def test_stage_2a(self):
        """Test Stage IIA determination."""
        assert get_stage_group("T2", "N0", "M0") == "Stage IIA"

    def test_stage_2b(self):
        """Test Stage IIB determination."""
        assert get_stage_group("T3", "N0", "M0") == "Stage IIB"
        assert get_stage_group("T4", "N0", "M0") == "Stage IIB"

    def test_stage_3(self):
        """Test Stage III determination."""
        assert get_stage_group("T1", "N1", "M0") == "Stage III"
        assert get_stage_group("T2", "N2", "M0") == "Stage III"
        assert get_stage_group("T3", "N1", "M0") == "Stage III"

    def test_stage_4(self):
        """Test Stage IV determination (distant metastasis)."""
        assert get_stage_group("T1", "N0", "M1") == "Stage IV"
        assert get_stage_group("T4", "N3", "M1") == "Stage IV"
        assert get_stage_group("TX", "NX", "M1") == "Stage IV"


class TestDiagnosticParagraphGeneration:
    """Test cases for diagnostic paragraph generation."""

    def test_basic_generation(self):
        """Test basic diagnostic paragraph generation."""
        data = {
            "t_stage": "T2",
            "n_stage": "N0",
            "m_stage": "M0",
            "histological_type": "adenocarcinoma",
            "differentiation": "G2",
            "lymphatic_invasion": "ly0",
            "venous_invasion": "v0",
            "margin_status": "R0",
        }
        result = generate_diagnostic_paragraph(data)

        assert "病理診断報告書" in result
        assert "Pathological Diagnosis Report" in result
        assert "T2" in result
        assert "N0" in result
        assert "M0" in result
        assert "Adenocarcinoma" in result
        assert "Moderately differentiated" in result

    def test_generation_with_location_and_size(self):
        """Test paragraph generation includes location and tumor size."""
        data = {
            "t_stage": "T3",
            "n_stage": "N1",
            "m_stage": "M0",
            "histological_type": "squamous",
            "differentiation": "G3",
            "lymphatic_invasion": "ly1",
            "venous_invasion": "v1",
            "margin_status": "R0",
            "tumor_size": "45mm",
            "location": "胃体部",
        }
        result = generate_diagnostic_paragraph(data)

        assert "45mm" in result
        assert "胃体部" in result
        assert "Squamous cell carcinoma" in result
        assert "Poorly differentiated" in result

    def test_generation_with_additional_findings(self):
        """Test paragraph generation includes additional findings."""
        data = {
            "t_stage": "T1a",
            "n_stage": "N0",
            "m_stage": "M0",
            "histological_type": "adenocarcinoma",
            "differentiation": "G1",
            "lymphatic_invasion": "ly0",
            "venous_invasion": "v0",
            "margin_status": "R0",
            "additional_findings": "特記すべき所見なし",
        }
        result = generate_diagnostic_paragraph(data)

        assert "特記すべき所見なし" in result
        assert "Additional Findings" in result

    def test_generation_with_default_values(self):
        """Test paragraph generation with empty/default data."""
        data = {}
        result = generate_diagnostic_paragraph(data)

        assert "病理診断報告書" in result
        assert "TX" in result
        assert "NX" in result
        assert "MX" in result

    def test_footer_compliance_statement(self):
        """Test that the footer contains compliance statement."""
        data = {"t_stage": "T1", "n_stage": "N0", "m_stage": "M0"}
        result = generate_diagnostic_paragraph(data)

        assert "癌取扱い規約に準拠" in result
        assert "Japanese General Rules" in result
