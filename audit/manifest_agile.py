from flask import Flask, render_template, jsonify, request, send_from_directory
import json
from datetime import datetime
import os
from audit import remplacer_caracteres

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('manifest_agile_fr.html')


@app.route('/manifest_agile_fr.json')
def get_manifest_json():
    # path = os.path.join(app.root_path, 'static', 'manifest_agile_fr.json')
    # with open(path, 'r', encoding='utf-8') as file:
    #     data = json.load(file)
    # return jsonify(data)
    return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest_agile_fr.json')


@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), remplacer_caracteres(filename))


@app.route('/save_results', methods=['POST'])
def save_results():
    if request.method == 'POST':
        data = request.json
        date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        filename = f'manifest_agile_{date_now}.json'
        path = os.path.join(app.root_path, 'result', filename)
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)

        return jsonify({"status": "success", "filename": filename})


if __name__ == '__main__':
    app.run(debug=False)
