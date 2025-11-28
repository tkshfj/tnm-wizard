"""TNM Wizard - Synoptic Cancer Pathology Diagnostic Paragraph Generator."""

import os
import secrets

from flask import Flask


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    # Use environment variable for secret key in production, fallback to random key
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    from app import routes

    app.register_blueprint(routes.bp)

    return app
