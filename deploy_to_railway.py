#!/usr/bin/env python3
"""
Quick Railway Deployment Script
"""
import os
import subprocess

def deploy_to_railway():
    print("🚂 Deploying Vibe App to Railway...")
    
    # Check if railway CLI is installed
    try:
        subprocess.run(["railway", "--version"], check=True, capture_output=True)
        print("✅ Railway CLI found")
    except:
        print("❌ Railway CLI not found. Installing...")
        os.system("npm install -g @railway/cli")
    
    # Initialize railway project
    print("🔧 Setting up Railway project...")
    
    # Create railway project
    commands = [
        "railway login --browserless",
        "railway init vibe-app",
        "railway add --service postgresql",
        "railway env set SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')",
        "railway env set VENICE_API_KEY=VENICE_INFERENCE_KEY_IPKxzZhAO1g8PR_x8W6nUaCVMhpwJqi_JR3vQpVwIj",
        "railway up"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        os.system(cmd)
    
    print("\n🎉 Deployment complete!")
    print("🔗 Your app will be available at: https://vibe-app.railway.app")
    print("\n📱 TikTok Account: meetAkari / Futbolas100*")

if __name__ == "__main__":
    deploy_to_railway()