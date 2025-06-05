from fastapi import FastAPI
from pydantic import BaseModel
import os
import uuid
import requests
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()

# cors enabling for cross origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat memory and sytem prompt given to the model
chat_memory = {}
MAX_MESSAGES = 10
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful first-aid assistant. "
        "When answering, ALWAYS use short BULLET POINTS. "
        "Use EMOJIS relevant to the context. "
        "CAPITALIZE IMPORTANT WORDS or PHRASES to emphasize them. "
        "Keep the answer CONCISE and EASY TO UNDERSTAND."
    )
}



class ChatRequest(BaseModel): #input of the model 
    message: str
    session_id: str | None = None

# API endpoint (/chat) with post request 
@app.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4()) # creating a new session ID if not provided

    # Initialize memory if new session
    if session_id not in chat_memory:
        chat_memory[session_id] = [SYSTEM_PROMPT]

    # adding memory to the chat history
    chat_memory[session_id].append({"role": "user", "content": req.message})

    # deleting extra messages if the memory exceeds the limit
    if len(chat_memory[session_id]) > MAX_MESSAGES:
        chat_memory[session_id] = [SYSTEM_PROMPT] + chat_memory[session_id][-MAX_MESSAGES + 1:]

    # Call Groq API
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-8b-8192",
            "messages": chat_memory[session_id]
        }
    )

    res_data = response.json()
    bot_reply = res_data["choices"][0]["message"]["content"]
    chat_memory[session_id].append({"role": "assistant", "content": bot_reply})

    return {
        "session_id": session_id,
        "reply": bot_reply,
        "history": chat_memory[session_id]
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# this is for telling render where to port it