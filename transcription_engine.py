# transcription_engine.py (v2 - with Timestamps)

# This script uses an enhanced version of Whisper to get word-level timestamps.

# --- Installation ---
# 1. Uninstall the original whisper if you have it:
#    pip uninstall openai-whisper
# 2. Install the timestamp-enabled version:
#    pip install whisper-timestamped
#
# You still need FFmpeg installed on your system.

import whisper_timestamped as whisper # Use the new library
import os
import time

# --- Configuration ---
MODEL_NAME = "tiny.en" 

def transcribe_audio_with_timestamps(file_path: str) -> dict:
    """
    Transcribes an audio file and returns the result with word-level timestamps.

    Args:
        file_path (str): The full path to the audio file.

    Returns:
        dict: The full transcription result object from whisper_timestamped,
              which includes text and a 'segments' list with word timings.
              Returns an empty dictionary on failure.
    """
    if not os.path.exists(file_path):
        print(f"Error: Audio file not found at '{file_path}'")
        return {}

    print(f"Transcription with timestamps started for: {file_path}")
    
    try:
        # 1. --- Load the Audio ---
        # This library has its own audio loading function.
        audio = whisper.load_audio(file_path)

        # 2. --- Load the Model ---
        model = whisper.load_model(MODEL_NAME, device="cpu") # Specify CPU for consistency
        
        # 3. --- Perform the Transcription ---
        print("Transcribing and aligning... (This may take a moment)")
        start_time = time.time()
        
        # The transcribe function is called directly from the library
        result = whisper.transcribe(model, audio, language="en")
        
        transcribe_time = time.time() - start_time
        print(f"Transcription finished in {transcribe_time:.2f} seconds.")

        # 4. --- Return the Full Result ---
        # The result object is a dictionary containing the full text and
        # a list of segments, which in turn contain lists of words with timestamps.
        return result

    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return {}

# --- Example Usage ---
if __name__ == '__main__':
    sample_file = 'sample_meeting.wav'
    
    if not os.path.exists(sample_file):
        print(f"\nTo run a test, please create a '{sample_file}' in this directory.")
    else:
        print("\n--- Running Timestamp Transcription Test ---")
        
        transcription_result = transcribe_audio_with_timestamps(sample_file)
        
        if transcription_result:
            print("\n--- Full Transcript ---")
            print(transcription_result["text"].strip())
            print("------------------------\n")
            
            print("--- Word Timestamps (first 10 words) ---")
            # The result is nested. We access segments, then words.
            word_count = 0
            for segment in transcription_result["segments"]:
                for word in segment["words"]:
                    if word_count < 10:
                        start_time = f"{word['start']:.2f}"
                        end_time = f"{word['end']:.2f}"
                        print(f"[{start_time}s - {end_time}s] {word['text']}")
                        word_count += 1
                    else:
                        break
                if word_count >= 10:
                    break
            print("----------------------------------------\n")

