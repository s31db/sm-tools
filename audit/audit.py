from flask import Flask, render_template, jsonify, request, send_from_directory
import json
from datetime import datetime
import os
import re


app = Flask(__name__)


def remplacer_caracteres(string: str) -> str:
    # Utiliser une expression régulière pour remplacer les caractères non autorisés par _
    nouvelle_chaine = re.sub(r'[^a-zA-Z0-9_]', '_', string)
    return nouvelle_chaine


@app.route('/')
def index():
    return render_template('audit_fr.html')


@app.route('/audit_fr.json')
def get_audit_json():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'audit_fr.json')


@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), remplacer_caracteres(filename))


@app.route('/save_results', methods=['POST'])
def save_results():
    if request.method == 'POST':
        data = request.json
        date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        filename = f'audit_{date_now}.json'
        path = os.path.join(app.root_path, 'result', filename)
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)

        return jsonify({"status": "success", "filename": filename})


if __name__ == '__main__':
    app.run(debug=True)
