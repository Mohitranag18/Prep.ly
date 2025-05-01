import os
import json
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import google.generativeai as genai
from django.conf import settings
from urllib.parse import urlparse, parse_qs
import re


# Initialize Gemini AI
genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)

def extract_video_id(url):
    """Extracts YouTube video ID from various URL formats."""
    if not url:
        return None
    # Standard URL: https://www.youtube.com/watch?v=VIDEO_ID
    # Short URL: https://youtu.be/VIDEO_ID
    # Embed URL: https://www.youtube.com/embed/VIDEO_ID
    try:
        parsed_url = urlparse(url)
        if "youtube.com" in parsed_url.netloc:
            if parsed_url.path == "/watch":
                return parse_qs(parsed_url.query).get("v", [None])[0]
            elif parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/embed/")[1].split("?")[0]
            elif parsed_url.path.startswith("/v/"):
                 return parsed_url.path.split("/v/")[1].split("?")[0]
        elif "youtu.be" in parsed_url.netloc:
            return parsed_url.path[1:].split("?")[0]
    except Exception as e:
        return None
    return None # Added explicit return None if no format matches

def approximate_tokens(text: str) -> int:
    """Estimate token count by splitting on whitespace."""
    return len(text.split())


def get_transcript(video_id: str) -> dict | None:
    """
    Fetches the English transcript (manual preferred, fallback to auto-generated) for a YouTube video.
    Returns a dict with 'transcript' (list of segments), 'text' (full concatenated), and 'token_count'.
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript(['en'])

        segments = transcript.fetch()
        full_text = " ".join(segment.text for segment in segments)

        return {
            'transcript': segments,
            'text': full_text,
            'token_count': approximate_tokens(full_text)
        }
    except (TranscriptsDisabled, NoTranscriptFound):
        return None


import json
import re
import google.generativeai as genai
from django.conf import settings

def extract_keywords_gemini(transcript_chunk: str, num_keywords: int = 7) -> list[str]:
    """
    Extracts keywords from a transcript snippet using the Gemini API.
    Returns a list of keywords or an empty list on failure.
    """
    if not settings.GOOGLE_GEMINI_API_KEY or not transcript_chunk:
        return []

    prompt = f"""
Analyze the following text and extract the {num_keywords} most important and relevant keywords or topics that represent the main subject.

Text:
{transcript_chunk}

Respond ONLY with a valid JSON list of strings. Example:
["keyword1", "keyword2", "keyword3"]
"""

    # Configure Gemini
    genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",  # or "gemini-1.0-pro"
            generation_config={"temperature": 0.4},
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
        )

        response = model.generate_content(prompt)

        # Extract JSON array from response using regex
        match = re.search(r"\[[^\]]+\]", response.text, re.DOTALL)
        if match:
            keywords = json.loads(match.group(0))
            if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
                return keywords[:num_keywords]
    except Exception as e:
        print(f"Error extracting keywords: {e}")

    return []


import json

def get_practice_questions_from_gemini(keywords: list[str]) -> list[dict]:
    """
    Uses Gemini API to generate practice questions with platform links based on keywords.
    Returns a list of dicts: [{ "title": "question", "link": "url" }]
    """
    if not keywords:
        return []

    prompt = f"""
You are an API that returns ONLY JSON data. No explanations or extra text.

Given these programming topics: {', '.join(keywords)}.

Generate 7 practice problems related to them. For each one, return:
- a short title (max 12 words)
- a direct link (LeetCode, GeeksforGeeks, HackerRank)

Return strictly this JSON structure:
[
  {{ "title": "Problem Title", "link": "https://..." }},
  ...
]
"""

    genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    try:
        # Get the response
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        print("Raw Gemini Output:\n", raw_text)  # Check the response structure
        
        # Clean any potential unwanted markdown (e.g., backticks, extra spaces, etc.)
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].strip("``` \n")

        print("Cleaned Response:\n", raw_text)

        # Try parsing the JSON from the cleaned response
        questions = json.loads(raw_text)

        if isinstance(questions, list) and all("title" in q and "link" in q for q in questions):
            return questions

    except json.JSONDecodeError as e:
        print("JSON Decoding Error:", e)
    except Exception as e:
        print("Error:", e)

    return []
