from flask import Flask, jsonify, request
from firebase_admin import credentials, firestore, initialize_app
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Initialize Flask and Firebase Admin
app = Flask(__name__)
CORS(app)  # Allow all origins (no restrictions)
load_dotenv()

# Firebase credentials
firebase_creds = {
    "type": os.getenv("FIREBASE_TYPE", "service_account"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),  # Ensure newlines are interpreted correctly
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
}

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_creds)
initialize_app(cred)
db = firestore.client()
tasks_ref = db.collection('tasks')

@app.after_request
def set_headers(response):
    # Adjust COOP and COEP headers for security
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    return response

# Route to get all tasks
@app.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = []
        for doc in tasks_ref.stream():
            task = doc.to_dict()
            task['id'] = doc.id  # Include document ID for updates/deletes
            tasks.append(task)
        return jsonify(tasks)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500

# Route to add a new task
@app.route('/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        if not data.get('task'):
            return jsonify({"error": "Task content is required"}), 400
        
        # Add the task to the collection and get the document reference
        new_task_ref = tasks_ref.add(data)
        
        # Ensure that the reference is valid and contains an ID
        if isinstance(new_task_ref, tuple):
            new_task_ref = new_task_ref[1]  # The document reference is likely the second item in the tuple
        
        # Return the response with the task ID
        return jsonify({"message": "Task added successfully!", "id": new_task_ref.id}), 201
    except Exception as e:
        print(f"Error adding task: {str(e)}")  # Log the full error to the console
        return jsonify({"error": f"Failed to add task: {str(e)}"}), 500

# Route to update an existing task
@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided for update"}), 400
        task_ref = tasks_ref.document(task_id)
        task_ref.update(data)
        return jsonify({"message": "Task updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to update task: {str(e)}"}), 500

# Route to delete a task
@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        task_ref = tasks_ref.document(task_id)
        task_ref.delete()
        return jsonify({"message": "Task deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete task: {str(e)}"}), 500

if __name__ == '__main__':
    print("Server is running")  # Server start message
    app.run(debug=True)
