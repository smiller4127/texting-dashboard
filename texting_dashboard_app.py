
from flask import Flask, render_template_string, request, redirect, send_from_directory, jsonify
import subprocess
import os
import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['LOG_FILE'] = 'reply_log.txt'
app.config['ERROR_LOG'] = 'error_log.txt'
app.config['SEND_LOG'] = 'send_log.txt'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

TEMPLATE = """<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Texting Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 2rem; background-color: #f5f5f5; }
        h1 { color: #333; }
        button, select, input[type=file] { padding: 10px; margin: 10px 0; font-size: 16px; display: block; }
        form, .log-section { margin-bottom: 2rem; background: #fff; padding: 1rem; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .log-section pre { background: #000; color: #0f0; padding: 1rem; overflow-x: auto; height: 200px; }
    </style>
</head>
<body>
    <h1>📲 Texting Lead Dashboard</h1>
    <form action='/upload' method='post' enctype='multipart/form-data'>
        <label>📂 Upload New Lead File (CSV/XLSX):</label>
        <input type='file' name='file'>
        <button type='submit'>Upload File</button>
    </form>
    <form action='/run' method='post'>
        <button name='task' value='prep'>1️⃣ Prep New Lead File</button>
        <label>📊 Choose Group to Text:</label>
        <select name='group'>
            <option value='Group A'>Group A</option>
            <option value='Group B'>Group B</option>
            <option value='Group C'>Group C</option>
        </select>
        <button name='task' value='send'>2️⃣ Send Campaign</button>
        <button name='task' value='reply'>3️⃣ Start Auto Reply Listener</button>
    </form>
    <div class='log-section'>
        <h2>📬 Recent Replies / Logs</h2>
        <pre>{{ logs }}</pre>
        <a href='/download_dnc'>⬇️ Download DNC List</a>
    </div>
    <div class='log-section'>
        <h2>⚠️ Twilio Delivery Errors</h2>
        <pre>{{ error_logs }}</pre>
    </div>
    <div class='log-section'>
        <h2>📈 Send Activity Log</h2>
        <pre>{{ send_logs }}</pre>
    </div>
</body>
</html>"""

@app.route("/")
def index():
    logs, error_logs, send_logs = "", "", ""
    if os.path.exists(app.config['LOG_FILE']):
        with open(app.config['LOG_FILE'], 'r') as f: logs = f.read()[-5000:]
    if os.path.exists(app.config['ERROR_LOG']):
        with open(app.config['ERROR_LOG'], 'r') as f: error_logs = f.read()[-3000:]
    if os.path.exists(app.config['SEND_LOG']):
        with open(app.config['SEND_LOG'], 'r') as f: send_logs = f.read()[-3000:]
    return render_template_string(TEMPLATE, logs=logs, error_logs=error_logs, send_logs=send_logs)

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files: return redirect("/")
    file = request.files['file']
    if file.filename == '': return redirect("/")
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        os.replace(os.path.join(app.config['UPLOAD_FOLDER'], filename), filename)
    return redirect("/")

@app.route("/run", methods=["POST"])
def run_task():
    task = request.form.get("task")
    group = request.form.get("group")
    if task == "prep":
        subprocess.Popen(["python", "prep_excel.py"])
    elif task == "send" and group:
        os.environ['SEND_GROUP'] = group
        subprocess.Popen(["python", "send_campaign.py"])
    elif task == "reply":
        subprocess.Popen(["python", "auto_reply.py"])
    return redirect("/")

@app.route("/download_dnc")
def download_dnc():
    return send_from_directory(directory=".", path="DNC_List.xlsx", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=8000)
