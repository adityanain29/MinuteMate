# app.py 

from flask import Flask, jsonify
from flask_cors import CORS
from threading import Thread
import os
import uuid

# --- Import our custom modules ---
from audio_listener import AudioListener
from transcription_engine import transcribe_audio_with_timestamps
from nlp_processor import process_transcript

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Global State Management ---
app_state = {
    "status": "idle",
    "current_meeting_id": None,
    "minutes_data": {}
}
listener = None

# --- Processing Pipeline Function ---
def process_audio_pipeline(filepath, meeting_id):
    """This function runs the heavy tasks and handles final cleanup."""
    global listener
    print(f"Starting processing pipeline for {meeting_id}...")
    
    transcription_result = transcribe_audio_with_timestamps(filepath)
    if not transcription_result or not transcription_result.get("text"):
        print(f"Processing failed for {meeting_id}: Transcription returned no result.")
        app_state["status"] = "idle"
        app_state["minutes_data"][meeting_id] = {"error": "Transcription failed."}
        listener = None
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
    
    # --- *** NEW: Automatically save results to a text file *** ---
    try:
        # Create a folder for minutes if it doesn't exist
        if not os.path.exists('meeting_minutes'):
            os.makedirs('meeting_minutes')
            
        # Define the filename using the meeting ID to make it unique
        output_filename = f"meeting_minutes/minutes_{meeting_id}.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write("MinuteMate Meeting Notes\n")
            f.write("=========================\n\n")
            f.write(f"Meeting ID: {meeting_id}\n\n")
            
            f.write("## Summary\n")
            f.write(f"{final_minutes['summary']}\n\n")
            
            f.write("## Action Items\n")
            if final_minutes['action_items']:
                for item in final_minutes['action_items']:
                    f.write(f"- {item}\n")
            else:
                f.write("No action items detected.\n")
            f.write("\n")

            f.write("## Reminders & Dates\n")
            if final_minutes['reminders']:
                for item in final_minutes['reminders']:
                    f.write(f"- {item}\n")
            else:
                f.write("No reminders detected.\n")
            f.write("\n")
            
            f.write("## Full Transcript\n")
            f.write("-----------------\n")
            f.write(final_minutes['full_transcript'])
            
        print(f"✅ Successfully saved minutes to {output_filename}")

    except Exception as e:
        print(f"❌ Error saving minutes to file: {e}")
    # --- End of new section ---
    
    # Final cleanup
    app_state["status"] = "idle"
    listener = None
    print(f"✅ Processing complete for {meeting_id}. Listener has been cleared.")
    
    # Optional: Clean up the original audio file
    # if os.path.exists(filepath):
    #     os.remove(filepath)

# --- API Endpoints (No changes below this line) ---

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": app_state["status"],
        "current_meeting_id": app_state["current_meeting_id"]
    })

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
