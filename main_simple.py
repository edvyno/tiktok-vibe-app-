from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
VENICE_API_KEY = os.getenv("VENICE_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-for-testing")

app = FastAPI(title="TikTok Vibe App", description="AI-powered social media content generator")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "TikTok Vibe App", "version": "1.0", "status": "running"}

@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "venice_api": "configured" if VENICE_API_KEY else "missing"
    }

@app.get("/api/test")
def test_api():
    """Test API endpoint"""
    return {
        "message": "API working",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production" if os.getenv("PORT") else "development"
    }

# Serve static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    @app.get("/{full_path:path}")
    def serve_react_app(full_path: str):
        """Serve React app for SPA routing"""
        return FileResponse("static/index.html")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting TikTok Vibe App...")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))