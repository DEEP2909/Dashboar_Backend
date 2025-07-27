import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from werkzeug.utils import secure_filename
import datetime
import traceback

# --- Supabase Configuration ---
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# --- Startup Check ---
if not url or not key:
    print("FATAL ERROR: SUPABASE_URL and SUPABASE_KEY environment variables are not set.")
else:
    print("Supabase credentials loaded successfully.")

supabase: Client = create_client(url, key)

# --- Flask App Configuration ---
app = Flask(__name__)
CORS(app)

# --- API Endpoints ---

@app.route('/background', methods=['GET'])
def get_background():
    try:
        response = supabase.table('app_data').select('background_url').limit(1).single().execute()
        url = response.data.get('background_url', '') if response.data else ''
        return jsonify({'url': url})
    except Exception as e:
        print(f"Error getting background: {e}")
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
        file_content = file.read()
        file_mimetype = file.content_type
        
        # Step 1: Upload to Storage
        supabase.storage.from_('backgrounds').upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": file_mimetype}
        )
        
        # Step 2: Get Public URL
        public_url = supabase.storage.from_('backgrounds').get_public_url(unique_filename)

        # Step 3: Update or Insert into Database (Self-healing logic)
        response = supabase.table('app_data').select('id').limit(1).execute()
        if response.data:
            row_id = response.data[0]['id']
            supabase.table('app_data').update({'background_url': public_url}).eq('id', row_id).execute()
        else:
            supabase.table('app_data').insert({'background_url': public_url}).execute()
        
        return jsonify({'success': True, 'url': public_url})

    except Exception as e:
        print(f"!!! AN EXCEPTION OCCURRED DURING UPLOAD: {e} !!!")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Endpoints for To-Do list and Special Events (These remain the same)
@app.route('/todos', methods=['GET'])
def get_todos():
    response = supabase.table('todos').select('*').execute()
    return jsonify(response.data)

@app.route('/todos', methods=['POST'])
def update_todos():
    try:
        new_todos = request.json
        # First, delete all existing todos for this user
        supabase.table('todos').delete().neq('id', -1).execute() # This deletes all rows
        # Then, insert the new list if it's not empty
        if new_todos:
            # ** THE FIX IS HERE: changed new_dos to new_todos **
            supabase.table('todos').insert(new_todos).execute()
        return jsonify({'success': True})
    except Exception as e:
        print(f"!!! AN EXCEPTION OCCURRED IN UPDATE_TODOS: {e} !!!")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/events', methods=['GET'])
def get_events():
    response = supabase.table('special_events').select('*').execute()
    return jsonify(response.data)

@app.route('/events', methods=['POST'])
def update_events():
    try:
        new_events = request.json
        supabase.table('special_events').delete().neq('id', -1).execute()
        if new_events:
            supabase.table('special_events').insert(new_events).execute()
        return jsonify({'success': True})
    except Exception as e:
        print(f"!!! AN EXCEPTION OCCURRED IN UPDATE_EVENTS: {e} !!!")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
