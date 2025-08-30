import streamlit as st
import google.generativeai as genai
from pydub import AudioSegment
import tempfile
import os
import json

# Try from environment first
api_key = os.getenv("GEMINI_API_KEY")

# If not set in environment, allow manual input
if not api_key:
    api_key = st.text_input("Enter your Gemini API Key", type="password")


# --- Prompt Templates ---
PROMPTS = {
    "minimal": """Transcribe the meeting audio word-for-word.
    
    "Transcribe all spoken words in the audio using English letters (Roman script), 
    even if the word is Hindi. Preserve English words as they are. 
    Do NOT convert English words into Hindi script."
  
    Then summarize it into clear, well-structured meeting notes.  
    Include:
    - Key discussion points
    - Decisions made
    - Action items with assignee (if mentioned) and deadlines (if any).
    """,

    "business": """First, transcribe the audio accurately.
    
     "Transcribe all spoken words in the audio using English letters (Roman script), 
    even if the word is Hindi. Preserve English words as they are. 
    Do NOT convert English words into Hindi script."
    
    Return your response strictly in JSON with two fields.
    Respond ONLY in the following format, without any extra text:

    json
    {
      "transcription": "... full word-for-word transcription ...",
      "summary": "... structured summary notes ..."
    }
    
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
    
     "Transcribe all spoken words in the audio using English letters (Roman script), 
    even if the word is Hindi. Preserve English words as they are. 
    Do NOT convert English words into Hindi script."

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
    ], generation_config={"temperature": 1.0})

    # Get raw model text
    raw_text = getattr(response, "text", None) or str(response)
    # st.text(raw_text)
    

    # Clean ```json fences if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Take only the inside of the first fenced block
        parts = cleaned.split("```")
        if len(parts) >= 2:
            cleaned = parts[1]
        cleaned = cleaned.replace("json", "", 1).strip()

    # Try to parse JSON response
    transcription, summary = "", ""
    try:
        result = json.loads(cleaned)
        st.text(result)
        transcription = result.get("transcription", "")
        summary = result.get("summary", "")
    except Exception:
        # fallback if model outputs plain text
        transcription, summary = "", raw_text

    return transcription, summary


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

    
    # Run transcription + summarization
    # result = transcribe_and_summarize(wav_path, api_key, style)
    transcription, summary = transcribe_and_summarize(wav_path, api_key, style)
    st.success("✅ Done!")

    
    # --- Full Transcription (scrollable) ---
    st.subheader("📝 Full Transcription")
    if transcription.strip():
        st.markdown(
        f"""
        <div style="
            max-height: 400px;
            overflow-y: auto;
            padding: 1em;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #f9f9f9;
            white-space: pre-wrap;
            font-family: monospace;
        ">
        {transcription}
        </div>
        """,
        unsafe_allow_html=True
        )
    else:
         st.info("⚠️ No transcription available.")
    
    # --- Summary Notes (clean, scannable) ---
    st.subheader("📌 Meeting Summary Notes")
    st.markdown(summary)
    

    # Cleanup
    os.remove(wav_path)
