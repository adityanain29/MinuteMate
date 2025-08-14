# audio_listener.py

import pyaudio
import wave
import threading
import time
import numpy as np
from collections import deque

class AudioListener:
    """
    A class to handle background audio recording from the default microphone,
    detect silence, and save the recording.
    """
    def __init__(self, output_filename="meeting_audio.wav"):
        # --- Audio Configuration ---
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        
        # --- Silence Detection Configuration ---
        self.SILENCE_THRESHOLD = 500
        self.SILENCE_SECONDS = 30
        
        self.output_filename = output_filename
        
        # --- State Management ---
        self.recording = False
        self.frames = deque()
        self.silence_start_time = None
        self.thread = None
        self.p = pyaudio.PyAudio()

    def _recording_loop(self):
        """The main loop that runs in the background thread."""
        try:
            # By leaving input_device_index as None, PyAudio uses the default mic
            stream = self.p.open(format=self.FORMAT,
                                 channels=self.CHANNELS,
                                 rate=self.RATE,
                                 input=True,
                                 frames_per_buffer=self.CHUNK)
            print("✅ Listener started. Recording from default microphone...")
            
            while self.recording:
                data = stream.read(self.CHUNK)
                self.frames.append(data)
                
                # --- Silence Detection Logic ---
                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data.astype(float)**2))
                
                if rms < self.SILENCE_THRESHOLD:
                    if self.silence_start_time is None:
                        self.silence_start_time = time.time()
                    elif time.time() - self.silence_start_time > self.SILENCE_SECONDS:
                        print(f"🔇 Detected {self.SILENCE_SECONDS} seconds of silence. Stopping...")
                        self.stop()
                else:
                    self.silence_start_time = None

            stream.stop_stream()
            stream.close()
            print("✅ Listener stopped.")

        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            self._save_recording()

    def _save_recording(self):
        """Saves the buffered audio frames to a WAV file."""
        if not self.frames:
            print("No audio was recorded.")
            return

        print(f"💾 Saving recording to {self.output_filename}...")
        wf = wave.open(self.output_filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(list(self.frames)))
        wf.close()
        print("💾 Save complete.")
        self.frames.clear()

    def start(self):
        """Starts the recording in a new thread."""
        if self.recording:
            print("Already recording.")
            return
        self.recording = True
        self.thread = threading.Thread(target=self._recording_loop)
        self.thread.start()

    def stop(self):
        """Stops the recording."""
        if not self.recording:
            return
        self.recording = False
        print("Stopping listener...")

    def __del__(self):
        """Ensure PyAudio is terminated when the object is destroyed."""
        self.p.terminate()

# --- Example Usage ---
if __name__ == '__main__':
    listener = AudioListener()
    print("Starting the MinuteMate listener (using default microphone).")
    print("It will stop automatically after 30 seconds of silence.")
    print("Or, press ENTER to stop it manually at any time.")
    listener.start()
    input() 
    listener.stop()
    if listener.thread:
        listener.thread.join()
    print("\nProgram finished.")
