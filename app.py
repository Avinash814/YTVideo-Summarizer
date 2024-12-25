import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from googletrans import Translator

# Load environment variables
load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("AIzaSyDvN0vnSjaBgb4WHOe1AsVTYuoiTif5-40"))

# Prompt for the summarization task in English
english_prompt = """You are a YouTube video summarizer. Your task is to summarize the provided transcript text, 
highlighting the key points in bullet format within 500 words. Please provide the summary of the text: 
- Introduction: The video introduces the main topic, explaining its relevance and setting the stage for the discussion.
- Key Point 1: The first major point, detailing important aspects and their implications.
- Key Point 2: The second key topic, providing relevant findings, examples, and insights.
- Key Point 3: Another critical topic discussed, highlighting key examples and their broader impact.
- Supporting Points: Additional topics that reinforce the main discussion and provide supporting evidence.
- Expert Opinion: Insights or recommendations from the speaker, adding depth and perspective.
- Conclusion: A wrap-up of the main takeaways, with a final call to action or thought for the viewer."""

# Prompt for the summarization task in Hindi
hindi_prompt = """Aap ek YouTube video summary creator hain. Transcript text ka summary 
tayar karein aur 250 shabdon ke andar Hindi mein sabse important points provide karein."""

# Function to extract transcript details
def extract_transcript_details(youtube_video_url, language="en"):
    try:
        video_id = youtube_video_url.split("v=")[1].split("&")[0]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        transcript = " ".join([entry["text"] for entry in transcript_text])
        return transcript
    except NoTranscriptFound:
        st.error("No transcript was found for this video. Ensure the video has captions enabled.")
    except TranscriptsDisabled:
        st.error("Transcripts are disabled for this video. Try a different video.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
    return None

# Function to generate a summary using Google Gemini
def generate_gemini_content(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"Failed to generate a summary using Gemini: {e}")
        return None

# Function to translate the summary from English to Hindi
def translate_to_hindi(text):
    try:
        translator = Translator()
        translated_text = translator.translate(text, src='en', dest='hi').text
        return translated_text
    except Exception as e:
        st.error(f"Failed to translate to Hindi: {e}")
        return None

# Function to create a downloadable file (returns binary data)
def create_downloadable_file(content):
    # Convert the content to bytes and return it
    return content.encode('utf-8')

# Streamlit App
st.set_page_config(page_title="YouTube Summarizer", layout="wide")

# Custom CSS for styling
st.markdown(
    """
    <style>
    body {
        background-color: #f7f7f7;
        font-family: 'Arial', sans-serif;
    }
    .stHeader {
        background-color: #4a90e2;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .sidebar .sidebar-content {
        background-color: #f5f5f5;
        padding: 10px;
    }
    
    .stButton>button {
        background-color:rgb(0, 0, 0);  /* Box color */
        color: white;               /* Font color */
        font-size: 16px;
        border-radius: 5px;
        padding: 10px 20px;
        margin: 5px;
        width: 100%;
        font-weight: bold;   
        
    }
    
    .stButton>button:hover {
        background-color:#4a90e2;
        color: rgb(255, 255, 255);
    }
    .video-container iframe {
        border-radius: 10px;
    }
    .summary-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Add attractive header to the page
st.markdown('<div class="stHeader">YouTube Video Summarizer</div>', unsafe_allow_html=True)
st.sidebar.title("Transcript to Notes")

# Sidebar Inputs
youtube_link = st.sidebar.text_input("Enter YouTube Video Link:")
language = st.sidebar.selectbox("Select Video Language", ["English", "Hindi"])

# Initialize session state variables if not present
if "generated_summary" not in st.session_state:
    st.session_state.generated_summary = None
if "generated_language" not in st.session_state:
    st.session_state.generated_language = "English"  # Default to English
if "note_language" not in st.session_state:
    st.session_state.note_language = "English"  # Default to English for note language
if "has_downloaded" not in st.session_state:
    st.session_state.has_downloaded = False  # Track whether the file has been downloaded

# Handle YouTube video iframe embedding
if youtube_link:
    try:
        video_id = youtube_link.split("v=")[1].split("&")[0]
        iframe_html = f"""
        <div class="video-container">
            <iframe 
                width="520" 
                height="380" 
                src="https://www.youtube.com/embed/{video_id}" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        </div>
        """
        st.markdown(iframe_html, unsafe_allow_html=True)
    except IndexError:
        st.error("Invalid YouTube link. Please ensure it contains a valid video ID.")

# Check if the YouTube link has changed and reset summary if it has
if "last_youtube_link" not in st.session_state:
    st.session_state.last_youtube_link = ""

if youtube_link != st.session_state.last_youtube_link:
    st.session_state.generated_summary = None  # Reset summary when a new link is entered
    st.session_state.has_downloaded = False  # Reset download status

# Store the current YouTube link in session state to detect future changes
st.session_state.last_youtube_link = youtube_link

# Generate Notes Button
generate_button = st.sidebar.button("Generate Notes")

if generate_button and youtube_link and language:
    if st.session_state.generated_summary is None:
        # Generate the summary based on the selected language for the video
        selected_language = "hi" if language == "Hindi" else "en"
        transcript_text = extract_transcript_details(youtube_link, selected_language)

        if transcript_text:
            prompt = hindi_prompt if language == "Hindi" else english_prompt
            summary = generate_gemini_content(transcript_text, prompt)

            if summary:
                # Store the generated summary in session state
                st.session_state.generated_summary = summary
                # Also store the language of the generated summary
                st.session_state.generated_language = language

                # Reset the downloaded status after generating the summary
                st.session_state.has_downloaded = False

# Language Switcher for Detailed Notes
col1, col2 = st.columns([3, 1])  # First column takes more space

with col1:
    # Show the generated summary based on the language selected
    if st.session_state.generated_summary:
        if st.session_state.note_language == "English":
            st.subheader("Detailed Notes (English):")
            st.write(st.session_state.generated_summary)

        elif st.session_state.note_language == "Hindi":
            st.subheader("Detailed Notes (Hindi):")
            hindi_summary = translate_to_hindi(st.session_state.generated_summary)
            if hindi_summary:
                st.write(hindi_summary)

with col2:
    # Dropdown for selecting detailed notes language (with auto-reload)
    note_language = st.selectbox("Select Detailed Notes Language", ["English", "Hindi"], key="note_language")

    # If the language is switched, update the displayed notes
    if note_language != st.session_state.note_language:
        # Update the note language and reload the summary
        st.session_state.note_language = note_language
        st.session_state.generated_summary = None  # Reset summary when a new language is selected
        st.experimental_rerun()  # Trigger the rerun to update notes language to default (English)

# Show Download Buttons only if the summary is available and not yet downloaded
if st.session_state.generated_summary and not st.session_state.has_downloaded:
    # English Download Button
    if st.session_state.note_language == "English":
        content = st.session_state.generated_summary
    # Hindi Download Button
    elif st.session_state.note_language == "Hindi":
        content = translate_to_hindi(st.session_state.generated_summary)

    if content:
        file_data = create_downloadable_file(content)
        if st.session_state.note_language == "English":
            if st.download_button(
                label="Download Notes as English Text File",
                data=file_data,
                file_name="summarized_notes_english.txt",
                mime="text/plain"
            ):
                st.session_state.has_downloaded = True  # Mark as downloaded after the first download
        elif st.session_state.note_language == "Hindi":
            if st.download_button(
                label="Download Notes as Hindi Text File",
                data=file_data,
                file_name="summarized_notes_hindi.txt",
                mime="text/plain"
            ):  
                st.session_state.has_downloaded = True  # Mark as downloaded after the first download
