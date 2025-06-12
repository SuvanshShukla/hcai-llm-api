from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from llm_model import generate_response
from database import get_db, User, Conversation, Message
from auth import (
    verify_google_token, 
    create_access_token, 
    get_current_user
)

app = FastAPI(title="LLM Chat Bot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Add your React app URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class GoogleLoginRequest(BaseModel):
    token: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class MessageCreate(BaseModel):
    role: str
    content: str

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class GenerateRequest(BaseModel):
    conversation_id: int
    message: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

class GenerateResponse(BaseModel):
    message: MessageResponse
    response: MessageResponse

# Authentication endpoints
@app.post("/auth/google", response_model=LoginResponse)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Login with Google OAuth token"""
    try:
        # Verify Google token
        user_info = verify_google_token(request.token)
        
        # Check if user exists, create if not
        user = db.query(User).filter(User.google_id == user_info['google_id']).first()
        if not user:
            user = User(
                google_id=user_info['google_id'],
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info['picture']
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update user info if needed
            user.name = user_info['name']
            user.picture = user_info['picture']
            db.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture
            }
        )
    except Exception as e:
        logging.exception("Error during Google login")
        raise HTTPException(status_code=400, detail=str(e))

# Conversation endpoints
@app.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all conversations for the current user"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    
    return conversations

@app.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    conversation = Conversation(
        user_id=current_user.id,
        title=request.title
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with messages"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation

@app.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted successfully"}

# Message generation endpoint
@app.post("/generate", response_model=GenerateResponse)
def generate(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate response and save both user message and AI response"""
    try:
        # Verify conversation belongs to user
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Build conversation history for prompt
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at).all()
        
        prompt = ""
        for msg in messages:
            prefix = "User: " if msg.role == "user" else "Bot: "
            prompt += f"{prefix}{msg.content}\n"
        
        # Generate AI response
        ai_response_text = generate_response(prompt, max_tokens=100)
        
        # Save AI response
        ai_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response_text
        )
        db.add(ai_message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ai_message)
        
        return GenerateResponse(
            message=MessageResponse(
                id=user_message.id,
                role=user_message.role,
                content=user_message.content,
                created_at=user_message.created_at
            ),
            response=MessageResponse(
                id=ai_message.id,
                role=ai_message.role,
                content=ai_message.content,
                created_at=ai_message.created_at
            )
        )
        
    except Exception as e:
        logging.exception("Error generating response")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "LLM Chat Bot API - Go to /docs for the interactive Swagger UI."}

@app.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture
    }
