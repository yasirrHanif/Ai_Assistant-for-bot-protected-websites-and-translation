import requests
from bs4 import BeautifulSoup
import os
import re
import json
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
import gradio as gr

# -----------------------------------------------
# LOAD API KEYS
# -----------------------------------------------
# load_dotenv()  # Remove on Hugging Face
BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")
BRIGHTDATA_USER    = os.getenv("BRIGHTDATA_USER", "")
BRIGHTDATA_PASS    = os.getenv("BRIGHTDATA_PASS", "")
BRIGHTDATA_HOST    = os.getenv("BRIGHTDATA_HOST", "brd.superproxy.io")
BRIGHTDATA_PORT    = os.getenv("BRIGHTDATA_PORT", "22225")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
print("OPENAI key exists:", bool(OPENAI_API_KEY))
print("OpenAI client exists:", openai_client is not None)

client = Groq(api_key=GROQ_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# -----------------------------------------------
# PERSISTENT STORAGE — JSON Files
# -----------------------------------------------
HISTORY_FILE     = "chat_history.json"
PREFERENCES_FILE = "user_preferences.json"


def load_chat_history():
    """Load chat history from JSON file."""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Storage] Could not load history: {e}")
    return []



def save_chat_history(history):
    """Save chat history to JSON file after every turn."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Storage] Could not save history: {e}")



def load_preferences():
    """Load user preferences from JSON file."""
    try:
        if os.path.exists(PREFERENCES_FILE):
            with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[Storage] Could not load preferences: {e}")
    return {
        "tone": "friendly",
        "language": "English",
        "format": "concise",
        "custom_rules": ""
    }



def save_preferences(prefs):
    """Save user preferences to JSON file."""
    try:
        with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
        return "✅ Preferences saved!"
    except Exception as e:
        return f"❌ Could not save: {str(e)}"


# Load at startup
chat_history_store = load_chat_history()
user_preferences   = load_preferences()
print(f"[Storage] Loaded {len(chat_history_store)} messages from history")
print(f"[Storage] Preferences: {user_preferences}")


# ================================================================
# VERSION 1: GOODREADS SCRAPER
# ================================================================
def get_books():
    if not BRIGHTDATA_API_KEY:
        return [], "❌ BRIGHTDATA_API_KEY not found!"

    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "zone": "web_unlocker1",
        "url": "https://www.goodreads.com/list/show/1.Best_Books_Ever",
        "format": "raw"
    }

    try:
        response = requests.post(
            "https://api.brightdata.com/request",
            json=data,
            headers=headers,
            timeout=30
        )
        if response.status_code != 200:
            return [], f"❌ Scraping failed! Status: {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")
        books = soup.select("tr[itemtype='http://schema.org/Book']")
        if not books:
            return [], "⚠️ No books found."

        results = []
        for i, book in enumerate(books[:20], start=1):
            try:
                title  = book.select_one("a.bookTitle span").text.strip()
                author = book.select_one("a.authorName span").text.strip()
                rating = book.select_one("span.minirating").text.strip()
                results.append({
                    "rank": i,
                    "title": title,
                    "author": author,
                    "rating": rating
                })
            except Exception:
                pass
        return results, f"✅ Scraped {len(results)} books!"
    except Exception as e:
        return [], f"❌ Error: {str(e)}"



def format_books_as_text(books):
    if not books:
        return "No book data available."
    return "\n".join([
        f"Rank #{b['rank']}: \"{b['title']}\" by {b['author']} — Rating: {b['rating']}"
        for b in books
    ])



def show_books_table(books_data, scrape_status):
    if not books_data:
        return f"**Status:** {scrape_status}"
    md = f"**{scrape_status}**\n\n| Rank | Title | Author | Rating |\n|------|-------|--------|--------|\n"
    for b in books_data:
        md += f"| #{b['rank']} | {b['title']} | {b['author']} | {b['rating']} |\n"
    return md


print("🔄 Scraping Goodreads...")
books_data, scrape_status = get_books()
print(scrape_status)


# ================================================================
# VERSION 2: YOUTUBE TRANSCRIPT
# ================================================================
def get_youtube_transcript(video_id: str):
    """Fetch YouTube transcript — old aur new API dono handle karta hai."""
    video_id = video_id.strip()

    if "youtube.com/watch" in video_id:
        video_id = video_id.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in video_id:
        video_id = video_id.split("youtu.be/")[-1].split("?")[0]

    if not video_id:
        return None, "❌ Please enter a valid YouTube Video ID or URL."

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        try:
            ytt = YouTubeTranscriptApi()
            fetched = ytt.fetch(video_id)
            full_text = " ".join([s.text for s in fetched])
            if full_text.strip():
                return full_text, f"✅ Transcript fetched! ({len(full_text)} chars, ID: {video_id})"
        except Exception:
            pass

        try:
            fetched = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([s["text"] for s in fetched])
            if full_text.strip():
                return full_text, f"✅ Transcript fetched! ({len(full_text)} chars, ID: {video_id})"
        except Exception:
            pass

        return None, "⚠️ Transcript empty or not available. Try another video."

    except Exception as e:
        return None, f"❌ Error: {str(e)}"


current_transcript = {"text": None, "status": "No transcript loaded."}


def load_transcript(video_id):
    global current_transcript
    text, status = get_youtube_transcript(video_id)
    current_transcript["text"] = text
    current_transcript["status"] = status
    if text:
        preview = text[:600] + "..." if len(text) > 600 else text
        return status, f"**📄 Preview:**\n\n_{preview}_"
    return status, "No preview available."


# ================================================================
# VERSION 4: VOICE HELPERS
# ================================================================
def transcribe_audio(audio_path):
    """Convert microphone audio to text using Groq Whisper."""
    if not audio_path:
        return "", "⚠️ No audio recorded."

    if not GROQ_API_KEY:
        return "", "❌ GROQ_API_KEY not set for transcription."

    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                response_format="verbose_json"
            )

        text = getattr(transcript, "text", "") or ""
        if not text.strip():
            return "", "⚠️ Speech detected but transcript is empty."

        return text.strip(), "✅ Voice transcribed successfully!"
    except Exception as e:
        return "", f"❌ Transcription error: {str(e)}"



def text_to_speech(text):
    """Convert assistant reply to speech using OpenAI TTS."""
    if not text or not text.strip():
        return None, "⚠️ Empty text for audio output."

    if not OPENAI_API_KEY:
        return None, "⚠️ OPENAI_API_KEY missing."

    try:
        tts_client = OpenAI(api_key=OPENAI_API_KEY)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_path = tmp_file.name
        tmp_file.close()

        response = tts_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text[:1000],
        )

        with open(tmp_path, "wb") as f:
            f.write(response.content)

        return tmp_path, "✅ Audio reply generated!"
    except Exception as e:
        print("TTS full error:", repr(e))
        return None, f"❌ TTS error: {str(e)}"



def process_voice_for_main_chat(audio_path, history):
    """Voice input for main chatbot."""
    transcript_text, voice_status = transcribe_audio(audio_path)
    if not transcript_text:
        return history, voice_status, None, ""

    reply = ask_main_ai(transcript_text, history)
    audio_reply, tts_status = text_to_speech(reply)

    updated_history = list(history) if history else []
    updated_history.append({"role": "user", "content": transcript_text})
    updated_history.append({"role": "assistant", "content": reply})

    combined_status = f"{voice_status}\n{tts_status}"
    return updated_history, combined_status, audio_reply, transcript_text



def process_voice_for_books(audio_path, history):
    """Voice input for books chatbot."""
    transcript_text, voice_status = transcribe_audio(audio_path)
    if not transcript_text:
        return history, voice_status, None, ""

    reply = ask_books_ai(transcript_text, history)
    audio_reply, tts_status = text_to_speech(reply)

    updated_history = list(history) if history else []
    updated_history.append({"role": "user", "content": transcript_text})
    updated_history.append({"role": "assistant", "content": reply})

    combined_status = f"{voice_status}\n{tts_status}"
    return updated_history, combined_status, audio_reply, transcript_text



def process_voice_for_youtube(audio_path, history):
    """Voice input for YouTube chatbot."""
    transcript_text, voice_status = transcribe_audio(audio_path)
    if not transcript_text:
        return history, voice_status, None, ""

    reply = ask_youtube_ai(transcript_text, history)
    audio_reply, tts_status = text_to_speech(reply)

    updated_history = list(history) if history else []
    updated_history.append({"role": "user", "content": transcript_text})
    updated_history.append({"role": "assistant", "content": reply})

    combined_status = f"{voice_status}\n{tts_status}"
    return updated_history, combined_status, audio_reply, transcript_text


# ================================================================
# VERSION 3: PREFERENCES + PERSISTENT CHAT
# ================================================================
def build_system_prompt(base_prompt, prefs):
    """Inject user preferences into system prompt dynamically."""
    pref_text = f"""
USER PREFERENCES (follow these always):
- Tone: {prefs.get('tone', 'friendly')}
- Language: {prefs.get('language', 'English')}
- Response Format: {prefs.get('format', 'concise')}
"""
    custom = prefs.get("custom_rules", "").strip()
    if custom:
        pref_text += f"- Custom Rules: {custom}\n"
    return base_prompt + pref_text



def convert_history_for_display(history_store):
    """Convert stored history to Gradio chatbot format (list of dicts)."""
    return [{"role": item["role"], "content": item["content"]} for item in history_store]



def ask_main_ai(message, history):
    """
    VERSION 3 Main Chatbot:
    - Multi-turn (session memory via history)
    - Persistent (saves to JSON after every turn)
    - Preferences injected into system prompt
    """
    global chat_history_store, user_preferences

    if not GROQ_API_KEY:
        return "❌ GROQ_API_KEY not set."

    base_prompt = """You are a smart, helpful AI assistant with memory of past conversations.
You help users with general questions, book recommendations, research, and more.
Always maintain context from previous messages in the conversation."""

    system = build_system_prompt(base_prompt, user_preferences)
    messages = [{"role": "system", "content": system}]

    for item in chat_history_store:
        messages.append({"role": item["role"], "content": item["content"]})

    for item in history:
        if isinstance(item, dict):
            if item not in chat_history_store:
                messages.append({"role": item["role"], "content": item["content"]})
        else:
            messages.append({"role": "user", "content": item[0]})
            messages.append({"role": "assistant", "content": item[1]})

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.6,
            max_tokens=1024
        )
        reply = response.choices[0].message.content

        chat_history_store.append({"role": "user", "content": message})
        chat_history_store.append({"role": "assistant", "content": reply})
        save_chat_history(chat_history_store)

        return reply

    except Exception as e:
        return f"❌ AI Error: {str(e)}"



def ask_books_ai(message, history):
    """Goodreads Q&A — Version 1 (carried forward)."""
    if not GROQ_API_KEY:
        return "❌ GROQ_API_KEY not set."
    if not books_data:
        return f"⚠️ No book data. Status: {scrape_status}"

    base = """You are a smart and friendly book assistant named BookBot 📚.
Books data from Goodreads:
{context}
RULES: Only answer from this data. Be friendly and concise."""

    system   = build_system_prompt(base.format(context=format_books_as_text(books_data)), user_preferences)
    messages = [{"role": "system", "content": system}]
    for item in history:
        if isinstance(item, dict):
            messages.append({"role": item["role"], "content": item["content"]})
        else:
            messages.append({"role": "user", "content": item[0]})
            messages.append({"role": "assistant", "content": item[1]})
    messages.append({"role": "user", "content": message})

    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.5,
            max_tokens=1024
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"❌ AI Error: {str(e)}"



def ask_youtube_ai(message, history):
    """YouTube Q&A — Version 2 (carried forward)."""
    if not GROQ_API_KEY:
        return "❌ GROQ_API_KEY not set."
    transcript = current_transcript.get("text")
    if not transcript:
        return "⚠️ No transcript loaded. Enter a YouTube Video ID and click 'Load Transcript' first."

    base     = "You are a helpful assistant answering ONLY from this transcript:\n{transcript}\nRULES: Only use transcript info. Be concise."
    system   = build_system_prompt(base.format(transcript=transcript[:6000]), user_preferences)
    messages = [{"role": "system", "content": system}]
    for item in history:
        if isinstance(item, dict):
            messages.append({"role": item["role"], "content": item["content"]})
        else:
            messages.append({"role": "user", "content": item[0]})
            messages.append({"role": "assistant", "content": item[1]})
    messages.append({"role": "user", "content": message})

    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4,
            max_tokens=1024
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"❌ AI Error: {str(e)}"



def update_preferences(tone, language, fmt, custom_rules):
    """Save updated preferences and return status."""
    global user_preferences
    user_preferences = {
        "tone": tone,
        "language": language,
        "format": fmt,
        "custom_rules": custom_rules
    }
    status = save_preferences(user_preferences)
    return status



def clear_history():
    """Clear all persistent chat history."""
    global chat_history_store
    chat_history_store = []
    save_chat_history([])
    return "🗑️ Chat history cleared!"


# ================================================================
# CUSTOM CSS — SAME UI + SMALL AUDIO SECTION SUPPORT
# ================================================================
CUSTOM_CSS = """
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root {
    --bg-primary:     #0a0e1a;
    --bg-secondary:   #0f1629;
    --bg-card:        #141d35;
    --bg-card-hover:  #1a2540;
    --accent-cyan:    #00d4ff;
    --accent-emerald: #00ff9d;
    --accent-amber:   #ffb800;
    --accent-rose:    #ff4f7b;
    --text-primary:   #e8edf8;
    --text-secondary: #8899bb;
    --text-muted:     #4a5a7a;
    --border:         #1e2d50;
    --border-bright:  #2a3f70;
    --glow-cyan:      0 0 20px rgba(0,212,255,0.15);
    --glow-emerald:   0 0 20px rgba(0,255,157,0.12);
    --radius-sm:      8px;
    --radius-md:      14px;
    --radius-lg:      20px;
    --font-main:      'Space Grotesk', sans-serif;
    --font-mono:      'JetBrains Mono', monospace;
}
*, *::before, *::after { box-sizing: border-box; }
body, .gradio-container {
    background: var(--bg-primary) !important;
    font-family: var(--font-main) !important;
    color: var(--text-primary) !important;
    min-height: 100vh;
}
.gradio-container {
    background:
        radial-gradient(ellipse 80% 50% at 20% 10%, rgba(0,212,255,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 90%, rgba(0,255,157,0.03) 0%, transparent 60%),
        var(--bg-primary) !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 0 16px !important;
}
.hero-header {
    text-align: center;
    padding: 40px 20px 28px;
    position: relative;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: 0; left: 50%; transform: translateX(-50%);
    width: 300px; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-emerald) 60%, var(--accent-amber) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 10px;
    line-height: 1.1;
}
.hero-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    font-weight: 400;
    letter-spacing: 0.3px;
    margin: 0;
}
.hero-subtitle span {
    color: var(--accent-cyan);
    font-weight: 500;
}
.hero-badges {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-top: 16px;
    flex-wrap: wrap;
}
.badge {
    background: var(--bg-card);
    border: 1px solid var(--border-bright);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    font-family: var(--font-mono);
    color: var(--text-secondary);
    letter-spacing: 0.5px;
}
.tab-nav {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 6px !important;
    margin-bottom: 20px !important;
    display: flex;
    gap: 4px;
}
.tab-nav button {
    background: transparent !important;
    border: none !important;
    color: var(--text-muted) !important;
    font-family: var(--font-main) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    border-radius: var(--radius-md) !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    letter-spacing: 0.2px !important;
    white-space: nowrap !important;
}
.tab-nav button:hover {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
}
.tab-nav button.selected {
    background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(0,255,157,0.08)) !important;
    color: var(--accent-cyan) !important;
    border: 1px solid rgba(0,212,255,0.25) !important;
    box-shadow: var(--glow-cyan) !important;
}
.chatbot-wrap .chatbot,
.chatbot-wrap > div {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
}
.message.user {
    background: linear-gradient(135deg, rgba(0,212,255,0.12), rgba(0,212,255,0.06)) !important;
    border: 1px solid rgba(0,212,255,0.2) !important;
    border-radius: var(--radius-md) var(--radius-sm) var(--radius-md) var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
}
.message.bot {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: var(--radius-sm) var(--radius-md) var(--radius-md) var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
}
input[type="text"],
textarea,
.gr-textbox,
.gr-textbox textarea,
.gr-textbox input {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
    font-size: 0.9rem !important;
    padding: 12px 16px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    outline: none !important;
}
input[type="text"]:focus,
textarea:focus,
.gr-textbox textarea:focus,
.gr-textbox input:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.08) !important;
}
button.lg.primary, button[variant="primary"] {
    background: linear-gradient(135deg, var(--accent-cyan), #0099cc) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    color: #000 !important;
    font-family: var(--font-main) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.3px !important;
    padding: 11px 22px !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}
button.lg.secondary, button[variant="secondary"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 11px 22px !important;
}
button.lg.stop, button[variant="stop"] {
    background: rgba(255,79,123,0.1) !important;
    border: 1px solid rgba(255,79,123,0.3) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--accent-rose) !important;
    font-family: var(--font-main) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 11px 22px !important;
}
.gr-markdown, .prose {
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
}
.status-box textarea {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
}
.transcript-preview {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent-amber);
    border-radius: var(--radius-sm);
    padding: 14px 18px;
    font-size: 0.875rem;
    line-height: 1.6;
    color: var(--text-secondary);
    max-height: 180px;
    overflow-y: auto;
}
.voice-box {
    background: rgba(0, 212, 255, 0.04);
    border: 1px solid rgba(0, 212, 255, 0.18);
    border-radius: 14px;
    padding: 14px;
    margin-top: 14px;
}
.footer-strip {
    text-align: center;
    padding: 18px 0 28px;
    color: var(--text-muted);
    font-size: 0.75rem;
    font-family: var(--font-mono);
    letter-spacing: 0.5px;
    border-top: 1px solid var(--border);
    margin-top: 24px;
}
"""


# ================================================================
# GRADIO UI — SAME LAYOUT + VOICE BLOCKS ADDED
# ================================================================
initial_display = convert_history_for_display(chat_history_store)
prefs = load_preferences()

with gr.Blocks(title="⚡ NeuralChat — AI Assistant") as demo:

    gr.HTML("""
    <div class="hero-header">
        <p class="hero-title">⚡ NeuralChat</p>
        <p class="hero-subtitle">
            Powered by <span>Groq LLaMA</span> &nbsp;·&nbsp;
            <span>Persistent Memory</span> &nbsp;·&nbsp;
            <span>Goodreads + YouTube + Voice</span>
        </p>
        <div class="hero-badges">
            <span class="badge">llama-3.3-70b</span>
            <span class="badge">llama-3.1-8b</span>
            <span class="badge">whisper-large-v3-turbo</span>
            <span class="badge">tts-1</span>
            <span class="badge">ver 4.0</span>
        </div>
    </div>
    """)

    with gr.Tabs(elem_classes=["tab-nav"]):

        # ============================================================
        # TAB 1: MAIN CHATBOT
        # ============================================================
        with gr.Tab("💬  Chat"):
            gr.HTML("""
            <div style="margin-bottom:18px;">
                <div class="section-label">Main Assistant</div>
                <div class="section-title">Conversational AI with Memory</div>
                <div class="section-desc">
                    Your assistant remembers past sessions and adapts to your preferences automatically.
                </div>
            </div>
            """)

            main_chatbot = gr.Chatbot(
                value=initial_display,
                height=460,
                placeholder="<div style='text-align:center;color:#4a5a7a;padding:40px;font-family:Space Grotesk,sans-serif;'>💬 Start a conversation — I remember everything.</div>",
                elem_classes=["chatbot-wrap"],
                show_label=False
                
            )

            with gr.Row():
                main_msg = gr.Textbox(
                    placeholder="Type a message…",
                    scale=7,
                    show_label=False,
                    container=False,
                )
                main_send = gr.Button("Send ↑", variant="primary", scale=1)

            def submit_main_text(message, history):
                history = list(history) if history else []
                if not message.strip():
                    return history, "", None, ""
                reply = ask_main_ai(message, history)
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": reply})
                image_path, image_status = maybe_generate_image(message, reply)
                return history, "", image_path, image_status

            main_send.click(
                fn=submit_main_text,
                inputs=[main_msg, main_chatbot],
                outputs=[main_chatbot, main_msg, main_image_output, main_image_status]
            )
            main_msg.submit(
                fn=submit_main_text,
                inputs=[main_msg, main_chatbot],
                outputs=[main_chatbot, main_msg, main_image_output, main_image_status]
            )

            with gr.Column(elem_classes=["voice-box"]):
                gr.Markdown("**🎤 Voice Input / 🔊 Audio Reply**")
                with gr.Row():
                    main_audio_in = gr.Audio(sources=["microphone"], type="filepath", label="Record Voice")
                    main_audio_out = gr.Audio(label="Assistant Voice Reply", autoplay=True)
                with gr.Row():
                    main_voice_btn = gr.Button("🎙️ Ask by Voice", variant="secondary")
                    main_voice_status = gr.Textbox(label="Voice Status", interactive=False, elem_classes=["status-box"])
                main_voice_text = gr.Textbox(label="Transcribed Text", interactive=False)

            with gr.Column(elem_classes=["image-box"]):
                gr.Markdown("**🖼️ Version 5 — Generated Image**")
                main_image_output = gr.Image(label="AI Generated Image", type="filepath")
                main_image_status = gr.Textbox(label="Image Status", interactive=False, elem_classes=["status-box"])

            main_voice_btn.click(
                fn=process_voice_for_main_chat,
                inputs=[main_audio_in, main_chatbot],
                outputs=[main_chatbot, main_voice_status, main_audio_out, main_voice_text, main_image_output, main_image_status]
            )

            gr.HTML("<div style='height:12px'></div>")

            with gr.Row():
                clear_btn = gr.Button("🗑️  Clear History", variant="stop", scale=1)
                clear_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    scale=3,
                    elem_classes=["status-box"],
                )

            clear_btn.click(fn=clear_history, outputs=clear_status)

        # ============================================================
        # TAB 2: GOODREADS
        # ============================================================
        with gr.Tab("📖  Books"):
            gr.HTML("""
            <div style="margin-bottom:18px;">
                <div class="section-label">Goodreads Scraper</div>
                <div class="section-title">BookBot — Best Books Q&A</div>
                <div class="section-desc">
                    Ask BookBot anything about the scraped Goodreads \"Best Books Ever\" list.
                </div>
            </div>
            """)

            books_chatbot = gr.Chatbot(
                height=380,
                placeholder="<div style='text-align:center;color:#4a5a7a;padding:40px;font-family:Space Grotesk,sans-serif;'>📚 Ask me about the Goodreads Best Books list!</div>",
                show_label=False
                
            )

            with gr.Row():
                books_msg = gr.Textbox(
                    placeholder="e.g. Who wrote the top book?",
                    scale=7,
                    show_label=False,
                    container=False,
                )
                books_send = gr.Button("Ask ↑", variant="primary", scale=1)

            def submit_books_text(message, history):
                history = list(history) if history else []
                if not message.strip():
                    return history, "", None, ""
                reply = ask_books_ai(message, history)
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": reply})
                image_path, image_status = maybe_generate_image(message, reply)
                return history, "", image_path, image_status

            books_send.click(
                fn=submit_books_text,
                inputs=[books_msg, books_chatbot],
                outputs=[books_chatbot, books_msg, books_image_output, books_image_status]
            )
            books_msg.submit(
                fn=submit_books_text,
                inputs=[books_msg, books_chatbot],
                outputs=[books_chatbot, books_msg, books_image_output, books_image_status]
            )

            with gr.Column(elem_classes=["voice-box"]):
                gr.Markdown("**🎤 Voice Input / 🔊 Audio Reply**")
                with gr.Row():
                    books_audio_in = gr.Audio(sources=["microphone"], type="filepath", label="Record Voice")
                    books_audio_out = gr.Audio(label="Assistant Voice Reply", autoplay=True)
                with gr.Row():
                    books_voice_btn = gr.Button("🎙️ Ask by Voice", variant="secondary")
                    books_voice_status = gr.Textbox(label="Voice Status", interactive=False, elem_classes=["status-box"])
                books_voice_text = gr.Textbox(label="Transcribed Text", interactive=False)

            with gr.Column(elem_classes=["image-box"]):
                gr.Markdown("**🖼️ Version 5 — Generated Image**")
                books_image_output = gr.Image(label="AI Generated Image", type="filepath")
                books_image_status = gr.Textbox(label="Image Status", interactive=False, elem_classes=["status-box"])

            books_voice_btn.click(
                fn=process_voice_for_books,
                inputs=[books_audio_in, books_chatbot],
                outputs=[books_chatbot, books_voice_status, books_audio_out, books_voice_text, books_image_output, books_image_status]
            )

            gr.HTML("<hr>")
            gr.HTML("""
            <div style="margin-bottom:14px;">
                <div class="section-label">Scraped Data</div>
                <div class="section-title">Goodreads Top 20</div>
            </div>
            """)

            books_display = gr.Markdown(value=show_books_table(books_data, scrape_status))
            refresh_btn = gr.Button("🔄  Re-Scrape Goodreads", variant="secondary")

            def refresh_data():
                global books_data, scrape_status
                books_data, scrape_status = get_books()
                return show_books_table(books_data, scrape_status)

            refresh_btn.click(fn=refresh_data, outputs=books_display)

        # ============================================================
        # TAB 3: YOUTUBE
        # ============================================================
        with gr.Tab("🎬  YouTube"):
            gr.HTML("""
            <div style="margin-bottom:18px;">
                <div class="section-label">YouTube Transcript</div>
                <div class="section-title">Video Q&A Assistant</div>
                <div class="section-desc">
                    Load any YouTube video's transcript, then ask questions about it.
                </div>
            </div>
            """)

            gr.HTML("""
            <div style="background:rgba(255,184,0,0.06);border:1px solid rgba(255,184,0,0.2);
                        border-left:3px solid #ffb800;border-radius:10px;
                        padding:12px 18px;margin-bottom:16px;
                        font-size:0.85rem;color:#c89a00;font-family:Space Grotesk,sans-serif;">
                <strong>Step 1</strong> — Paste a YouTube Video ID or full URL and click <em>Load Transcript</em>
            </div>
            """)

            with gr.Row():
                video_id_input = gr.Textbox(
                    placeholder="e.g.  dQw4w9WgXcQ  or  https://youtu.be/…",
                    label="YouTube Video ID or URL",
                    scale=4,
                )
                load_btn = gr.Button("📥  Load Transcript", variant="primary", scale=1)

            with gr.Row():
                transcript_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    elem_classes=["status-box"],
                )

            transcript_preview = gr.Markdown(
                value="*Transcript preview will appear here…*",
                elem_classes=["transcript-preview"],
            )
            load_btn.click(
                fn=load_transcript,
                inputs=[video_id_input],
                outputs=[transcript_status, transcript_preview],
            )

            gr.HTML("""
            <div style="background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.15);
                        border-left:3px solid #00d4ff;border-radius:10px;
                        padding:12px 18px;margin:16px 0;
                        font-size:0.85rem;color:#0099bb;font-family:Space Grotesk,sans-serif;">
                <strong>Step 2</strong> — Ask anything about the loaded video below
            </div>
            """)

            youtube_chatbot = gr.Chatbot(
                height=360,
                placeholder="<div style='text-align:center;color:#4a5a7a;padding:40px;font-family:Space Grotesk,sans-serif;'>📥 Load a transcript above, then ask anything!</div>",
                show_label=False
        
            )

            with gr.Row():
                youtube_msg = gr.Textbox(
                    placeholder="e.g. What is the main topic?",
                    scale=7,
                    show_label=False,
                    container=False,
                )
                youtube_send = gr.Button("Ask ↑", variant="primary", scale=1)

            def submit_youtube_text(message, history):
                history = list(history) if history else []
                if not message.strip():
                    return history, "", None, ""
                reply = ask_youtube_ai(message, history)
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": reply})
                image_path, image_status = maybe_generate_image(message, reply)
                return history, "", image_path, image_status

            youtube_send.click(
                fn=submit_youtube_text,
                inputs=[youtube_msg, youtube_chatbot],
                outputs=[youtube_chatbot, youtube_msg, youtube_image_output, youtube_image_status]
            )
            youtube_msg.submit(
                fn=submit_youtube_text,
                inputs=[youtube_msg, youtube_chatbot],
                outputs=[youtube_chatbot, youtube_msg, youtube_image_output, youtube_image_status]
            )

            with gr.Column(elem_classes=["voice-box"]):
                gr.Markdown("**🎤 Voice Input / 🔊 Audio Reply**")
                with gr.Row():
                    youtube_audio_in = gr.Audio(sources=["microphone"], type="filepath", label="Record Voice")
                    youtube_audio_out = gr.Audio(label="Assistant Voice Reply", autoplay=True)
                with gr.Row():
                    youtube_voice_btn = gr.Button("🎙️ Ask by Voice", variant="secondary")
                    youtube_voice_status = gr.Textbox(label="Voice Status", interactive=False, elem_classes=["status-box"])
                youtube_voice_text = gr.Textbox(label="Transcribed Text", interactive=False)

            with gr.Column(elem_classes=["image-box"]):
                gr.Markdown("**🖼️ Version 5 — Generated Image**")
                youtube_image_output = gr.Image(label="AI Generated Image", type="filepath")
                youtube_image_status = gr.Textbox(label="Image Status", interactive=False, elem_classes=["status-box"])

            youtube_voice_btn.click(
                fn=process_voice_for_youtube,
                inputs=[youtube_audio_in, youtube_chatbot],
                outputs=[youtube_chatbot, youtube_voice_status, youtube_audio_out, youtube_voice_text, youtube_image_output, youtube_image_status]
            )

        # ============================================================
        # TAB 4: PREFERENCES
        # ============================================================
        with gr.Tab("⚙️  Preferences"):
            gr.HTML("""
            <div style="margin-bottom:20px;">
                <div class="section-label">Personalization</div>
                <div class="section-title">AI Behavior Settings</div>
                <div class="section-desc">
                    These preferences are saved permanently and injected into every AI response across all tabs.
                </div>
            </div>
            """)

            with gr.Row():
                with gr.Column():
                    tone_input = gr.Dropdown(
                        choices=["friendly", "formal", "casual", "professional", "humorous"],
                        value=prefs.get("tone", "friendly"),
                        label="🎭  Tone",
                        info="How the AI speaks to you",
                    )
                    lang_input = gr.Dropdown(
                        choices=["English", "Urdu", "Roman Urdu", "Arabic", "French", "Spanish"],
                        value=prefs.get("language", "English"),
                        label="🌐  Response Language",
                        info="Language for all AI responses",
                    )

                with gr.Column():
                    fmt_input = gr.Dropdown(
                        choices=["concise", "detailed", "bullet points", "numbered list", "paragraph"],
                        value=prefs.get("format", "concise"),
                        label="📝  Response Format",
                        info="How responses should be structured",
                    )
                    custom_input = gr.Textbox(
                        value=prefs.get("custom_rules", ""),
                        label="✏️  Custom Rules",
                        placeholder='e.g. "Always cite sources" or "Use emojis sparingly"',
                        lines=3,
                        info="Extra instructions for the AI to always follow",
                    )

            with gr.Row():
                save_btn = gr.Button("💾  Save Preferences", variant="primary", scale=1)
                pref_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    scale=2,
                    elem_classes=["status-box"],
                )

            save_btn.click(
                fn=update_preferences,
                inputs=[tone_input, lang_input, fmt_input, custom_input],
                outputs=pref_status,
            )

            def show_current_prefs():
                p = load_preferences()
                return f"""```
Tone         →  {p.get('tone')}
Language     →  {p.get('language')}
Format       →  {p.get('format')}
Custom Rules →  {p.get('custom_rules') or 'None'}
```"""

            pref_preview = gr.Markdown(value=show_current_prefs())
            save_btn.click(
                fn=lambda t, l, f, c: show_current_prefs(),
                inputs=[tone_input, lang_input, fmt_input, custom_input],
                outputs=pref_preview,
            )

        # ============================================================
        # TAB 5: ABOUT
        # ============================================================
        with gr.Tab("ℹ️  About"):
            gr.HTML(f"""
            <div style="max-width:680px;margin:0 auto;padding:10px 0 24px;">
                <div style="margin-bottom:24px;">
                    <div class="section-label">Project Info</div>
                    <div class="section-title">NeuralChat — Version 4</div>
                    <div class="section-desc">
                        A multi-tab AI assistant with web scraping, YouTube transcript Q&A,
                        persistent memory, user preference personalization, voice input, and audio output.
                    </div>
                </div>
                <div style="background:var(--bg-card,#141d35);border:1px solid #1e2d50;
                            border-radius:14px;overflow:hidden;margin-bottom:20px;">
                    <table style="width:100%;border-collapse:collapse;">
                        <thead>
                            <tr style="background:rgba(0,212,255,0.07);">
                                <th style="padding:11px 16px;text-align:left;font-size:0.72rem;letter-spacing:1px;text-transform:uppercase;color:#00d4ff;border-bottom:1px solid #1e2d50;">Layer</th>
                                <th style="padding:11px 16px;text-align:left;font-size:0.72rem;letter-spacing:1px;text-transform:uppercase;color:#00d4ff;border-bottom:1px solid #1e2d50;">Detail</th>
                            </tr>
                        </thead>
                        <tbody style="color:#e8edf8;font-size:0.875rem;">
                            <tr style="border-bottom:1px solid #1e2d50;"><td style="padding:10px 16px;color:#8899bb;">🌐 Scraping</td><td style="padding:10px 16px;">Bright Data Web Unlocker + BeautifulSoup</td></tr>
                            <tr style="border-bottom:1px solid #1e2d50;"><td style="padding:10px 16px;color:#8899bb;">🎬 YouTube</td><td style="padding:10px 16px;">youtube-transcript-api</td></tr>
                            <tr style="border-bottom:1px solid #1e2d50;"><td style="padding:10px 16px;color:#8899bb;">🎤 STT</td><td style="padding:10px 16px;">Groq Whisper Large v3 Turbo</td></tr>
                            <tr style="border-bottom:1px solid #1e2d50;"><td style="padding:10px 16px;color:#8899bb;">🔊 TTS</td><td style="padding:10px 16px;">OpenAI tts-1 (alloy)</td></tr>
                            <tr style="border-bottom:1px solid #1e2d50;"><td style="padding:10px 16px;color:#8899bb;">🤖 AI (Main)</td><td style="padding:10px 16px;">Groq — llama-3.3-70b-versatile</td></tr>
                            <tr style="border-bottom:1px solid #1e2d50;"><td style="padding:10px 16px;color:#8899bb;">💾 Memory</td><td style="padding:10px 16px;">JSON persistent storage</td></tr>
                            <tr><td style="padding:10px 16px;color:#8899bb;">⚙️ Prefs</td><td style="padding:10px 16px;">JSON persistent storage</td></tr>
                        </tbody>
                    </table>
                </div>
                <div style="text-align:center;padding-top:10px;font-size:0.78rem;color:#4a5a7a;font-family:JetBrains Mono,monospace;letter-spacing:0.5px;border-top:1px solid #1e2d50;">
                    Assignment 01 — Ver 4 &nbsp;|&nbsp; Dept. of Data Science, University of Punjab<br>
                    Instructor: Dr. Muhammad Arif Butt
                </div>
            </div>
            """)

    gr.HTML("""
    <div class="footer-strip">
        NeuralChat v4 &nbsp;·&nbsp; Groq + OpenAI + Gradio &nbsp;·&nbsp; Built for DSAI @ UOP
    </div>
    """)

demo.launch(
    share=False,
    inbrowser=True,
    css=CUSTOM_CSS,
)