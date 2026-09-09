import os
import sys
import traceback

# Add project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from app import app
except Exception as e:
    from flask import Flask
    err_trace = traceback.format_exc()
    app = Flask(__name__)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def error_diagnostics(path):
        return (
            f"<!doctype html>"
            f"<html><head><title>Server Diagnostics</title>"
            f"<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:#0d1117;color:#c9d1d9;padding:40px;margin:0;}}"
            f".container{{max-width:900px;margin:auto;background:#161b22;padding:30px;border-radius:8px;border:1px solid #30363d;}}"
            f"h1{{color:#f85149;margin-top:0;font-size:22px;}}pre{{background:#0d1117;padding:20px;border-radius:6px;overflow-x:auto;color:#79c0ff;border:1px solid #21262d;font-size:14px;}}</style>"
            f"</head><body><div class='container'>"
            f"<h1>Serverless Initialization Error</h1>"
            f"<p>An unexpected exception occurred when importing the application on Vercel:</p>"
            f"<pre>{err_trace}</pre>"
            f"</div></body></html>",
            500,
            {'Content-Type': 'text/html; charset=utf-8'}
        )
