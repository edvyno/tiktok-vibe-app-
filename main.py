from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import hashlib
import secrets
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv
import uuid

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
VENICE_API_KEY = os.getenv("VENICE_API_KEY") 
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class GenerationHistory(Base):
    __tablename__ = "generations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    generation_type = Column(String, nullable=False)  # "image" or "tts"
    prompt = Column(Text, nullable=False)
    result_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Security
security = HTTPBearer()

# FastAPI app
app = FastAPI(title="Vibe App", description="FastAPI + React with Venice AI integration")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ImageGenerateRequest(BaseModel):
    prompt: str
    model: str = "qwen-image-2-pro"

class TTSRequest(BaseModel):
    text: str
    voice: str = "af_nicole"

# Helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Auth endpoints
@app.post("/api/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    # Authenticate user
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at
    }

# Venice AI endpoints
@app.post("/api/generate-image")
def generate_image(request: ImageGenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Call Venice AI
        url = "https://api.venice.ai/api/v1/image/generations"
        headers = {
            "Authorization": f"Bearer {VENICE_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "n": 1
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        image_url = result.get("data", [{}])[0].get("url", "")
        
        # Save to history
        generation = GenerationHistory(
            user_id=current_user.id,
            generation_type="image",
            prompt=request.prompt,
            result_url=image_url
        )
        db.add(generation)
        db.commit()
        
        return {"success": True, "image_url": image_url, "prompt": request.prompt}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/api/generate-tts")
def generate_tts(request: TTSRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Call Venice AI TTS
        url = "https://api.venice.ai/api/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {VENICE_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-kokoro",
            "input": request.text,
            "voice": request.voice
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        # Save audio file
        audio_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        audio_path = f"static/audio/{audio_filename}"
        os.makedirs("static/audio", exist_ok=True)
        
        with open(audio_path, "wb") as f:
            f.write(response.content)
        
        audio_url = f"/static/audio/{audio_filename}"
        
        # Save to history
        generation = GenerationHistory(
            user_id=current_user.id,
            generation_type="tts",
            prompt=request.text,
            result_url=audio_url
        )
        db.add(generation)
        db.commit()
        
        return {"success": True, "audio_url": audio_url, "text": request.text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.get("/api/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    generations = db.query(GenerationHistory).filter(
        GenerationHistory.user_id == current_user.id
    ).order_by(GenerationHistory.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": gen.id,
            "type": gen.generation_type,
            "prompt": gen.prompt,
            "result_url": gen.result_url,
            "created_at": gen.created_at
        }
        for gen in generations
    ]

# Serve static files and React app
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}")
def serve_react_app(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)