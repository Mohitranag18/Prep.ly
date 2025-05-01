import yt_dlp
import whisper
from keybert import KeyBERT
import google.generativeai as genai
import os

# Load models
model = whisper.load_model("base")
kw_model = KeyBERT()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloaded_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "downloaded_audio.mp3"

def transcribe_audio(audio_path, till_seconds):
    result = model.transcribe(audio_path)
    text = result["text"]
    return text[:int(till_seconds)]  # Approximate cut

def extract_keywords(text):
    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5)
    return [kw[0] for kw in keywords]

def get_practice_questions_from_gemini(keywords):
    prompt = f"""
    I have the following programming keywords: {", ".join(keywords)}.
    Suggest some specific problem-solving or coding practice questions (with platform links if possible) related to these topics.
    Prioritize DSA, LeetCode, GeeksforGeeks, and HackerRank links.
    """
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text
