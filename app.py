import streamlit as st
import google.generativeai as genai
from pydub import AudioSegment
import tempfile
import os
import json
import re
import html

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
    
    Return your response strictly in **valid JSON** with two fields:
    {
      "transcription": "<full transcription, escape all quotes and newlines>",
      "summary": "<structured summary notes>"
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

def safe_extract_json(text: str):
    # Extract first {...} block using regex
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    
    json_str = match.group(0)

    # Remove control characters
    json_str = re.sub(r"[\x00-\x1f\x7f]", "", json_str)

    # Escape unescaped quotes inside transcription/summary
    # Replace " with ' inside the transcription content safely
    json_str = re.sub(r'(?<!\\)"', '\\"', json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("⚠️ Still invalid JSON:", e)
        return None
def separate_transcription_and_summary(data_string):
    """
    Separates transcription and summary from model output.
    Handles both JSON and Markdown outputs safely.
    """
    delimiter = "📌 **Meeting Summary**"

    if delimiter in data_string:
        parts = data_string.split(delimiter, 1)
        # Try to extract transcription from JSON block
        json_part = parts[0].strip()
        try:
            start_index = json_part.find('{')
            end_index = json_part.rfind('}') + 1
            json_content = json_part[start_index:end_index]
            # Clean control characters
            json_content = re.sub(r"[\x00-\x1f\x7f]", "", json_content)
            data = json.loads(json_content)
            transcription = data.get("transcription", "")
        except Exception:
            transcription = json_part  # fallback to raw text
        summary = delimiter + parts[1].strip()
        return transcription, summary
    else:
        # If delimiter not found, try extracting JSON transcription directly
        match = re.search(r'"transcription"\s*:\s*"([^"]+)"', data_string, re.DOTALL)
        transcription = match.group(1) if match else data_string
        summary = ""
        return transcription, summary



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
    st.code(raw_text, language="json")
    

    # Clean ```json fences if present
    # cleaned = raw_text.strip()
    # cleaned = safe_extract_json(raw_text)
    # if cleaned.startswith("```"):
    #     # Take only the inside of the first fenced block
    #     parts = cleaned.split("```")
    #     if len(parts) >= 2:
    #         cleaned = parts[1]
    #     cleaned = cleaned.replace("json", "", 1).strip()

    # Try to parse JSON response
    transcription, summary = "", ""
    transcription_text, summary_text = separate_transcription_and_summary(raw_text)
    if transcription_text and summary_text:
        st.write("the transcription is ",transcription_text)
        transcription = transcription_text
        summary = summary_text
    else:
        transcription,summary = "", raw_text
    # try:
    #     result = safe_extract_json(raw_text)
    #     st.text(result)
    #     transcription = result.get("transcription", "")
    #     summary = result.get("summary", "")
    # except Exception as e:
    #     st.write("⚠️ JSON parse failed:", e)
    #     # fallback if model outputs plain text
    #     transcription, summary = "", raw_text

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
        safe_text = html.escape(transcription).replace("\\n", "\n")
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
        {safe_text}
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
