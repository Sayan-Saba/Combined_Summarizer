import streamlit as st
import tempfile
import moviepy.editor as mp
import assemblyai as aai
import google.generativeai as genai
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import os

load_dotenv()

# Define prompts for summarization
prompt = """You are a video summarizer. 
The summary should be in a detailed manner but shouldn't be too long or too short, covering all necessary content and important points.
The transcript text will be appended here: """

# Extract transcript from YouTube video
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("v=")[1].split("&")[0]  # Extract video ID
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([item["text"] for item in transcript_text])
        return transcript
    except Exception as e:
        st.error(f"Error fetching YouTube transcript: {e}")
        return None

# Extract audio from video file
def extract_audio_from_video(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
        temp_video_file.write(uploaded_file.read())
        temp_video_file_path = temp_video_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        audio_file_path = temp_audio_file.name

    try:
        # Convert video to audio
        video = mp.VideoFileClip(temp_video_file_path)
        video.audio.write_audiofile(audio_file_path)
    except Exception as e:
        st.error(f"Error processing video: {e}")
    finally:
        # Ensure the temporary video file is deleted
        try:
            os.remove(temp_video_file_path)
        except Exception as e:
            st.error(f"Error removing temporary video file: {e}")

    return audio_file_path

# Transcribe audio using AssemblyAI
def transcribe_audio_assemblyai(audio_path):
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_path)
        return transcript.text
    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return None

# Generate summary using Google Gemini Pro
def generate_summary(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None

# Streamlit UI
st.title("Video Summarizer")

# Sidebar for API key inputs
st.sidebar.title("API Key Configuration")
google_api_key = st.sidebar.text_input("Google API Key", type="password")
assemblyai_api_key = st.sidebar.text_input("AssemblyAI API Key", type="password")

# Configure API keys
if google_api_key and assemblyai_api_key:
    genai.configure(api_key=google_api_key)
    aai.settings.api_key = assemblyai_api_key
else:
    st.sidebar.error("Please enter both API keys")

option = st.radio("Choose the source of the video:", ("YouTube URL", "Upload a Video"))

if option == "YouTube URL":
    youtube_link = st.text_input("Enter the YouTube video link:")
    if youtube_link:
        if st.button("Get Summary"):
            st.write("Fetching transcript and generating summary, please wait...")
            transcript_text = extract_transcript_details(youtube_link)
            if transcript_text:
                summary = generate_summary(transcript_text, prompt)
                st.markdown("## Summary:")
                st.write(summary)

elif option == "Upload a Video":
    uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mpeg4"])
    if uploaded_file:
        st.video(uploaded_file)

        if st.button("Get Summary"):
            st.write("Processing video and generating summary, please wait...")
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_path = extract_audio_from_video(uploaded_file)
                if audio_path:
                    transcript_text = transcribe_audio_assemblyai(audio_path)
                    if transcript_text:
                        summary = generate_summary(transcript_text, prompt)
                        st.markdown("## Summary:")
                        st.write(summary)

                    # Clean up temporary audio file
                    try:
                        os.remove(audio_path)
                    except Exception as e:
                        st.error(f"Error removing temporary audio file: {e}")
