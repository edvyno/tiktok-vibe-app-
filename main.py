from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
import os
import requests
import base64
import json
from dotenv import load_dotenv
from pydantic import BaseModel

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

# Request models
class ImageGenerateRequest(BaseModel):
    prompt: str
    style: str = "glamorous"

class TikTokContentRequest(BaseModel):
    theme: str = "lifestyle"
    style: str = "glamorous"

@app.get("/api/test")
def test_api():
    """Test API endpoint"""
    return {
        "message": "API working",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production" if os.getenv("PORT") else "development"
    }

@app.post("/api/generate-image")
def generate_image(request: ImageGenerateRequest):
    """Generate Akari image using Venice AI"""
    if not VENICE_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "Venice API key not configured"}
        )
    
    # Build the prompt for Akari
    akari_prompt = f"""Akari, a stunning 25-year-old Japanese-Korean woman with voluminous golden blonde curls, 
{request.prompt}. {request.style} style, professional photography, 9:16 aspect ratio, high quality."""
    
    try:
        response = requests.post(
            "https://api.venice.ai/api/v1/image/generate",
            headers={
                "Authorization": f"Bearer {VENICE_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen-image-2-pro",
                "prompt": akari_prompt
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            # Handle new Venice API format - images array contains base64 strings directly
            if result.get("images") and len(result["images"]) > 0:
                return {
                    "success": True,
                    "image_b64": result["images"][0],
                    "prompt_used": akari_prompt,
                    "timestamp": datetime.utcnow().isoformat()
                }
            # Fallback to old format for backwards compatibility
            elif result.get("data") and len(result["data"]) > 0:
                return {
                    "success": True,
                    "image_b64": result["data"][0]["b64_json"],
                    "prompt_used": akari_prompt,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return JSONResponse(
            status_code=500,
            content={"error": f"Venice AI error: {response.status_code}"}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Generation failed: {str(e)}"}
        )

@app.post("/api/tiktok-content")
def create_tiktok_content(request: TikTokContentRequest):
    """Create complete TikTok content for Akari"""
    
    # Theme-based prompts
    themes = {
        "lifestyle": "enjoying a luxurious lifestyle, elegant evening wear, confident pose",
        "fashion": "showcasing trendy fashion, stylish outfit, runway-worthy look", 
        "beauty": "glamorous makeup look, perfect lighting, beauty influencer style",
        "luxury": "surrounded by luxury items, upscale environment, sophisticated"
    }
    
    prompt = themes.get(request.theme, themes["lifestyle"])
    
    # Generate image
    img_result = generate_image(ImageGenerateRequest(prompt=prompt, style=request.style))
    
    if not isinstance(img_result, dict) or not img_result.get("success"):
        return JSONResponse(
            status_code=500,
            content={"error": "Image generation failed"}
        )
    
    # Generate caption and hashtags
    captions = {
        "lifestyle": "✨ Living my best life and feeling absolutely radiant! Who else is having an amazing day? 💫",
        "fashion": "🔥 This outfit is giving me all the confidence! What's your go-to look? 👗",
        "beauty": "💄 Glowing from within! Self-care Sunday vibes ✨ How are you treating yourself?",
        "luxury": "🥂 Celebrating the little victories in life! What are you grateful for today? 💎"
    }
    
    hashtags = "#fashionstyle #stylish #trending #glowup #vibes #selfcare #fashionlover #fashion #aesthetic #instafashion #styleoftheday #empowerment #styleinspo #trendy"
    
    return {
        "success": True,
        "content": {
            "image_b64": img_result["image_b64"],
            "caption": captions.get(request.theme, captions["lifestyle"]),
            "hashtags": hashtags,
            "theme": request.theme,
            "account": "meetAkari"
        },
        "metadata": {
            "prompt_used": img_result["prompt_used"],
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "tiktok"
        }
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