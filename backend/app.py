import os
from dotenv import load_dotenv

# Load .env from current working directory first (where uvicorn was started)
load_dotenv()

# If the key isn't in the process environment, try loading the backend/.env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    backend_env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY missing in .env or environment variables")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_community.document_loaders import YoutubeLoader

# Text Splitting & Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# LLM
from langchain_google_genai import ChatGoogleGenerativeAI

# LangChain Core
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableParallel,
    RunnablePassthrough,
    RunnableLambda
)
from langchain_core.output_parsers import StrOutputParser
from langchain_community.retrievers import BM25Retriever


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be" in url:
        return url.split("/")[-1]
    return None

def translate_to_english_if_needed(text: str) -> str:
    """
    Detect language and translate Hindi -> English using Gemini.
    English text is returned unchanged.
    """
    if not text or len(text.strip()) == 0:
        return text

    # Lightweight detection: Hindi usually contains characters in \u0900-\u097F
    if any('\u0900' <= ch <= '\u097F' for ch in text):
        print("🌐 Hindi transcript detected → Translating to English...")

        translator = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            api_key=GOOGLE_API_KEY
        )

        prompt = f"""
        Translate the following Hindi transcript into clear English.
        Do NOT summarize. Translate word-by-word while keeping meaning EXACT.

        Hindi text:
        {text}
        """

        try:
            english = translator.invoke(prompt)
            if hasattr(english, "content"):
                english = english.content
            return english.strip()

        except Exception as e:
            print("❌ Translation failed:", e)
            return text  # fallback to original

    # English → no translation required
    return text

def fetch_transcript(video_url):
    video_id = get_video_id(video_url)

    # 1 try direct api
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "hi"])
        text = " ".join([x["text"] for x in transcript])
        return translate_to_english_if_needed(text)
    except:
        pass

    # 2 try list transcripts
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        t = transcripts.find_transcript(["en", "hi"])
        data = t.fetch()
        text = " ".join([x["text"] for x in data])
        return translate_to_english_if_needed(text)
    except:
        pass

    # 3 fallback youtube loader
    try:
        loader = YoutubeLoader.from_youtube_url(
            video_url,
            add_video_info=False,
            language=["en", "hi"]
        )
        docs = loader.load()
        if docs:
            return translate_to_english_if_needed(docs[0].page_content)
    except:
        pass

    return None



def create_retriever(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    docs = splitter.create_documents([text])

    embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectordb = FAISS.from_documents(docs, embedding)

    return vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 12, "lambda_mult": 0.5},
    )


def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


def build_rag_chain(retriever):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
        api_key=GOOGLE_API_KEY
    )

    prompt = ChatPromptTemplate.from_template("""
    You are a YouTube RAG assistant.
    Use ONLY the context below. If answer not found,
    reply: "The transcript does not contain this information."

    Context:
    {context}

    Question:
    {question}
    """)

    chain_inputs = RunnableParallel({
        "context": RunnablePassthrough() | retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough()
    })

    chain = chain_inputs | prompt | llm | StrOutputParser()
    return chain
