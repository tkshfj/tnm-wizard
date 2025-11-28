"""Tests for Flask routes."""

import pytest

from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestRoutes:
    """Test cases for application routes."""

    def test_index_get(self, client):
        """Test GET request to index page."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"TNM Wizard" in response.data
        assert b"\xe7\x97\x85\xe7\x90\x86\xe8\xa8\xba\xe6\x96\xad\xe6\x96\x87\xe7\x94\x9f\xe6\x88\x90" in response.data  # "病理診断文生成" in UTF-8

    def test_index_post_basic(self, client):
        """Test POST request with basic form data."""
        response = client.post(
            "/",
            data={
                "t_stage": "T2",
                "n_stage": "N0",
                "m_stage": "M0",
                "histological_type": "adenocarcinoma",
                "differentiation": "G2",
                "lymphatic_invasion": "ly0",
                "venous_invasion": "v0",
                "margin_status": "R0",
            },
        )
        assert response.status_code == 200
        assert b"T2" in response.data
        assert b"N0" in response.data
        assert b"M0" in response.data
        # Check for result section
        assert b"\xe7\x94\x9f\xe6\x88\x90\xe3\x81\x95\xe3\x82\x8c\xe3\x81\x9f\xe8\xa8\xba\xe6\x96\xad\xe6\x96\x87" in response.data  # "生成された診断文" in UTF-8

    def test_index_post_with_location(self, client):
        """Test POST request with location data."""
        response = client.post(
            "/",
            data={
                "t_stage": "T3",
                "n_stage": "N1",
                "m_stage": "M0",
                "histological_type": "squamous",
                "differentiation": "G3",
                "lymphatic_invasion": "ly1",
                "venous_invasion": "v1",
                "margin_status": "R0",
                "location": "TestLocation",
                "tumor_size": "50mm",
            },
        )
        assert response.status_code == 200
        assert b"TestLocation" in response.data
        assert b"50mm" in response.data

    def test_form_preserves_selections(self, client):
        """Test that form selections are preserved after submission."""
        response = client.post(
            "/",
            data={
                "t_stage": "T4",
                "n_stage": "N2",
                "m_stage": "M1",
                "histological_type": "undifferentiated",
                "differentiation": "G4",
                "lymphatic_invasion": "ly1",
                "venous_invasion": "v1",
                "margin_status": "R1",
            },
        )
        assert response.status_code == 200
        # Check that the selected values appear in the HTML (as 'selected')
        html = response.data.decode("utf-8")
        assert "T4" in html
        assert "N2" in html
        assert "M1" in html
