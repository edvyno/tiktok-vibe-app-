#!/usr/bin/env python3
"""
TikTok API Integration Module
Handles OAuth and posting functionality
"""
import os
import json
import requests
import base64
import urllib.parse
import secrets
from datetime import datetime

# Configuration - load from environment
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "awdiebndgxq450cm")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", "https://tiktok-vibe-app.onrender.com/auth/callback")

class TikTokAPI:
    def __init__(self):
        self.client_key = TIKTOK_CLIENT_KEY
        self.client_secret = TIKTOK_CLIENT_SECRET
        self.redirect_uri = TIKTOK_REDIRECT_URI
        self.base_url = "https://open.tiktokapis.com/v2"
        self.auth_url = "https://www.tiktok.com/v2/auth/authorize/"
        self.token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        self.scopes = "user.info.basic,video.upload,video.publish"
        self._csrf_token = None
        self._state = None
        
    def get_authorization_url(self):
        """Generate TikTok OAuth authorization URL"""
        self._state = secrets.token_urlsafe(32)
        self._csrf_token = secrets.token_hex(16)
        
        params = {
            "client_key": self.client_key,
            "scope": self.scopes,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": self._state
        }
        
        auth_url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        
        # Save state for verification
        state_file = os.path.expanduser("~/tiktok_oauth_state.json")
        with open(state_file, 'w') as f:
            json.dump({
                "state": self._state,
                "csrf_token": self._csrf_token,
                "timestamp": datetime.now().isoformat()
            }, f)
        
        return auth_url, self._state
        
    def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token"""
        if not self.client_secret:
            raise ValueError("TikTok client secret not configured")
            
        # Create basic auth header
        auth_string = f"{self.client_key}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_b64}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(self.token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Save tokens
            token_file = os.path.expanduser("~/tiktok_tokens.json")
            with open(token_file, 'w') as f:
                json.dump({
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in"),
                    "scope": token_data.get("scope"),
                    "obtained_at": datetime.now().isoformat()
                }, f)
            
            return token_data
        else:
            raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")


class TikTokPoster:
    def __init__(self):
        self.token_file = os.path.expanduser("~/tiktok_tokens.json")
        self.base_url = "https://open.tiktokapis.com/v2"
        
    def _get_tokens(self) -> dict:
        """Load saved tokens"""
        if not os.path.exists(self.token_file):
            raise FileNotFoundError("TikTok OAuth tokens not found. Please complete OAuth flow first.")
            
        with open(self.token_file, 'r') as f:
            return json.load(f)
    
    def _refresh_token_if_needed(self, tokens: dict) -> str:
        """Refresh token if expired, return valid access token"""
        # Check if token is expired (add 5min buffer)
        obtained = datetime.fromisoformat(tokens.get("obtained_at", "2000-01-01"))
        expires_in = int(tokens.get("expires_in", 7200))
        
        if datetime.now() > obtained + timedelta(seconds=(expires_in - 300)):
            # Token expired, refresh
            client_key = TIKTOK_CLIENT_KEY
            client_secret = TIKTOK_CLIENT_SECRET
            auth_string = f"{client_key}:{client_secret}"
            auth_b64 = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_b64}"
            }
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": tokens.get("refresh_token")
            }
            
            response = requests.post("https://open.tiktokapis.com/v2/oauth/token/", 
                                   headers=headers, data=data)
            
            if response.status_code == 200:
                new_tokens = response.json()
                
                # Update saved tokens
                new_tokens["obtained_at"] = datetime.now().isoformat()
                with open(self.token_file, 'w') as f:
                    json.dump(new_tokens, f)
                
                return new_tokens.get("access_token")
            else:
                raise Exception(f"Token refresh failed: {response.status_code} - {response.text}")
        
        return tokens.get("access_token")
    
    def initiate_video_upload(self, access_token: str, video_description: str):
        """Initiate video upload to TikTok"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        data = {
            "post_info": {
                "title": video_description,
                "privacy_level": "PUBLIC",
                "disable_comment": False,
                "disable_duet": False,
                "disable_stitch": False
            },
            "source_info": {
                "source": "FILE_UPLOAD"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/post/publish/inbox/video/init/",
            headers=headers,
            json=data
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Upload initiation failed: {response.status_code} - {response.text}")
    
    def upload_video_file(self, upload_url: str, video_path: str):
        """Upload the actual video file"""
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        headers = {
            "Content-Type": "video/mp4",
            "Content-Length": str(len(video_data))
        }
        
        response = requests.put(upload_url, headers=headers, data=video_data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"File upload failed: {response.status_code} - {response.text}")
    
    def post_content(self, content_data: dict) -> bool:
        """Complete pipeline: Initiate upload -> Upload file -> Complete"""
        try:
            tokens = self._get_tokens()
            access_token = self._refresh_token_if_needed(tokens)
            
            # Get video from content data
            video_path = content_data.get("video_path", "")
            if not video_path or not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            description = content_data.get("description", f"Akari content - {datetime.now().strftime('%Y-%m-%d')}")
            
            # Step 1: Initiate upload
            init_response = self.initiate_video_upload(access_token, description)
            upload_url = init_response.get("data", {}).get("upload_url")
            
            if not upload_url:
                raise Exception("No upload URL received from TikTok")
            
            # Step 2: Upload video
            upload_response = self.upload_video_file(upload_url, video_path)
            
            return True
            
        except Exception as e:
            print(f"❌ TikTok posting failed: {str(e)}")
            return False


if __name__ == "__main__":
    # Test the setup
    print("🧪 Testing TikTok API Setup...")
    
    api = TikTokAPI()
    auth_url, state = api.get_authorization_url()
    
    print(f"\n✅ Client Key: {api.client_key}")
    print(f"✅ Client Secret: {'*' * 8} [configured]" if api.client_secret else "❌ Client Secret not set")
    print(f"✅ Redirect URI: {api.redirect_uri}")
    print(f"\n🔗 Auth URL: {auth_url}")
    print(f"\n📝 Next steps:")
    print("1. Open auth URL in browser")
    print("2. Log in to @meetAkari")
    print("3. Authorize the application")
    print("4. Complete the OAuth callback")
