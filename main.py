from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime

app = FastAPI()

# Enable CORS for all origins (adjust if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory message store
chat_memory = {}
MAX_MESSAGES = 10

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a helpful medical assistant who gives short, bullet-point first-aid advice with emojis and emphasis on important words."
}

# Static FAQs
FAQS = [
    {
        "question": "What should I do if I get a minor cut?",
        "answer": "Clean the wound, apply pressure, use a bandage."
    },
    {
        "question": "How do I treat a burn?",
        "answer": "Cool with water, don't apply ice, loosely cover it."
    },
    {
        "question": "When to call emergency services?",
        "answer": "Unconsciousness, heavy bleeding, or breathing issues."
    },
    {
        "question": "How to stop a nosebleed?",
        "answer": "Pinch nose, lean forward, avoid tilting head back."
    }
]

@app.get("/")
async def root():
    return {"message": "First Aid Chatbot API is running."}


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message")
    session_id = data.get("session_id") or str(uuid.uuid4())

    # Initialize session
    if session_id not in chat_memory:
        chat_memory[session_id] = [SYSTEM_PROMPT]

    # Add user's message to history
    chat_memory[session_id].append({"role": "user", "content": message})

    # Trim history to max messages
    if len(chat_memory[session_id]) > MAX_MESSAGES:
        chat_memory[session_id] = [SYSTEM_PROMPT] + chat_memory[session_id][-MAX_MESSAGES + 1:]

    # --- Replace this with real Groq call later ---
    reply = (
        "🚨 **FIRST AID STEPS**:\n"
        "• 🩸 **STOP THE BLEEDING** with pressure\n"
        "• 🧼 **CLEAN** the wound gently\n"
        "• 🩹 **COVER** with a sterile bandage\n"
        "• 🏥 **SEE A DOCTOR** if it’s deep or keeps bleeding"
    )

    # Add reply to chat history
    chat_memory[session_id].append({"role": "assistant", "content": reply})

    return {
        "session_id": session_id,
        "reply": reply,
        "chat_history": chat_memory[session_id],
        "faqs": FAQS
    }
