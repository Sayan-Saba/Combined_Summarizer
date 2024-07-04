import streamlit as st
import os
import io
import moviepy.editor as mp
import assemblyai as aai
import google.generativeai as genai
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import time

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')

# Path to save temporary files
TEMP_DIR = "C:/Users/sayan/Desktop/Youtube_Transcriber/"

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
    temp_file_path = os.path.join(TEMP_DIR, "temp_video.mp4")
    audio_file_path = os.path.join(TEMP_DIR, "temp_audio.wav")

    # Save the uploaded file
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(uploaded_file.read())

    try:
        # Convert video to audio
        video = mp.VideoFileClip(temp_file_path)
        video.audio.write_audiofile(audio_file_path)
    finally:
        # Ensure the temporary video file is deleted
        attempt = 0
        while attempt < 5:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                break
            except PermissionError:
                attempt += 1
                time.sleep(1)  # Wait a bit before retrying
            except Exception as e:
                st.error(f"Error removing file: {e}")
                break
    
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
            audio_path = extract_audio_from_video(uploaded_file)
            if audio_path:
                transcript_text = transcribe_audio_assemblyai(audio_path)
                if transcript_text:
                    summary = generate_summary(transcript_text, prompt)
                    st.markdown("## Summary:")
                    st.write(summary)
                    
                    # Clean up temporary audio file
                    attempt = 0
                    while attempt < 5:
                        try:
                            if os.path.exists(audio_path):
                                os.remove(audio_path)
                            break
                        except PermissionError:
                            attempt += 1
                            time.sleep(1)  # Wait a bit before retrying
                        except Exception as e:
                            st.error(f"Error removing file: {e}")
                            break
