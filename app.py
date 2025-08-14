# app.py (with Upload Functionality)

from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Thread
import os
import uuid
from werkzeug.utils import secure_filename # For safe filenames

# --- Import our custom modules ---
from audio_listener import AudioListener
from transcription_engine import transcribe_audio_with_timestamps
from nlp_processor import process_transcript

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Configuration ---
UPLOAD_FOLDER = '.' # Save uploads in the same directory
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'ogg'} # Common audio formats

# --- Global State Management ---
app_state = {
    "status": "idle",
    "current_meeting_id": None,
    "minutes_data": {}
}
listener = None

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Processing Pipeline Function (no changes needed) ---
def process_audio_pipeline(filepath, meeting_id):
    """This function runs the heavy tasks and handles final cleanup."""
    global listener
    print(f"Starting processing pipeline for {meeting_id}...")
    
    transcription_result = transcribe_audio_with_timestamps(filepath)
    if not transcription_result or not transcription_result.get("text"):
        print(f"Processing failed for {meeting_id}: Transcription returned no result.")
        app_state["status"] = "idle"
        app_state["minutes_data"][meeting_id] = {"error": "Transcription failed."}
        if listener: listener = None
        return

    processed_data = process_transcript(transcription_result["text"])
    
    final_minutes = {
        "meeting_id": meeting_id,
        "full_transcript": transcription_result["text"],
        "summary": processed_data["summary"],
        "action_items": processed_data["action_items"],
        "reminders": processed_data["reminders"],
        "timed_transcript": transcription_result["segments"]
    }
    
    app_state["minutes_data"][meeting_id] = final_minutes
    app_state["status"] = "idle"
    if listener: listener = None
    print(f"✅ Processing complete for {meeting_id}.")
    
    # Optional: Clean up the audio file
    # if os.path.exists(filepath):
    #     os.remove(filepath)

# --- API Endpoints ---

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": app_state["status"],
        "current_meeting_id": app_state["current_meeting_id"]
    })

# --- File Upload Endpoint ---
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if app_state["status"] != "idle":
        return jsonify({"error": "Application is busy."}), 409
        
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
        
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        meeting_id = str(uuid.uuid4())
        # Use a unique name to avoid conflicts
        saved_filename = f"upload_{meeting_id}.{filename.rsplit('.', 1)[1].lower()}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(filepath)

        # Update state and start processing
        app_state["status"] = "processing"
        app_state["current_meeting_id"] = meeting_id
        pipeline_thread = Thread(target=process_audio_pipeline, args=(filepath, meeting_id))
        pipeline_thread.start()

        return jsonify({
            "message": "File uploaded successfully. Processing has begun.",
            "meeting_id": meeting_id
        })
    else:
        return jsonify({"error": "File type not allowed."}), 400


@app.route('/start_recording', methods=['POST'])
def start_recording():
    global listener
    if app_state["status"] != "idle":
        return jsonify({"error": "Application is not idle."}), 409

    meeting_id = str(uuid.uuid4())
    output_filename = f"meeting_{meeting_id}.wav"
    listener = AudioListener(output_filename=output_filename)
    
    original_save_method = listener._save_recording
    def save_and_process():
        original_save_method()
        if os.path.exists(output_filename):
            pipeline_thread = Thread(target=process_audio_pipeline, args=(output_filename, meeting_id))
            pipeline_thread.start()
    listener._save_recording = save_and_process
    
    listener.start()
    app_state["status"] = "recording"
    app_state["current_meeting_id"] = meeting_id
    
    return jsonify({
        "message": "Recording started.",
        "meeting_id": meeting_id
    })

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    if app_state["status"] != "recording" or listener is None:
        return jsonify({"error": "Not currently recording."}), 400
    listener.stop()
    app_state["status"] = "processing"
    return jsonify({"message": "Recording stopped. Processing has begun."})

@app.route('/minutes/<meeting_id>', methods=['GET'])
def get_minutes(meeting_id):
    minutes = app_state["minutes_data"].get(meeting_id)
    if not minutes:
        return jsonify({"error": "Meeting ID not found or not yet processed."}), 404
    return jsonify(minutes)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
