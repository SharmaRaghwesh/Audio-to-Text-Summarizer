# 🎙️ AI Meeting Transcriber & Summarizer

This Streamlit app uses **Google Gemini** to:
- Transcribe meeting audio/video files  
- Generate structured meeting notes with **decisions, action items, and follow-ups**  

It supports `.wav`, `.mp3`, `.m4a`, `.mp4` files. Non-`.wav` files are automatically converted before processing.

---

## 🚀 Features
- Upload audio or video files  
- Choose from **3 summary styles** (`minimal`, `business`, `advanced`)  
- Automatic audio conversion to `.wav` if needed  
- Output formatted in clean, scannable notes  

---

## 🛠️ Setup

### 1. Clone the repo
```
git clone https://github.com/your-username/meeting-transcriber.git
cd meeting-transcriber
```
### 2. Install dependencies
```
pip install -r requirements.txt
```
### 3. Configure API Key
```
The app needs a Gemini API Key.

Get it from Google AI Studio
.

You can either:

Local Dev: Paste it into the Streamlit text box when running the app.

Streamlit Cloud / Deployment: Set it as a secret.

For deployment on Streamlit Cloud:

1. Go to Settings → Secrets
2.Add:

GEMINI_API_KEY = "your_api_key_here"
```
### 4. Run locally
```
streamlit run app.py
```
📦 Deployment
Streamlit Cloud
```
Push the repo to GitHub

Connect repo to Streamlit Cloud

Add the secret GEMINI_API_KEY under Settings → Secrets

Add a packages.txt file with:
ffmpeg
```

