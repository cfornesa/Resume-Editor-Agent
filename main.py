from flask import Flask, request, jsonify, render_template
from model import build_resume, edit_resume
from flask_cors import CORS
import time
import os

# Instantiate Flask object
app = Flask(__name__)
CORS(app)

# Serve frontend
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Phase 1: Build the initial resume from structured form data
@app.route('/build', methods=['POST'])
def build():
    data = request.json

    required_fields = [
        'name', 'occupation', 'industry', 
        'job_description', 'summary', 'skills', 'experience', 'education', 'awards'
    ]

    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": "Missing one or more required resume fields."}), 400

    resume_data = (
        f"Name: {data['name']}\n"
        f"Target Occupation: {data['occupation']}\n"
        f"Industry: {data['industry']}\n"
        f"Target JD: {data['job_description']}\n"
        f"Summary: {data['summary']}\n"
        f"Skills: {data['skills']}\n"
        f"Experience: {data['experience']}\n"
        f"Education: {data['education']}\n"
        f"Awards: {data['awards']}"
    )

    start_time = time.time()

    try:
        result = build_resume(resume_data)
        result['duration'] = time.time() - start_time
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Phase 2: Fine-tune the resume via conversational chat
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    current_resume = data.get('resume')
    user_message = data.get('message')
    history = data.get('history', [])

    if not current_resume or not user_message:
        return jsonify({"error": "Missing resume or message."}), 400

    start_time = time.time()

    try:
        result = edit_resume(current_resume, user_message, history)
        result['duration'] = time.time() - start_time
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ensures Flask dev server runs when the file is executed
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)