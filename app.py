import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
DB_FILE = 'database.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app) # Allows your Netlify frontend to talk to this backend

# Default data to be used if the database file doesn't exist
DEFAULT_DATA = {
    "background_url": "",
    "todos": [],
    "special_events": [
        {"name": "First Talk Anniversary", "date": "2023-09-22"},
        {"name": "Her Birthday", "date": "2004-01-06"},
        {"name": "My Birthday", "date": "2004-09-29"},
        {"name": "Feelings Expressed Anniversary", "date": "2023-11-08"},
        {"name": "She Proposed! Anniversary", "date": "2023-11-24"},
        {"name": "First Met Anniversary", "date": "2023-11-15"},
        {"name": "First Kiss Anniversary", "date": "2024-05-05"}
    ]
}

# --- Helper Functions for Database ---
def read_db():
    """Reads the entire database from the JSON file.
    If the file doesn't exist or is empty, it returns the default data."""
    if not os.path.exists(DB_FILE):
        return DEFAULT_DATA
    try:
        with open(DB_FILE, 'r') as f:
            # Check if file is empty
            if os.path.getsize(DB_FILE) == 0:
                return DEFAULT_DATA
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return DEFAULT_DATA

def write_db(data):
    """Writes the entire database to the JSON file."""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- API Endpoints ---

# Endpoint for the background image
@app.route('/background', methods=['GET'])
def get_background():
    db = read_db()
    return jsonify({'url': db.get('background_url', '')})

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '' or not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
        return jsonify({'error': 'Invalid file'}), 400
    
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    db = read_db()
    db['background_url'] = f'/uploads/{filename}'
    write_db(db)
    
    return jsonify({'success': True, 'url': db['background_url']})

# Endpoints for the To-Do list
@app.route('/todos', methods=['GET'])
def get_todos():
    db = read_db()
    return jsonify(db.get('todos', []))

@app.route('/todos', methods=['POST'])
def update_todos():
    new_todos = request.json
    db = read_db()
    db['todos'] = new_todos
    write_db(db)
    return jsonify({'success': True})

# Endpoints for Special Events
@app.route('/events', methods=['GET'])
def get_events():
    db = read_db()
    return jsonify(db.get('special_events', []))

@app.route('/events', methods=['POST'])
def update_events():
    new_events = request.json
    db = read_db()
    db['special_events'] = new_events
    write_db(db)
    return jsonify({'success': True})

# --- Run the App (for local testing) ---
if __name__ == '__main__':
    # Create uploads folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # The host='0.0.0.0' makes it accessible from your local network
    app.run(host='0.0.0.0', port=5000, debug=True)
