from flask import Flask, render_template, jsonify, request, send_from_directory
import json
from datetime import datetime
import os
import re


app = Flask(__name__)


def remplacer_caracteres(string: str) -> str:
    # Utiliser une expression régulière pour remplacer les caractères non autorisés par _
    nouvelle_chaine = re.sub(r"[^a-zA-Z0-9_\.]", "_", string)
    return nouvelle_chaine


@app.route("/")
def index():
    print("index")
    return static_file("index.html")


@app.route("/audit")
def audit():
    return render_template("audit_fr.html")


@app.route("/audit_fr.json")
def get_audit_json():
    return send_from_directory(os.path.join(app.root_path, "static"), "audit_fr.json")


@app.route("/manifest")
def manifest():
    return render_template("manifest_agile_fr.html")


@app.route("/manifest_agile_fr.json")
def get_manifest_json():
    # path = os.path.join(app.root_path, 'static', 'manifest_agile_fr.json')
    # with open(path, 'r', encoding='utf-8') as file:
    #     data = json.load(file)
    # return jsonify(data)
    return send_from_directory(
        os.path.join(app.root_path, "static"), "manifest_agile_fr.json"
    )


@app.route("/static/<path:filename>")
def static_file(filename):
    return send_from_directory(
        os.path.join(app.root_path, "static"), remplacer_caracteres(filename)
    )


@app.route("/save_results_audit", methods=["POST"])
def save_results_audit():
    return save_result(request)


@app.route("/save_results_manifest", methods=["POST"])
def save_results_manifest():
    return save_result(request)


def save_result(request):
    if request.method == "POST":
        data = request.json
        date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        filename = f"audit_{date_now}.json"
        path = os.path.join(app.root_path, "result", filename)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        return jsonify({"status": "success", "filename": filename})


if __name__ == "__main__":
    app.run(debug=False)
