import streamlit as st
import google.generativeai as genai
from pydub import AudioSegment
import tempfile
import os

# Try from environment first
api_key = os.getenv("GEMINI_API_KEY")

# If not set in environment, allow manual input
if not api_key:
    api_key = st.text_input("Enter your Gemini API Key", type="password")


# --- Prompt Templates ---
PROMPTS = {
    "minimal": """Transcribe the meeting audio word-for-word.  
    Then summarize it into clear, well-structured meeting notes.  
    Include:
    - Key discussion points
    - Decisions made
    - Action items with assignee (if mentioned) and deadlines (if any).
    """,

    "business": """First, transcribe the audio accurately.  
    Then provide a structured summary in this format:

    📌 **Meeting Summary**
    - Purpose
    - Key Topics Discussed
    - Major Decisions

    ✅ **Action Items**
    - [Task] → [Person Responsible], [Deadline if mentioned]

    💡 **Follow-ups Needed**
    - List unclear points or open questions

    Keep the notes concise, professional, and easy to scan.
    """,

    "advanced": """You are an AI meeting assistant.

    1. Transcribe the entire meeting audio accurately.  
    2. Then summarize it into structured notes with these sections:
    - **Participants** (if mentioned)  
    - **Agenda / Purpose**  
    - **Key Discussion Points** (grouped by topic)  
    - **Decisions Made**  
    - **Action Items** (Task → Assignee → Deadline)  
    - **Risks / Concerns Raised**  
    - **Next Steps**

    Format in Markdown with bullet points and bold headings.
    """
}

# --- Transcribe & Summarize Function ---
def transcribe_and_summarize(audio_file, api_key, style="business"):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = PROMPTS[style]

    response = model.generate_content([
        {"mime_type": "audio/wav", "data": open(audio_file, "rb").read()},
        prompt
    ])
    return response.text


# --- Streamlit UI ---
st.title("🎙️ AI Meeting Transcriber & Summarizer")
style = st.selectbox("Choose summary style", ["minimal", "business", "advanced"])
uploaded_file = st.file_uploader("Upload an audio/video file", type=["wav", "mp3", "m4a", "mp4"])

if uploaded_file and api_key:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        if uploaded_file.name.endswith(".wav"):
            # Save as-is
            tmp_wav.write(uploaded_file.read())
            wav_path = tmp_wav.name
        else:
            # Convert to wav
            temp_input = tempfile.NamedTemporaryFile(delete=False)
            temp_input.write(uploaded_file.read())
            temp_input.close()

            # Convert using pydub (works for audio, also extracts audio from mp4)
            audio = AudioSegment.from_file(temp_input.name)
            audio.export(tmp_wav.name, format="wav")
            wav_path = tmp_wav.name

    st.info("⏳ Processing... this may take a while.")
    summary = transcribe_and_summarize(wav_path, api_key, style)
    st.success("✅ Done!")
    st.markdown(summary)

    # Cleanup
    os.remove(wav_path)
