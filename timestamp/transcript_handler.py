import os
import tempfile

import streamlit as st
import yt_dlp
import speech_recognition as sr
from pyannote.audio import Pipeline

# Download audio from YouTube
def download_audio_from_youtube(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Transcribe audio using SpeechRecognition
def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            transcription = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            transcription = "[Could not understand audio]"
        except sr.RequestError as e:
            transcription = f"[API Error: {e}]"
    return transcription

# Detect accent using pyannote-audio (speaker segmentation)
def detect_accent(audio_path):
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
    diarization = pipeline(audio_path)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "speaker": speaker,
            "start": turn.start,
            "end": turn.end
        })
    return segments
