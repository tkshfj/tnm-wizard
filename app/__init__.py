"""TNM Wizard - Synoptic Cancer Pathology Diagnostic Paragraph Generator."""

from flask import Flask


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "tnm-wizard-dev-key"

    from app import routes

    app.register_blueprint(routes.bp)

    return app
