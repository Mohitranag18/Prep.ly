# Handles keyword extraction from text chunks using Gemini API

import streamlit as st
import google.generativeai as genai
import json
import time
import pathlib
import uuid
import os
import tempfile

try:
    from config import GEMINI_API_KEYS
except ImportError:
    st.error("Error: Could not find config.py or GEMINI_API_KEYS within it.")
    st.info("Please create a config.py file with your Gemini API keys: `GEMINI_API_KEYS = ['YOUR_API_KEY_HERE']`")
    GEMINI_API_KEYS = []

@st.cache_data(ttl=3600) # Cache keyword results for 1 hour
def extract_keywords_gemini(
    transcript_chunk: str | None,
    num_keywords: int = 7 # Increased default slightly to capture more nuance
) -> list[str]:
    """
    Extracts keywords using the Gemini API

    Args:
        transcript_chunk: The relevant transcript chunk text (optional).
        num_keywords: The desired number of keywords.

    Returns:
        A list of extracted keywords, or an empty list if an error occurs or no text is provided.
    """
    if not GEMINI_API_KEYS:
        st.error("No Gemini API keys configured. Please add keys to config.py.")
        return []

    # Combine available text sources, giving clear labels
    input_text_parts = []
    if transcript_chunk:
        input_text_parts.append(f"Transcript Snippet: {transcript_chunk}")

    if not input_text_parts:
        st.warning("No transcript chunk provided for keyword extraction.")
        return []

    combined_text = "\n\n".join(input_text_parts)

    extracted_keywords = []
    success = False

    try:
 
        generation_config = {"temperature": 0.4}
        # Safety settings appropriate for general text analysis
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        prompt = f"""Analyze the following text sources from a YouTube video: a Transcript Snippet.
Extract the {num_keywords} most important and relevant keywords or key topics that represent the **main subject** of the video.

Use the Transcript Snippet primarily for context and to identify specific terms mentioned, but give less weight to topics from the transcript. Focus on specific entities, concepts, technologies, or main ideas.

Respond ONLY with a valid JSON list of strings, where each string is a keyword or key topic. Do not include any introductory text or markdown formatting.
Example format:
["specific term from transcript", "related entity"]
"""

        # --- Loop through API keys ---
        for i, key in enumerate(GEMINI_API_KEYS):
            st.info(f"Attempting keyword extraction with API key #{i+1}...")
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(model_name="gemini-1.5-pro",
                                              generation_config=generation_config,
                                              safety_settings=safety_settings)

                # Send combined text and the new prompt
                response = model.generate_content([
                    combined_text, # Use the combined text with labels
                    prompt
                ])

                # --- Robust response handling ---
                if not response.parts:
                     st.warning(f"Gemini response (key #{i+1}) was empty.")
                     if response.candidates and response.prompt_feedback.block_reason:
                         st.error(f"Request blocked (key #{i+1}) due to: {response.prompt_feedback.block_reason}")
                         success = False # Mark as failed
                         break 
                     st.warning(f"Response from key #{i+1} was empty, trying next key if available.")
                     continue # Try next key

                # Clean potential markdown code fences
                cleaned_response = response.text.strip().lstrip('```json').rstrip('```').strip()

                # Validate JSON response
                parsed_list = json.loads(cleaned_response)
                if isinstance(parsed_list, list) and all(isinstance(s, str) for s in parsed_list):
                    st.success(f"Gemini extracted keywords using key #{i+1}: {', '.join(parsed_list)}")
                    extracted_keywords = parsed_list[:num_keywords] # Ensure correct number
                    success = True
                    break # Success, exit the loop
                else:
                    st.warning(f"Gemini keyword response (key #{i+1}) was not a valid JSON list of strings: '{cleaned_response}'")
                    success = False
                    break

            except json.JSONDecodeError as json_err:
                response_text = getattr(response, 'text', 'N/A') # Safely get response text
                st.warning(f"Gemini keyword response (key #{i+1}) was not valid JSON: {json_err}. Response: '{response_text}'")
                success = False
                break

            except Exception as e:
                # Check for specific block reason if possible
                block_reason_str = "safety settings or other reasons"
                if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback') and getattr(e.response.prompt_feedback, 'block_reason', None):
                     block_reason_str = f"'{e.response.prompt_feedback.block_reason}'"

                if "response was blocked" in str(e).lower() or (hasattr(e, 'response') and getattr(e.response, 'prompt_feedback', None)):
                    st.error(f"Gemini keyword extraction blocked (key #{i+1}) likely due to {block_reason_str}.")
                    success = False
                    break 

                st.warning(f"Gemini API call failed for keyword extraction (key #{i+1}): {type(e).__name__} - {e}")
                # If it's the last key, report final failure
                if i == len(GEMINI_API_KEYS) - 1:
                    st.error("All Gemini API keys failed for keyword extraction.")
                    # extracted_keywords remains []
 
    except Exception as e:
        # Catch unexpected errors outside the API loop (e.g., file writing)
        st.error(f"An unexpected error occurred during the keyword extraction process: {e}")
        extracted_keywords = [] # Ensure failure returns empty list


    if not success and not extracted_keywords:
        st.warning("Keyword extraction failed after trying available API keys.")

    return extracted_keywords
