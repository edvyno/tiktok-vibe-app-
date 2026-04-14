from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from datetime import datetime, timedelta
import os
import requests
import base64
import json
import secrets
import urllib.parse
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

# Configuration
VENICE_API_KEY = os.getenv("VENICE_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-for-testing")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "awdiebndgxq450cm")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", "https://tiktok-vibe-app.onrender.com/auth/callback")
TIKTOK_SCOPES = "user.info.basic,video.upload,video.publish"

app = FastAPI(title="TikTok Vibe App", description="AI-powered social media content generator")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- TIKTOK OAUTH ENDPOINTS ---

@app.get("/auth/tiktok")
async def start_tiktok_auth():
    """Initiate TikTok OAuth flow"""
    state = secrets.token_urlsafe(32)
    csrf_token = secrets.token_hex(16)
    
    params = {
        "client_key": TIKTOK_CLIENT_KEY,
        "scope": TIKTOK_SCOPES,
        "response_type": "code",
        "redirect_uri": TIKTOK_REDIRECT_URI,
        "state": state
    }
    
    auth_url = f"https://www.tiktok.com/v2/auth/authorize/?{urllib.parse.urlencode(params)}"
    
    # Save state
    home = os.path.expanduser("~")
    state_file = os.path.join(home, "tiktok_oauth_state.json")
    with open(state_file, 'w') as f:
        json.dump({
            "state": state,
            "csrf_token": csrf_token,
            "timestamp": datetime.now().isoformat()
        }, f)
    
    # Also save the URL for easy access
    with open(os.path.join(home, "tiktok_oauth_url.txt"), 'w') as f:
        f.write(auth_url)
    
    return {
        "auth_url": auth_url,
        "csrf_token": csrf_token,
        "state": state,
        "instructions": [
            "1. Open the auth_url in your browser",
            "2. Log in as @meetAkari",
            "3. Authorize the app",
            "4. You'll be redirected back with tokens"
        ]
    }

@app.get("/auth/callback")
async def tiktok_auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle TikTok OAuth callback"""
    if error:
        return JSONResponse(
            status_code=400,
            content={"error": error, "message": "Authorization was denied or failed"}
        )
    
    if not code or not state:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing code or state parameter"}
        )
    
    # Verify state
    home = os.path.expanduser("~")
    state_file = os.path.join(home, "tiktok_oauth_state.json")
    try:
        with open(state_file, 'r') as f:
            saved_state = json.load(f)
        if state != saved_state.get("state"):
            return JSONResponse(status_code=400, content={"error": "State mismatch"})
    except FileNotFoundError:
        return JSONResponse(status_code=400, content={"error": "No saved state found"})
    
    # Exchange code for token
    auth_string = f"{TIKTOK_CLIENT_KEY}:{TIKTOK_CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_b64}"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": TIKTOK_REDIRECT_URI
    }
    
    response = requests.post("https://open.tiktokapis.com/v2/oauth/token/", headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        
        # Save tokens
        token_file = os.path.join(home, "tiktok_tokens.json")
        token_data["obtained_at"] = datetime.now().isoformat()
        with open(token_file, 'w') as f:
            json.dump(token_data, f)
        
        return JSONResponse(content={
            "success": True,
            "message": "TikTok authentication successful!",
            "scope": token_data.get("scope", ""),
            "expires_in": token_data.get("expires_in", 0)
        })
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Token exchange failed: {response.status_code}",
                "details": response.text
            }
        )

@app.get("/api/tiktok-status")
async def tiktok_status():
    """Check TikTok auth status"""
    home = os.path.expanduser("~")
    token_file = os.path.join(home, "tiktok_tokens.json")
    
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            tokens = json.load(f)
        obtained = datetime.fromisoformat(tokens.get("obtained_at", "2000-01-01"))
        expires_in = int(tokens.get("expires_in", 7200))
        is_expired = datetime.now() > obtained + timedelta(seconds=(expires_in - 300))
        
        return {
            "authenticated": True,
            "scope": tokens.get("scope", ""),
            "expires_at": (obtained + timedelta(seconds=expires_in)).isoformat(),
            "is_expired": is_expired
        }
    else:
        return {
            "authenticated": False,
            "auth_url": "/auth/tiktok"
        }

@app.post("/api/post-to-tiktok")
async def post_to_tiktok():
    """Upload and post a video to TikTok"""
    home = os.path.expanduser("~")
    token_file = os.path.join(home, "tiktok_tokens.json")
    
    if not os.path.exists(token_file):
        return JSONResponse(status_code=401, content={"error": "Not authenticated. Visit /auth/tiktok first."})
    
    with open(token_file, 'r') as f:
        tokens = json.load(f)
    
    # Check if expired and try to refresh
    obtained = datetime.fromisoformat(tokens.get("obtained_at", "2000-01-01"))
    expires_in = int(tokens.get("expires_in", 7200))
    
    if datetime.now() > obtained + timedelta(seconds=(expires_in - 300)):
        auth_string = f"{TIKTOK_CLIENT_KEY}:{TIKTOK_CLIENT_SECRET}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_b64}"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": tokens.get("refresh_token")
        }
        
        refresh_resp = requests.post("https://open.tiktokapis.com/v2/oauth/token/", headers=headers, data=data)
        
        if refresh_resp.status_code == 200:
            new_tokens = refresh_resp.json()
            new_tokens["obtained_at"] = datetime.now().isoformat()
            with open(token_file, 'w') as f:
                json.dump(new_tokens, f)
            access_token = new_tokens.get("access_token")
        else:
            return JSONResponse(status_code=401, content={"error": "Token expired and refresh failed. Re-authenticate."})
    else:
        access_token = tokens.get("access_token")
    
    # Initiate upload
    tiktok_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8"
    }
    
    description = f"Akari content - {datetime.now().strftime('%Y-%m-%d')}"
    init_data = {
        "post_info": {
            "title": description,
            "privacy_level": "PUBLIC",
            "disable_comment": False,
            "disable_duet": False,
            "disable_stitch": False
        },
        "source_info": {"source": "FILE_UPLOAD"}
    }
    
    init_response = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
        headers=tiktok_headers,
        json=init_data
    )
    
    if init_response.status_code in [200, 201]:
        return {
            "success": True,
            "message": "Upload initiated",
            "description": description
        }
    else:
        return JSONResponse(
            status_code=500,
            content={"error": f"TikTok API error: {init_response.text}"}
        )

# --- IMAGE GENERATION ENDPOINTS ---

@app.get("/")
def root():
    return {"message": "TikTok Vibe App", "version": "2.0", "status": "running"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "venice_api": "configured" if VENICE_API_KEY else "missing",
        "tiktok_client": "configured" if TIKTOK_CLIENT_KEY else "missing",
        "tiktok_secret": "configured" if TIKTOK_CLIENT_SECRET else "missing"
    }

class ImageGenerateRequest(BaseModel):
    prompt: str
    style: str = "glamorous"

class TikTokContentRequest(BaseModel):
    theme: str = "lifestyle"
    style: str = "glamorous"

@app.get("/api/test")
def test_api():
    return {
        "message": "API working",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production" if os.getenv("PORT") else "development"
    }

@app.post("/api/generate-image")
def generate_image(request: ImageGenerateRequest):
    """Generate Akari image using Venice AI"""
    if not VENICE_API_KEY:
        return JSONResponse(status_code=500, content={"error": "Venice API key not configured"})
    
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
                "prompt": akari_prompt,
                "width": 720,
                "height": 1280
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("images") and len(result["images"]) > 0:
                return {
                    "success": True,
                    "image_b64": result["images"][0],
                    "prompt_used": akari_prompt,
                    "timestamp": datetime.utcnow().isoformat()
                }
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
        return JSONResponse(status_code=500, content={"error": f"Generation failed: {str(e)}"})

@app.post("/api/tiktok-content")
def create_tiktok_content(request: TikTokContentRequest):
    """Create complete TikTok content for Akari"""
    
    themes = {
        "lifestyle": "enjoying a luxurious lifestyle, elegant evening wear, confident pose",
        "fashion": "showcasing trendy fashion, stylish outfit, runway-worthy look", 
        "beauty": "glamorous makeup look, perfect lighting, beauty influencer style",
        "luxury": "surrounded by luxury items, upscale environment, sophisticated"
    }
    
    prompt = themes.get(request.theme, themes["lifestyle"])
    img_result = generate_image(ImageGenerateRequest(prompt=prompt, style=request.style))
    
    if not isinstance(img_result, dict) or not img_result.get("success"):
        return JSONResponse(status_code=500, content={"error": "Image generation failed"})
    
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
        return FileResponse("static/index.html")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting TikTok Vibe App v2.0 with OAuth...")
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
