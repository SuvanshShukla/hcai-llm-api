from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from llm_model import generate_response
import logging

app = FastAPI()

# Request format from React frontend
class Message(BaseModel):
    role: str
    parts: List[str]

class HistoryRequest(BaseModel):
    contents: List[Message]

class PromptResponse(BaseModel):
    response: str

@app.post("/generate", response_model=PromptResponse)
def generate(history: HistoryRequest):
    try:
        # Build conversational prompt
        prompt = ""
        for message in history.contents:
            prefix = "User: " if message.role.lower() == "user" else "Bot: "
            prompt += prefix + " ".join(message.parts) + "\n"

        result = generate_response(prompt, max_tokens=100)
        return PromptResponse(response=result)

    except Exception as e:
        logging.exception("Error generating response")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Go to /docs for the interactive Swagger UI."}
