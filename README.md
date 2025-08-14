# MinuteMate - AI Meeting Note Taker

MinuteMate is a background service that listens to live meeting audio, transcribes it, and uses Natural Language Processing to automatically generate structured minutes, extract action items, and identify key dates. It provides a simple web interface to control recording and view the final results.

## Features

* **Live Audio Capture**: Records audio from the system's default microphone.
* **Automatic Silence Detection**: Stops recording automatically after 30 seconds of silence.
* **Offline Transcription**: Uses the `whisper-timestamped` library for accurate, local speech-to-text with word-level timestamps.
* **AI-Powered NLP**: Employs pre-trained Hugging Face models (`transformers`) to generate summaries and extract action items without external APIs.
* **Web Interface**: A simple, single-page UI to start/stop recording and view results.
* **Automatic Archiving**: Saves the final meeting notes as a `.txt` file on the server for every session.
* **File Upload**: Process existing audio files (`.wav`, `.mp3`, etc.) through the web UI.

## Project Structure

/minute_mate/
|-- meeting_minutes/            # Auto-generated folder for saved .txt notes
|-- app.py                      # The main Flask API server
|-- audio_listener.py           # Module for capturing microphone audio
|-- nlp_processor.py            # Module for summarizing and extracting info
|-- transcription_engine.py     # Module for converting audio to text
|-- index.html                  # The single-page web UI
|-- requirements.txt            # List of Python dependencies
|-- README.md                   # This file
`-- prompt_log.md               # Log of NLP methods tried


## Installation

### Prerequisites

* Python 3.9+
* [FFmpeg](https://ffmpeg.org/download.html) installed and available in your system's PATH.
    * **macOS**: `brew install ffmpeg`
    * **Windows**: `choco install ffmpeg`
    * **Debian/Ubuntu**: `sudo apt update && sudo apt install ffmpeg`
* **PortAudio** (for microphone access)
    * **macOS**: `brew install portaudio`
    * **Debian/Ubuntu**: `sudo apt-get install portaudio19-dev python3-pyaudio`

### Setup

1.  **Clone the repository:**
    ```
    git clone <your-repo-url>
    cd minute_mate
    ```
2.  **Create a virtual environment:**
    ```
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies from `requirements.txt`:**
    ```
    pip install -r requirements.txt
    ```
    *Note: The first time you run the application, the `transformers` and `whisper` libraries will download several GB of model files. This is a one-time process.*

## How to Run

1.  **Start the Backend Server:**
    Open a terminal in the project directory and run:
    ```
    python app.py
    ```
    The server will start on `http://127.0.0.1:5000`. You will see output indicating that the NLP models are being loaded.

2.  **Launch the Web UI:**
    Open the `index.html` file directly in your web browser (e.g., Chrome, Firefox).

## Usage

### Live Recording

1.  Open `index.html` in your browser.
2.  Click the **"Start Recording"** button. The status indicator will turn red.
3.  Speak into your default microphone.
4.  Click the **"Stop Recording"** button or remain silent for 30 seconds.
5.  The status will change to "Processing". Wait for the transcription and NLP analysis to complete.
6.  The results (summary, action items, etc.) will appear on the page.

### Uploading an Audio File

1.  Click the "Choose File" button and select a local audio file (e.g., `.wav`, `.mp3`).
2.  Click the **"Upload & Process"** button.
3.  The status will change to "Processing".
4.  The final results will appear on the page when ready.

## API Specification

The backend server exposes the following REST API endpoints:

* **`GET /status`**
    * **Description**: Returns the current status of the application.
    * **Response**:
        ```
        {
          "status": "idle" | "recording" | "processing",
          "current_meeting_id": "string-or-null"
        }
        ```
* **`POST /start_recording`**
    * **Description**: Starts a new recording session.
    * **Response**:
        ```
        {
          "message": "Recording started.",
          "meeting_id": "unique-uuid-string"
        }
        ```
* **`POST /stop_recording`**
    * **Description**: Stops the current recording and begins processing.
    * **Response**:
        ```
        { "message": "Recording stopped. Processing has begun." }
        ```
* **`POST /upload_audio`**
    * **Description**: Uploads an audio file for processing.
    * **Request Body**: `multipart/form-data` with a file field named `audio_file`.
    * **Response**:
        ```
        {
          "message": "File uploaded successfully. Processing has begun.",
          "meeting_id": "unique-uuid-string"
        }
        ```
* **`GET /minutes/<meeting_id>`**
    * **Description**: Retrieves the final processed notes for a specific meeting.
    * **Response**:
        ```
        {
          "meeting_id": "string",
          "summary": "string",
          "action_items": ["string", ...],
          "reminders": ["string", ...],
          "full_transcript": "string",
          "timed_transcript": [ { "words": [ { "text": "word", "start": 1.23, "end": 1.45 }, ... ] } ]
        }
        ```
