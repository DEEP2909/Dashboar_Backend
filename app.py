import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from werkzeug.utils import secure_filename
import datetime

# --- Supabase Configuration ---
# These will be set as environment variables on your hosting platform (e.g., Render)
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- Flask App Configuration ---
app = Flask(__name__)
CORS(app)

# --- API Endpoints ---

# Endpoint for the background image
@app.route('/background', methods=['GET'])
def get_background():
    try:
        response = supabase.table('app_data').select('background_url').limit(1).single().execute()
        url = response.data.get('background_url', '') if response.data else ''
        return jsonify({'url': url})
    except Exception as e:
        print(f"Error getting background: {e}")
        return jsonify({'url': ''})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    # Add a timestamp to make filenames unique
    unique_filename = f"{datetime.datetime.now().timestamp()}-{filename}"

    try:
        # Upload to Supabase Storage
        supabase.storage.from_('backgrounds').upload(unique_filename, file.read(), {
            "content-type": file.content_type
        })
        # Get the public URL of the uploaded file
        public_url = supabase.storage.from_('backgrounds').get_public_url(unique_filename)

        # Update the background_url in the app_data table
        # First, check if a row exists. If not, insert one.
        response = supabase.table('app_data').select('id').limit(1).execute()
        if response.data:
            # Update the existing row
            supabase.table('app_data').update({'background_url': public_url}).eq('id', response.data[0]['id']).execute()
        else:
            # Insert a new row
            supabase.table('app_data').insert({'background_url': public_url}).execute()

        return jsonify({'success': True, 'url': public_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoints for the To-Do list
@app.route('/todos', methods=['GET'])
def get_todos():
    response = supabase.table('todos').select('*').execute()
    return jsonify(response.data)

@app.route('/todos', methods=['POST'])
def update_todos():
    new_todos = request.json
    # For simplicity, we delete all and insert new ones.
    # A more advanced app would update/insert/delete individually.
    supabase.table('todos').delete().neq('id', -1).execute() # Delete all rows
    if new_todos:
        supabase.table('todos').insert(new_todos).execute()
    return jsonify({'success': True})

# Endpoints for Special Events
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

# --- Run the App (for local testing) ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
