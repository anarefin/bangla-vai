# 🎫 Bangla Vai - Voice Ticketing System

An AI-powered Bengali voice-to-ticket support system that converts Bengali speech complaints into structured support tickets using advanced speech recognition and natural language processing.

## ✨ Features

### 🎤 Voice Processing
- **Bengali Speech-to-Text**: Convert Bengali audio to text using ElevenLabs Scribe API
- **Real-time Recording**: Browser-based voice recording with HTML5
- **Multiple Audio Formats**: Support for WAV, MP3, OGG, M4A, WebM

### 🤖 AI-Powered Analysis
- **Gemini AI Integration**: Intelligent processing of Bengali complaints
- **Automatic Translation**: Bengali to English translation
- **Smart Categorization**: Automatic classification (technical, billing, general, complaint, feature_request)
- **Priority Detection**: Intelligent priority assignment (low, medium, high, urgent)
- **Sentiment Analysis**: Customer sentiment detection

### 🎫 Ticketing System
- **Complete CRUD Operations**: Create, read, update, delete tickets
- **Advanced Filtering**: Filter by status, priority, category, customer
- **Real-time Analytics**: Dashboard with statistics and visualizations
- **Voice Ticket Linking**: Direct connection between audio files and tickets

### 📊 Analytics & Management
- **Interactive Dashboard**: Comprehensive ticket overview
- **Visual Analytics**: Charts and graphs for ticket statistics
- **Ticket Management**: Update status, priority, assignments
- **Customer Information**: Complete customer contact details

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite/PostgreSQL
- **Frontend**: Streamlit with modern UI components
- **AI/ML**: Google Gemini Pro, LangChain
- **Speech Processing**: ElevenLabs Scribe API, Google TTS
- **Visualization**: Plotly, Pandas
- **Audio Processing**: HTML5 MediaRecorder, Pydub

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- ElevenLabs API Key (for speech-to-text)
- Google API Key (for Gemini AI)

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd bangla-vai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root:

```env
# ElevenLabs API Key (Required for speech-to-text)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Google API Key (Required for AI analysis)
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Database URL (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///./tickets.db
```

### 3. Initialize Database

```bash
# Create database tables
python database.py
```

### 4. Start the System

**Single Command Startup (Recommended):**
```bash
# Start both FastAPI backend and Streamlit frontend
python start_api.py
```

**Alternative - Manual Startup:**
```bash
# Terminal 1: Start FastAPI server
python -m uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit interface  
streamlit run streamlit_ticketing_app.py
```

### 5. Access the Application

- **🎨 Frontend (Streamlit)**: http://localhost:8501
- **🔧 Backend API Docs**: http://localhost:8000/docs
- **💚 Health Check**: http://localhost:8000/health

## 📱 Quick Usage Guide

1. **Run the startup script**: `python start_api.py`
2. **Open your browser** to http://localhost:8501
3. **Configure API keys** in the Streamlit sidebar
4. **Record a Bengali complaint** using the voice recorder
5. **Click "Check for New Recording"** to activate the recording
6. **Click "CREATE TICKET FROM RECORDING"** to start ticket creation
7. **Fill customer information** and submit to create the ticket

## 📱 How to Use

### Creating Voice Tickets

1. **Configure API Keys**: Enter your ElevenLabs and Google API keys in the sidebar
2. **Customer Information**: Fill in customer name (required), email, and phone
3. **Record Complaint**: 
   - Click "START RECORDING"
   - Speak your complaint in Bengali
   - Click "STOP RECORDING"
   - Download the audio file
4. **Upload & Process**: Upload the audio file and click "Process Voice Complaint"
5. **Review Results**: Check transcription, AI analysis, and generated ticket

### Managing Tickets

1. **Dashboard**: View all tickets with filtering options
2. **Analytics**: Monitor ticket statistics and trends
3. **Management**: Update ticket status, priority, and assignments
4. **Search**: Find tickets by various criteria

## 🔧 API Endpoints

### Speech Processing
- `POST /stt/transcribe` - Transcribe Bengali audio
- `POST /tts/convert` - Convert Bengali text to speech
- `POST /config/api-key` - Configure ElevenLabs API key

### Ticket Management
- `POST /tickets/create` - Create new ticket
- `POST /tickets/voice-to-ticket` - Create ticket from voice
- `POST /process/voice-complaint` - Complete voice-to-ticket pipeline
- `GET /tickets` - List tickets with filters
- `GET /tickets/{id}` - Get specific ticket
- `PUT /tickets/{id}` - Update ticket
- `DELETE /tickets/{id}` - Delete ticket
- `GET /tickets/stats` - Get ticket statistics

## 📊 Database Schema

### Ticket Table
- `id`: Primary key
- `title`: Ticket title (auto-generated from AI)
- `description`: Enhanced description
- `bengali_description`: Original Bengali text
- `audio_file_path`: Path to voice recording
- `status`: open, in_progress, resolved, closed
- `priority`: low, medium, high, urgent
- `category`: technical, billing, general, complaint, feature_request
- `customer_name`: Customer name
- `customer_email`: Customer email
- `customer_phone`: Customer phone
- `assigned_to`: Assigned team member
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `resolved_at`: Resolution timestamp

## 🎯 Use Cases

### Customer Support Centers
- Handle Bengali-speaking customers efficiently
- Automatic ticket creation from voice complaints
- Prioritize urgent issues automatically
- Track resolution metrics

### Government Services
- Process citizen complaints in Bengali
- Categorize issues automatically
- Generate reports and analytics
- Improve service delivery

### E-commerce Platforms
- Handle customer complaints in local language
- Automatic issue categorization
- Priority-based resolution workflow
- Customer satisfaction tracking

## 🔒 Security & Privacy

- API keys stored securely in environment variables
- Audio files stored locally with secure paths
- Database supports encryption (PostgreSQL recommended for production)
- No sensitive data logged in plain text

## 🚀 Deployment

### Production Considerations
- Use PostgreSQL for database
- Configure proper CORS settings
- Set up SSL/TLS certificates
- Use environment variables for all secrets
- Configure proper logging
- Set up monitoring and alerts

### Docker Deployment (Optional)

```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000 8501

CMD ["python", "start_api.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

1. **API Key Errors**
   - Ensure ElevenLabs and Google API keys are valid
   - Check API quotas and billing status

2. **Audio Recording Issues**
   - Allow microphone permissions in browser
   - Use HTTPS for production (required for MediaRecorder)

3. **Database Issues**
   - Run `python database.py` to initialize tables
   - Check database permissions

4. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Activate virtual environment

### Getting Help

- Check the FastAPI documentation at `/docs`
- Review server logs for error details
- Ensure all environment variables are set correctly

### Testing the System

```bash
# Test API health
curl http://localhost:8000/health

# Test voice processing endpoint
curl -X POST "http://localhost:8000/process/voice-complaint" \
  -F "file=@test_audio.wav" \
  -F "customer_name=John Doe" \
  -F "customer_email=john@example.com"

# Test ticket creation
curl -X POST "http://localhost:8000/tickets/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Ticket",
    "description": "Test Description",
    "customer_name": "Test Customer",
    "category": "general",
    "priority": "medium"
  }'
```

## 🎉 Acknowledgments

- ElevenLabs for speech-to-text API
- Google for Gemini AI
- Streamlit community for UI framework
- FastAPI for the backend framework
- LangChain for AI orchestration

---

**Ready to transform your customer support with AI-powered Bengali voice processing!** 🚀 