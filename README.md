# Bangla Vai - Bengali Speech Processing API

A comprehensive Bengali speech-to-text and text-to-speech application with FastAPI backend and Streamlit frontend.

## 🚀 Architecture

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   Streamlit     │◄──────────────►│   FastAPI       │
│   Frontend      │    /stt/       │   Backend       │
│   (Port 8501)   │    /tts/       │   (Port 8000)   │
└─────────────────┘                └─────────────────┘
```

- **FastAPI Backend**: RESTful API with automatic documentation
- **Streamlit Frontend**: Modern web interface for user interaction
- **ElevenLabs Scribe API**: High-quality Bengali speech-to-text
- **Google TTS**: Natural Bengali text-to-speech conversion

## ✨ Features

- 🎤 **Voice Recording**: Record audio directly in browser
- 🎯 **Speech-to-Text**: Convert Bengali audio to text
- 📝 **Text-to-Speech**: Convert Bengali text to natural speech
- 🌐 **REST API**: Full-featured API with automatic documentation
- 📥 **Download Options**: Download transcriptions and audio files
- 📊 **Health Monitoring**: API health checks and status monitoring

## 📋 Prerequisites

- Python 3.8 or higher
- ElevenLabs API key (for speech-to-text functionality)
- Modern web browser with microphone access

## 🛠️ Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd bangla-vai
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (optional):
   ```bash
   echo "ELEVENLABS_API_KEY=your_elevenlabs_api_key_here" > .env
   ```

## 🚀 Quick Start

### Option 1: Easy Start (Recommended)
```bash
python start_api.py
```

### Option 2: Manual Start
```bash
# Terminal 1: Start FastAPI server
uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit app  
streamlit run streamlit_app.py
```

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Streamlit App** | http://localhost:8501 | User Interface |
| **FastAPI Docs** | http://localhost:8000/docs | API Documentation |
| **Health Check** | http://localhost:8000/health | Server Status |

## 📚 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check endpoint |
| POST | `/stt/transcribe` | Upload audio file for Bengali transcription |
| POST | `/tts/convert` | Convert Bengali text to speech |
| GET | `/tts/download/{timestamp}` | Download generated speech file |
| POST | `/config/api-key` | Configure ElevenLabs API key |

### Quick API Testing

```bash
# Configure API key
curl -X POST "http://localhost:8000/config/api-key" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "api_key=your_elevenlabs_api_key"

# Test speech-to-text
curl -X POST "http://localhost:8000/stt/transcribe" \
  -F "file=@your_audio.wav" \
  -F "language=bengali"

# Test text-to-speech
curl -X POST "http://localhost:8000/tts/convert" \
  -d "text=আমি বাংলায় কথা বলছি&slow=false"
```

## 🎯 Usage

1. **Start the servers** using `python start_api.py`
2. **Open browser** to http://localhost:8501
3. **Configure API key** in sidebar
4. **Record/upload audio** for transcription or **enter text** for speech generation
5. **Download results**

## 📁 Project Structure

```
bangla-vai/
├── fastapi_app.py          # FastAPI backend server
├── streamlit_app.py        # Streamlit frontend interface  
├── bengali_stt.py          # Core Bengali STT and TTS classes
├── start_api.py            # Helper script to start servers
├── requirements.txt        # Python dependencies
├── voices/                 # Audio files storage (auto-created)
└── venv/                   # Virtual environment
```

## ⚠️ Troubleshooting

### Common Issues

1. **"FastAPI Server Not Running"**
   ```bash
   python start_api.py
   ```

2. **"API Connection Failed"**
   ```bash
   curl http://localhost:8000/health
   ```

3. **API Key Issues**
   - Set via environment variable: `ELEVENLABS_API_KEY=your_key`
   - Or configure through the web interface

### Testing Commands

```bash
# Check server status
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs

# Check if port is in use
lsof -i :8000
```

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000 8501
CMD uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 & \
    streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### Environment Variables
```bash
export ELEVENLABS_API_KEY="your_production_key"
export FASTAPI_BASE_URL="https://your-domain.com"
```

## 🔧 Configuration

- **Audio Formats**: WAV, MP3, OGG, M4A, WebM
- **Languages**: Bengali (primary), other languages supported
- **API Documentation**: Auto-generated at `/docs` and `/redoc`
- **CORS**: Enabled for cross-origin requests

## 🆘 Support

- **Interactive API Testing**: http://localhost:8000/docs
- **Health Monitoring**: http://localhost:8000/health
- **GitHub Issues**: For bugs and feature requests

## 🙏 Acknowledgments

- **ElevenLabs**: High-quality speech recognition API
- **Google**: Text-to-Speech services
- **FastAPI & Streamlit**: Excellent web frameworks 