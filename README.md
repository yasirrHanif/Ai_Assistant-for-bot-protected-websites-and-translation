# ⚡ NeuralChat — Multimodal AI Assistant

> A production-grade, multi-tab AI chatbot featuring real-time web scraping, YouTube transcript Q&A, voice I/O, persistent memory, and dynamic user personalization — built with Groq LLaMA, OpenAI, and Gradio.

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-HuggingFace%20Space-blue?style=for-the-badge)](https://yasir-bhatti-msdsf25m017-version5.hf.space)
[![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python)](https://python.org)
[![Gradio](https://img.shields.io/badge/UI-Gradio-orange?style=for-the-badge)](https://gradio.app)
[![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA-purple?style=for-the-badge)](https://groq.com)
[![OpenAI](https://img.shields.io/badge/TTS-OpenAI-black?style=for-the-badge&logo=openai)](https://openai.com)

---

## 🌐 Try It Live

**[→ https://yasir-bhatti-msdsf25m017-version5.hf.space](https://yasir-bhatti-msdsf25m017-version5.hf.space)**

No setup required — open the link and start chatting instantly.

---

## 📌 Project Overview

**NeuralChat v5** is a fully-featured multimodal AI assistant developed as a progressive, version-by-version engineering exercise at the **Department of Data Science, University of Punjab**, under the supervision of **Dr. Muhammad Arif Butt**.

Each version layered a new capability on top of the last, demonstrating practical mastery of modern AI APIs, web automation, voice technologies, and stateful application design:

| Version | Capability Added |
|---------|-----------------|
| v1 | Goodreads web scraping with Bright Data + LLM-powered book Q&A |
| v2 | YouTube transcript ingestion and video Q&A |
| v3 | Persistent chat memory (JSON) + user preference personalization |
| v4 | Voice input (Whisper STT) + audio output (OpenAI TTS) |
| v5 | AI image generation integrated into all chat tabs |

---

## ✨ Feature Highlights

### 💬 Conversational AI with Cross-Session Memory
The main chat tab uses **Groq's LLaMA 3.1 8B** model with a JSON-backed persistent store. Every conversation turn is saved to disk and reloaded on startup, giving the assistant genuine memory across sessions — not just within a single browser tab.

### 📖 Goodreads Book Q&A
Scrapes the Goodreads "Best Books Ever" list in real time using **Bright Data Web Unlocker** (a residential proxy network that bypasses bot detection), parses the HTML with **BeautifulSoup**, and feeds the structured book data directly into the LLM context. Users can then ask natural-language questions about the scraped data.

### 🎬 YouTube Transcript Q&A
Accepts any YouTube URL or video ID, fetches the full transcript using the **youtube-transcript-api** (with fallback handling for both old and new API versions), and enables document-grounded Q&A — the model is constrained to answer only from the transcript, preventing hallucination.

### 🎤 Voice Input / 🔊 Voice Output
Every chat tab supports full voice interaction:
- **Speech-to-Text**: Microphone audio is transcribed via **Groq Whisper Large v3 Turbo** — one of the fastest and most accurate transcription APIs available.
- **Text-to-Speech**: Assistant replies are synthesized into audio using **OpenAI TTS-1** (alloy voice) and auto-played back to the user.

### ⚙️ Dynamic User Preferences
A dedicated Preferences tab lets users configure AI tone, response language (English, Urdu, Roman Urdu, Arabic, French, Spanish), output format (concise, detailed, bullet points, etc.), and custom behavioral rules. These preferences are persisted to disk and injected into every system prompt across all tabs — the AI adapts its entire communication style accordingly.

### 🖼️ AI Image Generation (v5)
Context-aware image generation is integrated into the main chat, books, and YouTube tabs. The assistant detects when a visual response would enhance understanding and generates an image alongside its text reply.

---

## 🏗️ Architecture & Tech Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     NeuralChat v5                           │
│                   Gradio Frontend (UI)                      │
├───────────┬──────────────┬──────────────┬───────────────────┤
│  Chat Tab │  Books Tab   │ YouTube Tab  │  Preferences Tab  │
├───────────┴──────────────┴──────────────┴───────────────────┤
│                     Core AI Layer                           │
│   Groq LLaMA 3.1 8B  /  LLaMA 3.3 70B (versatile)         │
├──────────────────────────────────────────────────────────────┤
│                   Multimodal Layer                          │
│  Groq Whisper v3-Turbo (STT) │ OpenAI TTS-1 (TTS)         │
│  OpenAI DALL·E / Image Gen   │                             │
├──────────────────────────────────────────────────────────────┤
│                   Data & Integration Layer                  │
│  Bright Data Web Unlocker    │ youtube-transcript-api      │
│  BeautifulSoup HTML Parser   │                             │
├──────────────────────────────────────────────────────────────┤
│                   Persistence Layer                         │
│    chat_history.json         │  user_preferences.json      │
└──────────────────────────────────────────────────────────────┘
```

| Layer | Technology |
|-------|-----------|
| **LLM** | Groq — `llama-3.1-8b-instant`, `llama-3.3-70b-versatile` |
| **STT** | Groq — `whisper-large-v3-turbo` |
| **TTS** | OpenAI — `tts-1` (alloy voice) |
| **Web Scraping** | Bright Data Web Unlocker API + BeautifulSoup4 |
| **YouTube** | `youtube-transcript-api` (dual API fallback) |
| **UI Framework** | Gradio (Blocks API, multi-tab) |
| **Persistence** | JSON flat-file storage (history + preferences) |
| **Deployment** | Hugging Face Spaces |
| **Styling** | Custom CSS with CSS variables, Google Fonts (Space Grotesk, JetBrains Mono) |

---

## 🗂️ Project Structure

```
neuralchat/
├── app.py                  # Main application — all logic and UI
├── chat_history.json       # Auto-generated: persistent chat log
├── user_preferences.json   # Auto-generated: user settings
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.10+
- API keys for: Groq, OpenAI, Bright Data

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/neuralchat.git
cd neuralchat

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
BRIGHTDATA_API_KEY=your_brightdata_api_key
BRIGHTDATA_USER=your_brightdata_username
BRIGHTDATA_PASS=your_brightdata_password
BRIGHTDATA_HOST=brd.superproxy.io
BRIGHTDATA_PORT=22225
```

> **Note:** On Hugging Face Spaces, set these as repository secrets rather than using a `.env` file.

### Run Locally

```bash
python app.py
```

The app will launch at `http://localhost:7860`.

---

## 🔑 Required API Keys

| Service | Purpose | Free Tier Available |
|---------|---------|-------------------|
| [Groq](https://console.groq.com) | LLM inference + Whisper STT | ✅ Yes |
| [OpenAI](https://platform.openai.com) | TTS audio output + Image generation | ⚠️ Credits required |
| [Bright Data](https://brightdata.com) | Residential proxy for web scraping | ⚠️ Trial available |

---

## 💡 Key Engineering Decisions

**Dual Whisper API fallback** — The YouTube transcript fetcher tries the newer object-oriented `YouTubeTranscriptApi()` instance first, then falls back to the legacy class method `get_transcript()`, ensuring compatibility across library versions without breaking the user experience.

**Preference injection via system prompt** — Rather than building a separate personalization model, user preferences (tone, language, format, custom rules) are dynamically prepended to every system prompt at call time. This is a lightweight, zero-latency approach that works across all three specialized AI personas (main assistant, BookBot, YouTube assistant).

**Persistent memory without a database** — Chat history and preferences are stored as JSON files. This keeps the deployment dependency-free (no Redis, no SQLite, no vector DB) while still providing genuine cross-session continuity — a deliberate architectural choice optimized for Hugging Face Spaces deployment.

**Modular voice pipeline** — Each tab has its own `process_voice_for_*` function that wraps the same core `transcribe_audio()` and `text_to_speech()` helpers. This avoids coupling between tabs while keeping the voice pipeline DRY.

---

## 🖼️ UI Design

The interface is built with a fully custom CSS theme — dark mode with a deep navy palette, cyan/emerald/amber accent colors, and glassmorphism-inspired card styling. Typography uses **Space Grotesk** for body text and **JetBrains Mono** for status/code elements, both loaded from Google Fonts. The design prioritizes readability in low-light environments and a professional aesthetic aligned with modern AI product UX.

---


## 👨‍💻 Author

**Muhammad Yasir**    
University of Punjab(FCIT), Lahore  

---

## 📄 License

This project is developed for academic purposes. All API usage is subject to the terms of service of the respective providers (Groq, OpenAI, Bright Data).

---

<div align="center">
  <strong>⚡ NeuralChat v5</strong> &nbsp;·&nbsp; Groq + OpenAI + Gradio &nbsp;·&nbsp; Built for DSAI @ UOP
</div>
