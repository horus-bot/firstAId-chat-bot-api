import os
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS setup (allow all origins for now, tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_MESSAGES = 10

# In-memory chat store
chat_memory = {}

# System prompt (updated for WHO-first-aid guidance)
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful, calm, first-aid assistant trained using WHO guidelines. "
        "Always respond with only first-aid advice that can be done immediately. "
        "Use bullet points with emojis. Highlight critical info in ALL CAPS. "
        "If the injury is serious, say clearly to SEE A DOCTOR. "
        "If the question is irrelevant, politely redirect the user. "
        "Al8192so return 3 short FAQs relevant to the user’s question in the same style."
    )
}


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message")
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not user_message:
        return {"error": "No message provided."}

    # Initialize session if not exists
    if session_id not in chat_memory:
        chat_memory[session_id] = [SYSTEM_PROMPT]

    # Append user message
    chat_memory[session_id].append({"role": "user", "content": user_message})

    # Limit chat history
    if len(chat_memory[session_id]) > MAX_MESSAGES:
        chat_memory[session_id] = [SYSTEM_PROMPT] + chat_memory[session_id][-MAX_MESSAGES + 1:]

    # Prepare API call to Groq
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": chat_memory[session_id],
        "temperature": 0.7
    }

    try:
        res = requests.post(GROQ_API_URL, headers=headers, json=payload)
        res.raise_for_status()
        reply_content = res.json()["choices"][0]["message"]["content"]

        # Append assistant reply
        chat_memory[session_id].append({"role": "assistant", "content": reply_content})

        return {
            "session_id": session_id,
            "reply": reply_content,
            "chat_history": chat_memory[session_id],
        }

    except Exception as e:
        return {"error": str(e), "session_id": session_id}


# Optional: health check
@app.get("/")
def root():
    return {"message": "First Aid Chatbot API is live!"}
