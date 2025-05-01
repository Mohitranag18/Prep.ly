# Handles fetching and processing of YouTube transcripts

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import math

def approximate_tokens(text):
    return len(text.split())

@st.cache_data(ttl=3600) # Cache transcripts for 1 hour
def get_transcript(video_id):
    """Fetches the transcript for a given YouTube video ID."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_manually_created_transcript(['en'])
    except TranscriptsDisabled:
        st.error(f"Transcripts are disabled for video: {video_id}")
        return None
    except NoTranscriptFound:
        st.error(f"No English transcript found for video: {video_id}. Trying generated...")
        try:
            transcript = transcript_list.find_generated_transcript(['en'])
        except NoTranscriptFound:
             st.error(f"No generated English transcript found either for video: {video_id}")
             return None
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching transcript: {e}")
        return None

    try:
        return transcript.fetch()
    except Exception as e:
        st.error(f"Failed to fetch transcript content: {e}")
        return None


def chunk_transcript(transcript_list, max_chunk_duration=120, max_tokens=500, pause_threshold=2.0):
    """Chunks the transcript based on duration, token count, or pauses."""
    if not transcript_list:
        return []

    chunks = []
    current_chunk_text = ""
    chunk_start_time = transcript_list[0].start
    last_entry_end_time = chunk_start_time

    for i, entry in enumerate(transcript_list):
        entry_start = entry.start
        entry_duration = entry.duration
        entry_end = entry_start + entry_duration
        entry_text = entry.text + " "

        # Calculate time gap from the end of the last entry
        time_gap = entry_start - last_entry_end_time if i > 0 else 0

        # Conditions to start a new chunk
        chunk_duration = entry_end - chunk_start_time
        current_tokens = approximate_tokens(current_chunk_text)
        start_new_chunk = False

        if i > 0: # Don't start a new chunk on the very first entry
            if time_gap > pause_threshold:
                start_new_chunk = True
            elif chunk_duration > max_chunk_duration:
                 start_new_chunk = True
            elif current_tokens + approximate_tokens(entry_text) > max_tokens:
                 start_new_chunk = True

        if start_new_chunk:
            # Finalize the previous chunk
            chunks.append({
                "text": current_chunk_text.strip(),
                "start": chunk_start_time,
                "end": last_entry_end_time # End time is the end of the last added entry
            })
            # Start a new chunk
            current_chunk_text = entry_text
            chunk_start_time = entry_start
        else:
            # Add to the current chunk
            current_chunk_text += entry_text

        last_entry_end_time = entry_end

    # Add the last chunk
    if current_chunk_text:
        chunks.append({
            "text": current_chunk_text.strip(),
            "start": chunk_start_time,
            "end": last_entry_end_time
        })

    return chunks

def get_chunk_at_timestamp(chunks, timestamp):
    """Finds the transcript chunk that contains the given timestamp."""
    for chunk in chunks:
        # Check if timestamp falls within the chunk's start and end times
        # Add a small buffer to the end time to catch timestamps exactly at the end
        if chunk['start'] <= timestamp < (chunk['end'] + 0.1):
            return chunk
    # If timestamp is beyond the last chunk's end time, return the last chunk
    if chunks and timestamp >= chunks[-1]['end']:
        return chunks[-1]
    return None

