# test_minutemate.py

import pytest
import os
import time
import wave
from unittest.mock import MagicMock, patch

# Import the components from your application that we need to test
from app import app as flask_app  # The Flask app object
from audio_listener import AudioListener
from transcription_engine import transcribe_audio_with_timestamps

# --- Test Fixtures ---
# Fixtures are reusable setup functions for your tests.

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def dummy_wav_file(tmp_path):
    """Create a temporary, silent WAV file for testing."""
    file_path = tmp_path / "test.wav"
    # These parameters create a 1-second silent audio file
    with wave.open(str(file_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b'\x00\x00' * 16000) # 1 second of silence
    return str(file_path)

# --- 1. API Endpoint Tests ---

def test_get_status_endpoint(client):
    """Test if the /status endpoint returns the initial 'idle' state."""
    response = client.get('/status')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'idle'
    assert json_data['current_meeting_id'] is None

# We use 'patch' to temporarily replace parts of our code with mocks.
# This prevents the tests from actually starting a recording or running the slow AI models.
@patch('app.AudioListener')
@patch('app.process_audio_pipeline')
def test_recording_lifecycle(mock_process_pipeline, mock_audio_listener, client):
    """Test the full start -> stop recording lifecycle via API calls."""
    # --- Test Start Recording ---
    response = client.post('/start_recording')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['message'] == 'Recording started.'
    assert 'meeting_id' in json_data

    # Check the status after starting
    response = client.get('/status')
    assert response.get_json()['status'] == 'recording'

    # --- Test Stop Recording ---
    response = client.post('/stop_recording')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Recording stopped. Processing has begun.'

    # Check the status after stopping
    response = client.get('/status')
    assert response.get_json()['status'] == 'processing'
    
    # We assert that our mocks were used, but we don't need to check the pipeline
    # itself since that's a separate unit of work.
    assert mock_audio_listener.called
    # The pipeline is called in a separate thread, so we can't easily test its call here.
    # The main goal is to confirm the API endpoints respond correctly.

# --- 2. Transcription Call Test ---

@patch('transcription_engine.whisper.transcribe')
def test_transcription_call(mock_whisper_transcribe, dummy_wav_file):
    """
    Test that the transcription engine calls the whisper library correctly.
    We mock the actual transcription to avoid running the slow AI model.
    """
    # Set a return value for our mock function
    mock_whisper_transcribe.return_value = {"text": "This is a test."}
    
    # Call our function with the dummy audio file
    result = transcribe_audio_with_timestamps(dummy_wav_file)
    
    # Assert that our function was called
    mock_whisper_transcribe.assert_called_once()
    
    # Assert that our function returned the mocked value
    assert result["text"] == "This is a test."

# --- 3. Audio Capture Test ---

@patch('audio_listener.pyaudio.PyAudio')
def test_audio_capture(mock_pyaudio, tmp_path):
    """
    Test the AudioListener's ability to capture and buffer audio.
    We mock the PyAudio library to simulate microphone input without hardware.
    """
    # --- Setup the Mock ---
    mock_stream = MagicMock()
    fake_audio_chunk = b'\x00' * 1024
    
    # Make the mock PyAudio instance return our mock stream
    mock_pyaudio_instance = mock_pyaudio.return_value
    mock_pyaudio_instance.open.return_value = mock_stream
    mock_pyaudio_instance.get_sample_size.return_value = 2

    # --- Run the Listener ---
    output_file = tmp_path / "test_capture.wav"
    listener = AudioListener(output_filename=str(output_file))

    # Use a side effect to control the recording loop reliably
    def read_side_effect(*args, **kwargs):
        # After the first read, we signal the loop to stop.
        if mock_stream.read.call_count >= 1:
            listener.recording = False
        return fake_audio_chunk

    mock_stream.read.side_effect = read_side_effect

    # The side_effect will stop the loop from within the thread.
    listener.start()
    listener.thread.join() # Wait for the thread to finish

    # --- Assertions ---
    mock_pyaudio_instance.open.assert_called_once()
    assert mock_stream.read.called
    
    # *** FIX: Check the content of the saved file, not the in-memory buffer. ***
    # This is more robust because it confirms the entire process, and it avoids the
    # race condition where the buffer is cleared before the assertion runs.
    assert os.path.exists(output_file)
    with wave.open(str(output_file), 'rb') as wf:
        frames_written = wf.readframes(wf.getnframes())
        assert frames_written == fake_audio_chunk
