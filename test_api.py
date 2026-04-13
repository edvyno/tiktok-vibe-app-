#!/usr/bin/env python3
"""
Test script for TikTok Vibe App API
Tests all the new Venice AI endpoints
"""

import requests
import json
import base64
from datetime import datetime

# Configuration
BASE_URL = "https://tiktok-vibe-app.onrender.com"
# BASE_URL = "http://localhost:8000"  # For local testing

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_generate_image():
    """Test image generation endpoint"""
    print("\n🎨 Testing image generation...")
    
    payload = {
        "prompt": "wearing elegant evening dress, luxury lifestyle, confident pose",
        "style": "glamorous"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/generate-image",
        json=payload,
        timeout=60
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['success']}")
        print(f"Prompt used: {result['prompt_used'][:100]}...")
        print(f"Image data length: {len(result['image_b64'])} characters")
        
        # Save image for testing
        try:
            image_data = base64.b64decode(result['image_b64'])
            with open(f"/tmp/akari_test_{datetime.now().strftime('%H%M%S')}.png", "wb") as f:
                f.write(image_data)
            print("✅ Image saved to /tmp/")
        except Exception as e:
            print(f"⚠️ Could not save image: {e}")
            
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_tiktok_content():
    """Test complete TikTok content generation"""
    print("\n📱 Testing TikTok content creation...")
    
    themes = ["lifestyle", "fashion", "beauty", "luxury"]
    
    for theme in themes[:2]:  # Test first 2 themes
        print(f"\n  Testing theme: {theme}")
        
        payload = {
            "theme": theme,
            "style": "glamorous"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tiktok-content",
            json=payload,
            timeout=60
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['content']
            print(f"  ✅ Theme: {content['theme']}")
            print(f"  📝 Caption: {content['caption'][:50]}...")
            print(f"  🏷️ Hashtags: {len(content['hashtags'].split())} tags")
            print(f"  🖼️ Image: {len(content['image_b64'])} chars")
        else:
            print(f"  ❌ Error: {response.text}")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 TikTok Vibe App API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Image Generation", test_generate_image), 
        ("TikTok Content", test_tiktok_content)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "✅ PASS" if result else "❌ FAIL"))
        except Exception as e:
            results.append((test_name, f"💥 ERROR: {e}"))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    for name, result in results:
        print(f"  {name}: {result}")
    
    passed = sum(1 for _, r in results if "PASS" in r)
    total = len(results)
    print(f"\n🎯 Summary: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()