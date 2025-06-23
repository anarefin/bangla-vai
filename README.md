# 🎫 Bengali Voice based Ticket Creator

A Bengali voice-to-ticket support system that converts Bengali speech complaints and attachments into structured support tickets using AI.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd bangla-vai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment (.env file)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Initialize database
python -c "from src.bangla_vai.core.database import create_tables; create_tables()"

# Start application
python scripts/start_app.py
```

**Access Points:**
- 🎨 Main Interface: http://localhost:8501
- 🔧 API Documentation: http://localhost:8000/docs
- 💚 Health Check: http://localhost:8000/health

## 📋 API Endpoints

### Voice Processing
- `POST /stt/transcribe` - Transcribe Bengali audio to text
- `POST /tts/convert` - Convert Bengali text to speech
- `POST /config/api-key` - Configure ElevenLabs API key

### Ticket Operations
- `GET /tickets` - List all tickets with filtering options
- `GET /tickets/{id}` - Get specific ticket details
- `POST /tickets/create` - Create new ticket manually
- `PUT /tickets/{id}` - Update existing ticket
- `DELETE /tickets/{id}` - Delete ticket
- `GET /tickets/stats` - Get comprehensive ticket statistics

### Enhanced Processing
- `POST /process/voice-complaint` - Create ticket from voice only
- `POST /process/voice-with-attachment` - Create enhanced ticket from voice + attachment
- `POST /process/intelligent-analysis` - Test intelligent processing

### File Management
- `POST /upload/audio` - Upload audio files
- `POST /upload/attachment` - Upload attachment files
- `GET /files/{filename}` - Download stored files

### RAG (Similarity Search)
- `POST /rag/search` - Retrieve similar tickets
- `POST /rag/initialize` - Build vector database
- `GET /rag/status` - View RAG database statistics

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: Streamlit
- **AI/ML**: Google Gemini Pro + Vision API
- **Speech**: ElevenLabs Scribe API
- **Vector DB**: ChromaDB with SentenceTransformers

## 📊 Database Schema

```sql
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    bengali_description TEXT,
    audio_file_path VARCHAR(500),
    attachment_file_path VARCHAR(500),
    attachment_analysis TEXT,
    status VARCHAR(20) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'medium',
    category VARCHAR(50),
    subcategory VARCHAR(100),
    product VARCHAR(50),
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(100),
    customer_phone VARCHAR(20),
    assigned_to VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
);
```

## 🔧 Configuration

### Environment Variables
```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
GOOGLE_API_KEY=your_google_gemini_api_key_here
DATABASE_URL=sqlite:///./tickets.db
VOICES_DIR=./voices
ATTACHMENTS_DIR=./attachments
```

---

*Built for Bengali-speaking communities worldwide* 🎉 