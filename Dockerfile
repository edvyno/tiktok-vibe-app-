FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create directories
RUN mkdir -p static/audio

# Expose port (Railway will override with $PORT env var)
EXPOSE 8000

# Run app - Railway overrides this with startCommand
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]