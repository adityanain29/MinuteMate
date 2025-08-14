# nlp_processor.py (v2 - with Generative AI)

# This module uses pre-trained transformer models to process a transcript.

# --- Installation ---
# 1. Install PyTorch (CPU-only version is fine):
#    pip install torch torchvision torchaudio
# 2. Install the transformers library from Hugging Face:
#    pip install transformers

# Note: The first time you run this, the models (a few GB) will be
# downloaded and cached automatically.

from transformers import pipeline
import re

# --- Model Initialization ---
# We initialize the pipelines here to load the models only once.
# This is more efficient than loading them inside the functions.
try:
    # Pipeline for creating summaries
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    
    # Pipeline for classifying text without pre-defined labels
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    print("NLP models loaded successfully.")
except Exception as e:
    print(f"Error loading models: {e}")
    print("Please ensure you have an internet connection for the first run to download models.")
    summarizer = None
    classifier = None

# --- Component 1: GenAI Summarizer ---

def generate_summary_genai(text: str) -> str:
    """
    Generates a summary using a pre-trained abstractive summarization model.
    """
    if not summarizer:
        return "Summarizer model not loaded."
        
    # The model works best on text between 50 and 1024 characters.
    # We'll provide reasonable min/max lengths for the output summary.
    summary_list = summarizer(text, max_length=150, min_length=40, do_sample=False)
    
    return summary_list[0]['summary_text']


# --- Component 2: GenAI Action Item Extractor ---

def extract_action_items_genai(text: str) -> list[str]:
    """
    Extracts action items using a zero-shot classification model.
    It checks each sentence to see if it fits the "action item" category.
    """
    if not classifier:
        return ["Classifier model not loaded."]

    # Split the text into sentences. A simple split is often good enough.
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if not sentences:
        return []

    # The labels we want the model to classify each sentence against.
    candidate_labels = ["action item", "important point", "question", "general discussion"]
    
    action_items = []
    
    # We can classify sentences in batches for efficiency
    results = classifier(sentences, candidate_labels, multi_label=False)
    
    for result in results:
        # If the model's top prediction for a sentence is "action item"
        # with a confidence score above a certain threshold, we keep it.
        if result['labels'][0] == 'action item' and result['scores'][0] > 0.8:
            action_items.append(result['sequence'])
            
    return action_items


# --- Component 3: Date Extractor (Regex is still good for this) ---

def extract_dates(text: str) -> list[str]:
    """
    Extracts dates using regular expressions. This is still a reliable method
    for specific, structured date formats.
    """
    patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'(next\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))',
        r'(tomorrow)'
    ]
    found_dates = []
    for pattern in patterns:
        found_dates.extend(re.findall(pattern, text, re.IGNORECASE))
    return list(set(found_dates))


# --- Main Processor Function ---

def process_transcript(transcript: str) -> dict:
    """
    The main function that orchestrates the NLP processing with GenAI.
    """
    print("Processing transcript with GenAI models...")
    
    summary = generate_summary_genai(transcript)
    actions = extract_action_items_genai(transcript)
    dates = extract_dates(transcript)
    
    print("Processing complete.")
    
    return {
        "summary": summary,
        "action_items": actions,
        "reminders": dates
    }


# --- Example Usage ---
if __name__ == '__main__':
    sample_transcript = """
    Hello team, welcome to the sync-up. For our first action item, Alice will need to finalize the Q3 report. 
    The goal is to improve our key metrics. Bob, can you please schedule the client follow-up for next Tuesday? 
    I think that's a critical step. We must also remember the deadline of 2025-09-01 for the budget submission.
    The task for engineering is to deploy the new feature. Thank you.
    """
    
    print("--- Running NLP Processor (GenAI) Test ---")
    if summarizer and classifier:
        processed_data = process_transcript(sample_transcript)
        
        print("\n--- Processed Output ---")
        print("\nSummary:")
        print(processed_data["summary"])
        
        print("\nAction Items:")
        for item in processed_data["action_items"]:
            print(f"- {item}")
            
        print("\nReminders (Detected Dates):")
        for item in processed_data["reminders"]:
            print(f"- {item}")
    else:
        print("\nCould not run test because models failed to load.")

