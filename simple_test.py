from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(title="TikTok Vibe App - Test")

@app.get("/")
def root():
    return {"message": "TikTok Vibe App is working!", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "venice_key": "configured" if os.getenv("VENICE_API_KEY") else "missing"
    }

@app.get("/test")  
def test():
    return {"test": "success", "message": "Deployment working properly"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))