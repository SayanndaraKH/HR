import os
import sys
import traceback
from flask import Flask, jsonify

# Add project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

app = None
init_error = None

try:
    from app import app as real_app
    app = real_app
except Exception:
    init_error = traceback.format_exc()
    app = Flask(__name__)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        task_files = []
        try:
            for root, dirs, files in os.walk(parent_dir):
                for f in files:
                    task_files.append(os.path.relpath(os.path.join(root, f), parent_dir))
        except Exception as e:
            task_files.append(f"Walk error: {e}")

        return jsonify({
            "status": "init_error",
            "error": init_error,
            "parent_dir": parent_dir,
            "sys_path": sys.path,
            "files_found": sorted(task_files)
        }), 500
