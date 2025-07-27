import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from werkzeug.utils import secure_filename
import datetime

# --- Supabase Configuration ---
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- Flask App Configuration ---
app = Flask(__name__)
CORS(app)

# --- API Endpoints ---

@app.route('/background', methods=['GET'])
def get_background():
    try:
        response = supabase.table('app_data').select('background_url').eq('id', 1).single().execute()
        url = response.data.get('background_url', '') if response.data else ''
        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'url': '', 'error': str(e)})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.datetime.now().timestamp()}-{filename}"

    try:
        # 1. Upload to Supabase Storage
        supabase.storage.from_('backgrounds').upload(unique_filename, file.read(), {"content-type": file.content_type})
        
        # 2. Get the public URL
        public_url = supabase.storage.from_('backgrounds').get_public_url(unique_filename)

        # 3. Update the single row in the app_data table
        supabase.table('app_data').update({'background_url': public_url}).eq('id', 1).execute()

        return jsonify({'success': True, 'url': public_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoints for To-Do list and Special Events (These remain the same)
@app.route('/todos', methods=['GET'])
def get_todos():
    response = supabase.table('todos').select('*').execute()
    return jsonify(response.data)

@app.route('/todos', methods=['POST'])
def update_todos():
    new_todos = request.json
    supabase.table('todos').delete().neq('id', -1).execute()
    if new_todos:
        supabase.table('todos').insert(new_todos).execute()
    return jsonify({'success': True})

@app.route('/events', methods=['GET'])
def get_events():
    response = supabase.table('special_events').select('*').execute()
    return jsonify(response.data)

@app.route('/events', methods=['POST'])
def update_events():
    new_events = request.json
    supabase.table('special_events').delete().neq('id', -1).execute()
    if new_events:
        supabase.table('special_events').insert(new_events).execute()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
