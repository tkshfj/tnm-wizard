# TNM Wizard

A small intranet web application, accessible on Windows browsers, that converts structured inputs into synoptic cancer pathology diagnostic paragraphs aligned with the Japanese General Rules for Clinical and Pathological Study of Cancer (癌取扱い規約).

## Features

- **TNM Staging Input**: Select T (Primary Tumor), N (Regional Lymph Nodes), and M (Distant Metastasis) stages
- **Histological Classification**: Choose tumor type and differentiation grade
- **Vascular Invasion**: Document lymphatic and venous invasion status
- **Resection Margin**: Record surgical margin status
- **Bilingual Output**: Generate reports in both Japanese and English
- **Copy to Clipboard**: Easy one-click copying of generated reports

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/tkshfj/tnm-wizard.git
cd tnm-wizard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

For development with debug mode enabled:
```bash
FLASK_DEBUG=true python run.py
```

4. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Select the histological type and differentiation grade
2. Enter tumor location and size (optional)
3. Select TNM staging values from the dropdowns
4. Select vascular invasion and margin status
5. Add any additional findings (optional)
6. Click "診断文を生成 / Generate Report"
7. Copy the generated report to your clipboard

## Production Deployment

For production deployment on an intranet, use gunicorn with a proper secret key:

```bash
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

## Project Structure

```
tnm-wizard/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── routes.py             # URL routes and view functions
│   ├── tnm_staging.py        # TNM staging logic and definitions
│   ├── templates/
│   │   └── index.html        # Main web interface
│   └── static/
│       └── style.css         # CSS styling
├── tests/
│   ├── test_routes.py        # Route tests
│   └── test_tnm_staging.py   # Staging logic tests
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── README.md
```

## License

MIT License - see LICENSE file for details.

## References

This application follows the Japanese General Rules for Clinical and Pathological Study of Cancer (癌取扱い規約に準拠).
