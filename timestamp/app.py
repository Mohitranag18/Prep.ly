import streamlit as st
import re
from urllib.parse import urlparse, parse_qs

from transcript_handler import get_transcript, chunk_transcript, get_chunk_at_timestamp
from keyword_extractor import extract_keywords_gemini
from resource_finder import get_resources


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
        st.error(f"Error parsing URL: {e}")
        return None
    return None

# --- Streamlit App UI ---

st.set_page_config(layout="wide")
st.title("▶️ YouTube Timestamp Resource Finder") 
st.caption("Enter a YouTube URL, specify a timestamp, and get relevant resource links!")

# --- Inputs ---
col1, col2 = st.columns([3, 1])

with col1:
    youtube_url = st.text_input("YouTube Video URL:", placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ")

with col2:
    timestamp_input = st.number_input("Timestamp (s):", min_value=0, value=60, step=10, help="Enter the time in the video (in seconds) you want resources for.") 


# --- Processing Logic ---
video_id = None
if youtube_url:
    video_id = extract_video_id(youtube_url)
    if video_id:
        st.video(youtube_url, start_time=timestamp_input) # Display video
    else:
        st.warning("Invalid YouTube URL or could not extract Video ID.")

# Placeholder for results
resource_area = st.empty()

if video_id and timestamp_input is not None and num_resources_input > 0: 
    st.divider()
    st.subheader(f"Relevant Resources (Targeting {num_resources_input})") 

    # 1. Get Transcript
    with st.spinner("Fetching transcript..."):
        transcript_list = get_transcript(video_id)

    if transcript_list:
        # 2. Filter transcript up to the timestamp
        with st.spinner(f"Filtering transcript up to {timestamp_input}s..."):
            filtered_transcript = [entry for entry in transcript_list if entry.start <= timestamp_input]

        if filtered_transcript:
            with st.spinner("Chunking relevant transcript portion..."):
                # Chunk only the part of the transcript the user has 'watched'
                chunks = chunk_transcript(filtered_transcript)

            if chunks:
                # 4. Use the LAST chunk from the filtered transcript
                # This represents the most recent content the user encountered
                relevant_chunk = chunks[-1]

                # 5. Extract Keywords from this last chunk using Gemini
                with st.spinner("Extracting keywords via Gemini..."):
                    # Pass the text of the last chunk to the Gemini extractor
                    keywords = extract_keywords_gemini(relevant_chunk['text'], num_keywords=5) # Request 5 keywords

                if keywords:
                    # 6. Get Resources based on keywords from the last chunk (using Gemini keywords now)
                    with st.spinner(f"Searching for {num_resources_input} resource(s)..."): 
                        # Call the get_resources function
                        resource_links = get_resources(keywords, target_num_resources=num_resources_input)

                    resource_area.empty() 

                    if resource_links:
                        st.divider()
                        # Display each resource link
                        for idx, res in enumerate(resource_links):
                            # Display title and link from resource_finder output
                            st.markdown(f"**{idx+1}. {res['title']}** (Source: {res['source']})")
                            st.markdown(f"[{res['link']}]({res['link']})")
                            st.write("---")
                    else:
                        # Use info for no results
                        resource_area.info("Could not find relevant resources for the keywords extracted from this timestamp.")
                        pass

                else:
                     resource_area.info("Could not extract keywords from this part of the transcript.")
                     pass
            else:
                # This case means chunking the filtered transcript failed
                resource_area.warning("Could not process the transcript segment up to the specified timestamp.")
        else:
            # This case means no transcript entries were found before the timestamp
             resource_area.warning(f"No transcript content found before timestamp {timestamp_input}s.")
    else:
        resource_area.error("Failed to fetch transcript. Cannot proceed.")

else:
    if youtube_url and not video_id:
         resource_area.warning("Please enter a valid YouTube URL.") 
    else:
        resource_area.info("Enter a YouTube URL and timestamp to find relevant resources.")
