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
        response = supabase.table('app_data').select('background_url').eq('id', 1).single().execute()
        url = response.data.get('background_url', '') if response.data else ''
        return jsonify({'url': url})
    except Exception as e:
        print(f"Error getting background: {e}")
        return jsonify({'url': '', 'error': str(e)})

@app.route('/upload', methods=['POST'])
def upload_file():
    print("--- New Upload Request Received ---")
    if 'file' not in request.files:
        print("Upload error: No file part in request")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        print("Upload error: No file selected")
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.datetime.now().timestamp()}-{filename}"
    
    try:
        file_content = file.read()
        file_mimetype = file.content_type
        print(f"Step 1/3: Attempting to upload '{unique_filename}' to bucket 'backgrounds'.")
        
        # Step 1: Upload to Storage
        supabase.storage.from_('backgrounds').upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": file_mimetype}
        )
        print("Step 1/3: SUCCESS - File uploaded to storage.")
        
        # Step 2: Get Public URL
        print("Step 2/3: Getting public URL...")
        public_url = supabase.storage.from_('backgrounds').get_public_url(unique_filename)
        print(f"Step 2/3: SUCCESS - Got public URL: {public_url}")

        # Step 3: Update Database
        print("Step 3/3: Updating database...")
        update_response = supabase.table('app_data').update({'background_url': public_url}).eq('id', 1).execute()
        
        if not update_response.data:
             raise Exception("Database update failed. The server did not receive a confirmation after the update.")

        print(f"Step 3/3: SUCCESS - Database updated. Response: {update_response.data}")
        print("--- Upload process successful. ---")
        return jsonify({'success': True, 'url': public_url})

    except Exception as e:
        print("!!! AN EXCEPTION OCCURRED DURING UPLOAD !!!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {e}")
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
