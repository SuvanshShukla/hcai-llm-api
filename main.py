from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_model import generate_response

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 100

class PromptResponse(BaseModel):
    response: str

@app.post("/generate", response_model=PromptResponse)
def generate(prompt_request: PromptRequest):
    try:
        result = generate_response(prompt_request.prompt, prompt_request.max_tokens)
        return PromptResponse(response=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
