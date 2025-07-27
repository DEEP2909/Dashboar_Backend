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
        print(f"Serving background URL: {url}")
        return jsonify({'url': url})
    except Exception as e:
        print(f"Error getting background: {e}")
        return jsonify({'url': '', 'error': str(e)})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        print("Upload error: No file part in request")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        print("Upload error: No file selected")
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.datetime.now().timestamp()}-{filename}"
    print(f"Attempting to upload file: {unique_filename}")

    try:
        # 1. Read file content into memory
        file_content = file.read()
        print(f"File read into memory, size: {len(file_content)} bytes")

        # 2. Upload to Supabase Storage
        print("Uploading to Supabase storage...")
        supabase.storage.from_('backgrounds').upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        print("Storage upload step finished.")

        # 3. Get the public URL
        print("Getting public URL...")
        public_url = supabase.storage.from_('backgrounds').get_public_url(unique_filename)
        print(f"Got public URL: {public_url}")

        # 4. Update the single row in the app_data table
        print("Updating database with new URL...")
        update_response = supabase.table('app_data').update({'background_url': public_url}).eq('id', 1).execute()
        print(f"Database update response: {update_response.data}")

        if not update_response.data:
             raise Exception("Database update failed, no data returned from update operation.")

        print("Upload process successful.")
        return jsonify({'success': True, 'url': public_url})
    except Exception as e:
        # Log the full error to the server logs
        print(f"An exception occurred during upload: {e}")
        traceback.print_exc()
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
