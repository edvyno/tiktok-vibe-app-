# Vibe App 🚀

**FastAPI + React web app with Venice AI integration** — built with vibe coding!

## Features ✨

- **JWT Authentication** — Register/login with secure tokens
- **AI Image Generation** — Venice AI qwen-image-2-pro integration
- **Text-to-Speech** — Kokoro TTS with af_nicole voice
- **Generation History** — Track all your AI creations
- **Responsive UI** — Clean React dashboard with Tailwind CSS
- **Ready to Deploy** — Railway, Vercel, or Docker

## Quick Start 🏃‍♂️

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (copy .env.example to .env and fill in keys)
cp .env.example .env

# Run the server
python main.py
```

Visit `http://localhost:8000` — the React app is served from `/static/index.html`

### Deploy to Railway

1. Connect your GitHub repo to Railway
2. Set environment variables in Railway dashboard:
   - `SECRET_KEY` — JWT signing key
   - `VENICE_API_KEY` — Your Venice AI key
3. Deploy automatically on git push!

### Deploy to Docker

```bash
docker build -t vibe-app .
docker run -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e VENICE_API_KEY="your-venice-key" \
  vibe-app
```

## API Endpoints 🛠

### Auth
- `POST /api/register` — Create account
- `POST /api/login` — Login
- `GET /api/me` — Get current user

### AI Generation
- `POST /api/generate-image` — Generate images via Venice AI
- `POST /api/generate-tts` — Generate speech via Kokoro TTS
- `GET /api/history` — Get generation history

## Tech Stack 💻

- **Backend:** FastAPI, SQLAlchemy, JWT auth, bcrypt
- **Frontend:** React 18, Tailwind CSS, vanilla JS (no build step!)
- **AI:** Venice AI (qwen-image-2-pro, Kokoro TTS)
- **Database:** SQLite (easily switch to PostgreSQL)
- **Deploy:** Railway, Vercel, Docker

## Architecture 🏗

```
├── main.py              # FastAPI backend with all endpoints
├── static/
│   ├── index.html       # Single-page React app
│   └── audio/          # Generated TTS files
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container setup
└── railway.json        # Railway deployment config
```

Built with **vibe coding** — described in plain English, built by Claude Sonnet 4! 🤖✨