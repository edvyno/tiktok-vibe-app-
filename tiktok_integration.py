#!/usr/bin/env python3
"""
TikTok API Integration for Akari Vibe App
Connects content generation with actual TikTok posting
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import RedirectResponse, JSONResponse
import os
import json
import requests
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import our existing TikTok API classes
from tiktok_api_setup import TikTokAPI, TikTokPoster

app = FastAPI()

# Global storage for background jobs
JOBS = {}
tiktok_poster = TikTokPoster()

class TikTokIntegration:
    def __init__(self):
        self.api = TikTokAPI()
        self.poster = TikTokPoster()
    
    async def generate_and_post(self, theme="fashion"):
        """Complete pipeline: Generate content -> Post to TikTok"""
        try:
            # Step 1: Generate content using existing API
            content_response = requests.post(
                "https://tiktok-vibe-app.onrender.com/api/tiktok-content",
                json={"theme": theme},
                timeout=60
            )
            
            if content_response.status_code != 200:
                raise Exception(f"Content generation failed: {content_response.text}")
            
            content_data = content_response.json()
            
            # Step 2: Post to TikTok
            success = self.poster.post_content(content_data)
            
            return {
                "success": success,
                "content": content_data,
                "posted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

tiktok_integration = TikTokIntegration()

# --- API ENDPOINTS ---

@app.get("/")
async def root():
    """Main dashboard with TikTok integration"""
    return JSONResponse({
        "service": "Akari TikTok Integration",
        "account": "@meetAkari",
        "status": "ready",
        "endpoints": {
            "auth": "/auth/tiktok",
            "post": "/api/post-to-tiktok",
            "status": "/api/tiktok-status",
            "callback": "/auth/callback"
        }
    })

@app.get("/auth/tiktok")
async def start_tiktok_auth():
    """Initiate TikTok OAuth flow"""
    try:
        auth_url, csrf_token = tiktok_integration.api.get_authorization_url()
        
        return {
            "auth_url": auth_url,
            "csrf_token": csrf_token,
            "instructions": [
                "1. Open the auth_url in your browser",
                "2. Log in as @meetAkari",
                "3. Authorize the app",
                "4. You'll be redirected back with tokens"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth setup failed: {e}")

@app.get("/auth/callback")
async def tiktok_auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle TikTok OAuth callback"""
    if error:
        return JSONResponse({
            "success": False,
            "error": f"TikTok auth error: {error}"
        })
    
    if not code:
        return JSONResponse({
            "success": False,
            "error": "No authorization code received"
        })
    
    try:
        # Exchange code for tokens
        token_response = tiktok_integration.api.exchange_code_for_token(code)
        
        if "access_token" in token_response:
            # Save tokens
            tiktok_integration.poster.save_tokens(token_response)
            
            return RedirectResponse(
                url="/?auth=success",
                status_code=302
            )
        else:
            return JSONResponse({
                "success": False,
                "error": f"Token exchange failed: {token_response}"
            })
    
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Callback processing failed: {e}"
        })

@app.post("/api/post-to-tiktok")
async def post_to_tiktok(
    background_tasks: BackgroundTasks,
    theme: str = "fashion",
    auto_generate: bool = True
):
    """Generate content and post to TikTok (async)"""
    
    # Create job ID
    job_id = f"tiktok_post_{int(datetime.now().timestamp())}"
    
    # Initialize job status
    JOBS[job_id] = {
        "status": "started",
        "theme": theme,
        "started_at": datetime.now().isoformat(),
        "progress": "Initializing TikTok post..."
    }
    
    # Start background task
    background_tasks.add_task(
        process_tiktok_post,
        job_id,
        theme,
        auto_generate
    )
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "TikTok post generation started",
        "check_status_at": f"/api/status/{job_id}"
    }

async def process_tiktok_post(job_id: str, theme: str, auto_generate: bool):
    """Background task to handle TikTok posting"""
    
    try:
        # Update status
        JOBS[job_id]["status"] = "generating"
        JOBS[job_id]["progress"] = "Generating AI content..."
        
        if auto_generate:
            # Use complete pipeline
            result = await tiktok_integration.generate_and_post(theme)
        else:
            # Post existing content (if provided)
            raise NotImplementedError("Manual content posting not implemented yet")
        
        # Update final status
        if result["success"]:
            JOBS[job_id].update({
                "status": "completed",
                "progress": "Successfully posted to @meetAkari!",
                "result": result,
                "completed_at": datetime.now().isoformat()
            })
        else:
            JOBS[job_id].update({
                "status": "failed",
                "progress": f"Failed to post: {result.get('error', 'Unknown error')}",
                "error": result.get('error'),
                "failed_at": datetime.now().isoformat()
            })
    
    except Exception as e:
        JOBS[job_id].update({
            "status": "failed",
            "progress": f"Error during processing: {str(e)}",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Check status of TikTok posting job"""
    
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JOBS[job_id]

@app.get("/api/tiktok-status")
async def tiktok_account_status():
    """Check TikTok authentication and account status"""
    
    tokens = tiktok_integration.poster.load_tokens()
    
    return {
        "account": "@meetAkari",
        "authenticated": bool(tokens and "access_token" in tokens),
        "token_saved_at": tokens.get("saved_at") if tokens else None,
        "api_configured": bool(
            os.getenv("TIKTOK_CLIENT_KEY") and 
            os.getenv("TIKTOK_CLIENT_SECRET")
        ),
        "setup_required": not bool(tokens and os.getenv("TIKTOK_CLIENT_KEY"))
    }

@app.post("/api/test-content-generation")
async def test_content_generation(theme: str = "fashion"):
    """Test content generation without posting to TikTok"""
    
    try:
        content_response = requests.post(
            "https://tiktok-vibe-app.onrender.com/api/tiktok-content",
            json={"theme": theme},
            timeout=60
        )
        
        if content_response.status_code == 200:
            content_data = content_response.json()
            return {
                "success": True,
                "generated_content": {
                    "theme": content_data.get("theme"),
                    "caption": content_data.get("caption"),
                    "hashtags": content_data.get("hashtags"),
                    "image_size": len(content_data.get("image_b64", "")) if "image_b64" in content_data else 0
                }
            }
        else:
            return {
                "success": False,
                "error": f"Content generation failed: {content_response.text}"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Test failed: {str(e)}"
        }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tiktok-integration"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)