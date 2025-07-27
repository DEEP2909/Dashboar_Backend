print("--- Python script starting to load... ---")

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import datetime
import traceback

# --- Create uploads folder immediately ---
# This ensures the folder exists before the app tries to use it.
try:
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    print("--- 'uploads' directory is ready. ---")
except Exception as e:
    print(f"FATAL STARTUP ERROR: Could not create 'uploads' directory. Error: {e}")

# --- Supabase Configuration and Startup Check ---
supabase = None
try:
    print("--- Loading environment variables... ---")
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("FATAL STARTUP ERROR: SUPABASE_URL and/or SUPABASE_KEY environment variables are not set.")
    else:
        print("--- Supabase credentials found. Initializing client... ---")
        from supabase import create_client, Client
        supabase: Client = create_client(url, key)
        print("--- Supabase client initialized successfully. ---")

except ImportError as e:
    print(f"FATAL STARTUP ERROR: Failed to import a required library. Please check requirements.txt. Error: {e}")
except Exception as e:
    print(f"FATAL STARTUP ERROR: An unexpected error occurred during initialization. Error: {e}")


# --- Flask App Configuration ---
app = Flask(__name__)
CORS(app)
print("--- Flask app configured. Defining routes... ---")


# --- API Endpoints ---

@app.route('/background', methods=['GET'])
def get_background():
    if not supabase: return jsonify({'error': 'Supabase client not initialized'}), 500
    try:
        response = supabase.table('app_data').select('background_url').limit(1).single().execute()
        url = response.data.get('background_url', '') if response.data else ''
        return jsonify({'url': url})
    except Exception as e:
        print(f"Error getting background: {e}")
        return jsonify({'url': '', 'error': str(e)})

@app.route('/upload', methods=['POST'])
def upload_file():
    if not supabase: return jsonify({'error': 'Supabase client not initialized'}), 500
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
        
        supabase.storage.from_('backgrounds').upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": file_mimetype}
        )
        public_url = supabase.storage.from_('backgrounds').get_public_url(unique_filename)

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

@app.route('/todos', methods=['GET'])
def get_todos():
    if not supabase: return jsonify({'error': 'Supabase client not initialized'}), 500
    response = supabase.table('todos').select('*').execute()
    return jsonify(response.data)

@app.route('/todos', methods=['POST'])
def update_todos():
    if not supabase: return jsonify({'error': 'Supabase client not initialized'}), 500
    try:
        new_todos = request.json
        supabase.table('todos').delete().neq('id', -1).execute()
        if new_todos:
            supabase.table('todos').insert(new_todos).execute()
        return jsonify({'success': True})
    except Exception as e:
        print(f"!!! AN EXCEPTION OCCURRED IN UPDATE_TODOS: {e} !!!")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/events', methods=['GET'])
def get_events():
    if not supabase: return jsonify({'error': 'Supabase client not initialized'}), 500
    response = supabase.table('special_events').select('*').execute()
    return jsonify(response.data)

@app.route('/events', methods=['POST'])
def update_events():
    if not supabase: return jsonify({'error': 'Supabase client not initialized'}), 500
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

print("--- Script loaded and routes defined. Ready to run. ---")
