# NLP Model & Rule Log for MinuteMate

This document tracks the "prompts" and logic used for the Natural Language Processing tasks in this project. Since we are using pre-trained models and rule-based methods instead of a generative LLM, our "prompts" are the specific models and patterns we've implemented.

---

### **V1: Rule-Based Extraction (Initial Prototype)**

-   **Method**: Used `spaCy` for sentence segmentation and a basic extractive summarizer based on word frequency. Action items and dates were extracted using Python's `re` (regular expressions) module.
-   **"Prompts" / Rules**:
    -   **Action Items**: Searched for sentences containing keywords like `["will", "need to", "must", "action item", "assign", "task is"]`.
    -   **Dates**: Searched for regex patterns like `\d{4}-\d{2}-\d{2}` and `next Tuesday`.
-   **Result**: This approach was fast and worked for very clearly phrased sentences. However, it was brittle. It often missed action items that didn't use the exact keywords and failed to identify dates written in natural language (e.g., "September 15th, 2025"). The summary was often just a collection of the longest sentences.
-   **Decision**: This method was not accurate enough for reliable use. We decided to move to a more intelligent, model-based approach.

---

### **V2: Specialized Transformer Models (Current Version)**

-   **Method**: Switched to using dedicated, pre-trained models from the Hugging Face `transformers` library, running entirely offline on the CPU.
-   **"Prompts" / Models**:
    -   **Summarization**:
        -   **Model**: `sshleifer/distilbart-cnn-12-6`
        -   **Reasoning**: This is a well-regarded abstractive summarization model. Instead of just picking sentences, it *generates* a new, coherent summary, leading to much more natural-sounding results.
    -   **Action Item Extraction**:
        -   **Model**: `facebook/bart-large-mnli` (used in a Zero-Shot Classification pipeline).
        -   **Reasoning**: This powerful model can classify sentences against labels it has never been trained on. We "prompt" it by asking it to classify each sentence as an `"action item"`, `"question"`, `"important point"`, etc. This is far more robust than simple keyword matching, as it understands the *intent* of the sentence. We use a confidence threshold of `> 0.8` to ensure only clear action items are selected.
    -   **Date Extraction**:
        -   **Method**: Kept the `regex` approach from V1.
        -   **Reasoning**: For structured date formats, regex is still the most reliable and efficient method. A full language model is overkill for this specific task and could be less precise.
-   **Result**: This hybrid approach provides a significant improvement in accuracy. The summary is more readable, and the action item detection is much more reliable.
-   **Decision**: This is the current, implemented version as it provides the best balance of accuracy and performance using free, open-source tools.
