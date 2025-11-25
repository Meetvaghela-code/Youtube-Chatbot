# RAG YouTube Assistant - Chrome Extension

Quick extension to interact with the local RAG backend for YouTube videos.

Install (development):

1. Start your backend (FastAPI). Default assumed URL: `http://localhost:8000`.
   - Example: `uvicorn backend.api_fast:app --reload --port 8000` from the repo root.

2. Load the extension in Chrome (or Edge):

   - Open `chrome://extensions`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `extension/` folder in the repo.

3. Open the extension popup, set Backend URL if different, paste a YouTube URL and click "Process".
   - Wait until status shows "Ready".
   - Ask questions using the popup's question box.

Notes:
- The backend must have CORS enabled (the provided backend allows all origins).
- If your backend uses a different port, set it in the popup `Backend URL` and click Save.
