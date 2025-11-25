from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app import (
    get_video_id,
    fetch_transcript,
    create_retriever,
    build_rag_chain
)

app = FastAPI(title="YouTube RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessRequest(BaseModel):
    video_url: str

class AskRequest(BaseModel):
    video_id: str
    question: str


# Global store
STORE = {}
# STORE[video_id] = {
#   "transcript": str,
#   "retriever": retriever,
#   "chain": chain,
#   "ready": bool,
#   "error": str|None
# }


# ------------------- BACKGROUND RAG PIPELINE --------------------

def _build_pipeline(video_id: str, video_url: str):
    print(f"🔄 Processing {video_id} ...")

    transcript = fetch_transcript(video_url)
    if not transcript:
        print("❌ Transcript fetch failed")
        STORE[video_id] = {"ready": False, "error": "Transcript not available"}
        return

    print("✓ Transcript fetched")

    try:
        retriever = create_retriever(transcript)
        chain = build_rag_chain(retriever)

        STORE[video_id] = {
            "transcript": transcript,
            "retriever": retriever,
            "chain": chain,
            "ready": True,
            "error": None
        }

        print("✓ Pipeline built successfully")

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        STORE[video_id] = {"ready": False, "error": str(e)}


# ------------------- ROUTES --------------------

@app.post("/process")
def process(req: ProcessRequest, background_tasks: BackgroundTasks):
    url = req.video_url
    video_id = get_video_id(url)

    if not video_id:
        raise HTTPException(400, "Invalid YouTube URL")

    # mark as processing
    STORE[video_id] = {"ready": False}

    # run pipeline async
    background_tasks.add_task(_build_pipeline, video_id, url)

    return {"ok": True, "video_id": video_id, "status": "processing"}



@app.post("/ask")
def ask(req: AskRequest):
    vid = req.video_id

    if vid not in STORE:
        raise HTTPException(404, "Video not processed")

    record = STORE[vid]

    if not record.get("ready"):
        raise HTTPException(409, "Still processing")

    chain = record.get("chain")
    
    if not chain:
        raise HTTPException(500, "RAG chain unavailable")

    try:
        # CORRECTION HERE: 
        # Pass the plain string 'req.question', NOT a dictionary.
        # The chain in app.py is built to handle the string input directly.
        answer = chain.invoke(req.question)

        # Because your chain ends with StrOutputParser, 
        # 'answer' is already a string. No need for .content checks.
        return {"ok": True, "answer": answer}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"RAG error: {e}")


@app.get("/status/{video_id}")
def status(video_id: str):
    item = STORE.get(video_id)
    if not item:
        return {"ok": False, "status": "not_found"}

    return {
        "ok": True,
        "status": "ready" if item.get("ready") else "processing",
        "error": item.get("error")
    }


@app.get("/debug/{video_id}")
def debug(video_id: str):
    if video_id not in STORE:
        raise HTTPException(404, "video not found")
    return STORE[video_id]
