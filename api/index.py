import os
import sys
import traceback
from flask import Flask, jsonify, request

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

app = Flask(__name__)

@app.route('/')
def home():
    try:
        import app as main_app
        return main_app.app(request.environ, lambda status, headers: None)
    except Exception:
        pass
    return (
        "<h1>HRMS System Diagnostic</h1>"
        "<ul>"
        "<li><a href='/debug'>View Vercel Files & Environment (/debug)</a></li>"
        "<li><a href='/try-import'>Test Importing app.py (/try-import)</a></li>"
        "<li><a href='/app/login'>Direct Login Route (/app/login)</a></li>"
        "</ul>"
    )

@app.route('/debug')
def debug_route():
    root_files = []
    try:
        root_files = os.listdir(parent_dir)
    except Exception as e:
        root_files = [str(e)]

    return jsonify({
        "status": "ok",
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "parent_dir": parent_dir,
        "files_in_parent": sorted(root_files),
        "sys_path": sys.path
    })

@app.route('/try-import')
def try_import_route():
    try:
        import app as main_module
        return jsonify({
            "status": "success",
            "message": "Successfully imported app.py!",
            "routes_in_app": [str(rule) for rule in main_module.app.url_map.iter_rules()]
        })
    except Exception:
        return (
            f"<h1>Import Error Traceback</h1>"
            f"<pre style='background:#f4f4f4;padding:15px;'>{traceback.format_exc()}</pre>",
            500,
            {'Content-Type': 'text/html; charset=utf-8'}
        )

# Fallback forwarder to main app if available
@app.route('/app/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def forward_to_main(subpath):
    try:
        import app as main_module
        return main_module.app
    except Exception:
        return f"<pre>{traceback.format_exc()}</pre>", 500
