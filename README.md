# 📺 YouTube RAG Chatbot

A powerful **Retrieval Augmented Generation (RAG)** application that
allows users to chat with any YouTube video.\
By analyzing video transcripts using advanced vector search and **Google
Gemini 2.0 Flash**, this tool provides instant, context-aware answers.

It features a **premium Apple-style UI** built with React, a robust
FastAPI backend, and a Chrome Extension for browsing-time assistance.

## ✨ Features

-   🎥 **Video Analysis** --- Fetches and processes YouTube transcripts
    via API or fallback loaders.\
-   🌐 **Multi-Language Support** --- Works with both English and Hindi
    (with automatic translation).\
-   🧠 **Smart RAG Pipeline** --- Uses LangChain + FAISS for embedding &
    retrieval.\
-   ⚡ **Instant Answers** --- Powered by Gemini 2.0 Flash for fast,
    accurate responses.\
-   🔍 **Vector Search** --- Uses `all-MiniLM-L6-v2` with MMR for
    diverse result retrieval.\
-   🧩 **Chrome Extension** --- Chat with YouTube videos directly on
    YouTube.\
-   🎨 **Premium UI** --- Glassmorphism, animations, dark theme, fully
    responsive.

    <img width="400" height="500" alt="image" src="https://github.com/user-attachments/assets/bb8688d8-5876-480d-90c1-4c8fcd2ba26d" />

## 🛠️ Tech Stack

### Frontend

-   React (Vite)
-   Bootstrap 5 + Custom CSS
-   Lucide React + FontAwesome

### Backend

-   FastAPI
-   LangChain
-   FAISS Vectorstore
-   HuggingFace Embeddings
-   Gemini 2.0 Flash
-   youtube-transcript-api

### Chrome Extension

-   Manifest V3
-   Popup UI
-   DOM extraction for video metadata

## 🚀 Getting Started

### Backend Setup

``` bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

``` bash
cd frontend
npm install
npm run dev
```

### Chrome Extension Setup

1.  Open chrome://extensions/
2.  Enable Developer Mode
3.  Load unpacked → select extension folder

## 📂 Project Structure

    backend/
    frontend/
    extension/

## 🤝 Contributing

Fork → Modify → PR

## 📄 License

MIT
