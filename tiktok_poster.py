#!/usr/bin/env python3
"""
TikTok Sample Post Generator using Venice AI
"""
import requests
import json
import time
import os
from datetime import datetime

# Configuration
VIBE_APP_URL = "http://localhost:8002"
VENICE_API_KEY = os.getenv("VENICE_API_KEY", "VENICE_INFERENCE_KEY_IPKxzZhAO1g8PR_x8W6nUaCVMhpwJqi_JR3vQpVwIj")

def register_user():
    """Register a test user"""
    data = {
        "username": "akari_test",
        "email": "akari@example.com",
        "password": "test123"
    }
    
    response = requests.post(f"{VIBE_APP_URL}/api/register", json=data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ User registered successfully!")
        return token
    elif "already registered" in response.text or "already taken" in response.text:
        # Try to login instead
        login_data = {"username": "akari_test", "password": "test123"}
        response = requests.post(f"{VIBE_APP_URL}/api/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ User logged in successfully!")
            return token
    
    print(f"❌ Registration failed: {response.text}")
    return None

def generate_image(token, prompt):
    """Generate an image using Venice AI via our app"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"prompt": prompt, "model": "qwen-image-2-pro"}
    
    print(f"🎨 Generating image: {prompt}")
    response = requests.post(f"{VIBE_APP_URL}/api/generate-image", json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Image generated: {result['image_url']}")
        return result["image_url"]
    else:
        print(f"❌ Image generation failed: {response.text}")
        return None

def generate_tts(token, text):
    """Generate TTS using Venice AI via our app"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"text": text, "voice": "af_nicole"}
    
    print(f"🎤 Generating TTS: {text[:50]}...")
    response = requests.post(f"{VIBE_APP_URL}/api/generate-tts", json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ TTS generated: {result['audio_url']}")
        return result["audio_url"]
    else:
        print(f"❌ TTS generation failed: {response.text}")
        return None

def create_tiktok_content():
    """Create sample TikTok content"""
    print("🚀 Creating TikTok content with Venice AI...")
    
    # Register/login user
    token = register_user()
    if not token:
        return
    
    # Sample content themes
    content_ideas = [
        {
            "image_prompt": "Beautiful 25-year-old Japanese-Korean woman with voluminous blonde curly hair, wearing a chic burgundy silk dress, sitting in an upscale modern cafe with warm ambient lighting, candlelit atmosphere, smiling warmly at camera, glamorous influencer style, cinematic photography",
            "caption_text": "Just discovered this hidden gem cafe in the city! The ambiance is absolutely perfect for a cozy evening. What's your favorite spot for a peaceful moment?",
            "hashtags": "#CozyVibes #CafeLife #HiddenGems #WarmAmbiance #PerfectEvening"
        },
        {
            "image_prompt": "Stylish 25-year-old Japanese-Korean woman with golden blonde voluminous curls, wearing a trendy oversized cream sweater, sitting by a large window with natural light, reading a book, serene expression, minimalist aesthetic, soft focus background",
            "caption_text": "Sunday mornings are for slow living and good books. Sometimes the best conversations are the ones you have with yourself through the pages of a story.",
            "hashtags": "#SlowLiving #SundayMorning #BookLover #SelfCare #Mindfulness"
        },
        {
            "image_prompt": "Elegant 25-year-old Japanese-Korean woman with blonde curly hair, wearing a sophisticated navy blazer and white blouse, standing in a modern office setting with city view, confident pose, professional lighting, business influencer aesthetic",
            "caption_text": "Monday motivation: Your goals don't have expiration dates. Every small step forward is still progress. What's one thing you're working towards this week?",
            "hashtags": "#MondayMotivation #Goals #Progress #Professional #Mindset"
        }
    ]
    
    # Generate content for each idea
    for i, idea in enumerate(content_ideas, 1):
        print(f"\n--- Creating Content #{i} ---")
        
        # Generate image
        image_url = generate_image(token, idea["image_prompt"])
        if not image_url:
            continue
            
        # Generate TTS for caption
        full_text = f"{idea['caption_text']} {idea['hashtags']}"
        audio_url = generate_tts(token, full_text)
        
        # Save content info
        content = {
            "id": i,
            "image_url": image_url,
            "audio_url": audio_url,
            "caption": idea["caption_text"],
            "hashtags": idea["hashtags"],
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📝 Content #{i} ready:")
        print(f"   Image: {image_url}")
        print(f"   Audio: {audio_url}")
        print(f"   Caption: {idea['caption_text'][:50]}...")
        
        # Small delay between generations
        time.sleep(2)
    
    print(f"\n🎉 Generated {len(content_ideas)} TikTok content pieces!")
    print(f"📊 Check your generation history at: {VIBE_APP_URL}")

if __name__ == "__main__":
    create_tiktok_content()