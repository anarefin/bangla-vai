# 🎫 Bengali Voice based Ticket Creator (POC)

A comprehensive Bengali voice-to-ticket support system that converts Bengali speech complaints and supporting attachments into structured support tickets using advanced AI and natural language processing.

## ✨ Key Features

### 🎤 Advanced Voice Processing
- **Bengali Speech-to-Text**: Accurate Bengali audio transcription using ElevenLabs Scribe API
- **Real-time Recording**: Browser-based voice recording with HTML5 MediaRecorder
- **Multiple Audio Formats**: Support for WAV, MP3, OGG, M4A, WebM
- **Voice Quality Detection**: Automatic audio quality assessment

### 📎 Multi-Modal Attachment Support
- **Visual Content Analysis**: Screenshot, image, and document analysis using Gemini Vision API
- **Document Processing**: PDF, DOC, DOCX, and text file analysis
- **Voice-Attachment Correlation**: AI determines relationships between voice complaints and visual evidence
- **Technical Issue Detection**: Automatic identification of technical problems from screenshots

### 🤖 Intelligent AI Processing
- **Gemini AI Integration**: Advanced processing of Bengali complaints with Vision API support
- **Pattern-Based Extraction**: Hard-coded POC values with intelligent keyword matching
- **Smart Categorization**: Automatic classification across 8+ categories with subcategories
- **Priority Detection**: AI-powered urgency assessment (low, medium, high, urgent, critical)
- **Sentiment Analysis**: Customer emotion detection from voice and text
- **Technical Assessment**: Automated troubleshooting suggestions

### 🎫 Complete Ticketing System
- **Enhanced CRUD Operations**: Create, read, update, delete tickets with attachment support
- **Advanced Filtering**: Filter by status, priority, category, customer, date range
- **Real-time Analytics**: Interactive dashboard with comprehensive statistics
- **Voice-Attachment Linking**: Direct connection between audio files, attachments, and tickets
- **Customer Management**: Complete customer contact and history tracking

### 🔍 Contextual Similarity Search (RAG)
- **Vector Similarity Search**: Retrieve historical tickets similar to a new complaint using SentenceTransformer embeddings
- **ChromaDB Backend**: Persistent local vector database powered by FAISS for fast cosine search
- **Instant Suggestions**: Surface related past resolutions inside the Streamlit UI to accelerate support

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite/PostgreSQL
- **Frontend**: Streamlit with modern UI components and tabs
- **AI/ML**: Google Gemini Pro + Vision API, LangChain
- **Speech Processing**: ElevenLabs Scribe API, Google TTS
- **Document Processing**: Gemini Vision API (handles raw bytes directly)
- **Visualization**: Plotly, Pandas, Streamlit components
- **Audio Processing**: HTML5 MediaRecorder, Pydub
- **Vector Database / RAG**: ChromaDB, SentenceTransformers, FAISS
- **File Handling**: Python multipart, aiofiles

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+
- ElevenLabs API Key (for Bengali speech-to-text)
- Google API Key (for Gemini AI and Vision processing)

### 1. Clone & Setup

```bash
# Clone the repository
git clone <repository-url>
cd bangla-vai

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Required: ElevenLabs API Key for Bengali speech-to-text
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Required: Google API Key for Gemini AI and Vision processing
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Optional: Database configuration (defaults to SQLite)
DATABASE_URL=sqlite:///./tickets.db

# Optional: File storage paths
VOICES_DIR=./voices
ATTACHMENTS_DIR=./attachments
```

### 3. Initialize Database

```bash
# Create database tables and initial data
python database.py
```

### 3b. (Optional) Initialize RAG Vector Database

Build the similarity-search index from the sample `customer_support_tickets.csv` file (≈100 MB on disk):

```bash
python initialize_rag_db.py
# Or, once the FastAPI server is running:
# curl -X POST http://localhost:8000/rag/initialize
```

If you skip this step, the RAG feature in Streamlit will stay disabled until initialization is performed.

### 4. Start the Complete System

**🎯 One-Command Startup (Recommended):**
```bash
# Start both FastAPI backend and Streamlit frontend
python start_app.py
```

This will:
- Start FastAPI server on `http://localhost:8000`
- Start Streamlit interface on `http://localhost:8501`
- Display system status and configuration
- Show helpful tips and URLs

**Alternative Manual Startup:**
```bash
# Terminal 1: FastAPI Backend
python -m uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit Frontend
streamlit run streamlit_app.py --server.port 8501
```

### 5. Access the Application

- **🎨 Main Interface**: http://localhost:8501
- **🔧 API Documentation**: http://localhost:8000/docs
- **💚 Health Check**: http://localhost:8000/health

## 📱 Complete Usage Guide

### 🎤 Voice-Only Tickets

1. **Configure API Keys** in the Streamlit sidebar
2. **Navigate to Voice Complaint Tab**
3. **Record Bengali Complaint**:
   - Click "START RECORDING"
   - Speak clearly in Bengali
   - Click "STOP RECORDING"
   - Download the generated audio file
4. **Upload Audio File** and provide customer information
5. **Click "Process Voice Complaint"** to create ticket

### 🎤📎 Voice + Attachment Tickets (Enhanced)

1. **Navigate to "Voice + Attachment" Sub-tab**
2. **Upload Both Files**:
   - Bengali audio file (voice complaint)
   - Supporting attachment (screenshot, document, etc.)
3. **Provide Context**:
   - Customer information (name, email, phone)
   - Optional attachment description
   - Priority level selection
4. **Click "🚀 CREATE ENHANCED TICKET"**
5. **Review Results**:
   - Voice transcription and translation
   - Attachment analysis and content description
   - Voice-attachment correlation analysis
   - Technical assessment and troubleshooting suggestions
   - Generated ticket with enhanced context

### 📊 Ticket Management & Analytics

1. **Dashboard Overview**: View all tickets with real-time statistics
2. **Advanced Filtering**: Filter by multiple criteria simultaneously
3. **Ticket Updates**: Change status, priority, assignments
4. **Analytics**: View trends, performance metrics, and insights
5. **Export Data**: Download CSV reports for external analysis

## 🔧 API Endpoints

### Voice Processing
- `POST /stt/transcribe` - Transcribe Bengali audio to text
- `POST /tts/convert` - Convert Bengali text to speech
- `POST /config/api-key` - Configure ElevenLabs API key

### Enhanced Ticket Creation
- `POST /process/voice-complaint` - Create ticket from voice only
- `POST /process/voice-with-attachment` - Create enhanced ticket from voice + attachment
- `POST /process/intelligent-analysis` - Test intelligent processing

### Ticket Management
- `GET /tickets` - List all tickets with filtering options
- `GET /tickets/{id}` - Get specific ticket details
- `POST /tickets/create` - Create new ticket manually
- `PUT /tickets/{id}` - Update existing ticket
- `DELETE /tickets/{id}` - Delete ticket
- `GET /tickets/stats` - Get comprehensive ticket statistics

### File Management
- `POST /upload/audio` - Upload audio files
- `POST /upload/attachment` - Upload attachment files
- `GET /files/{filename}` - Download stored files

### RAG – Similarity Search
- `POST /rag/search` - Retrieve tickets similar to a query
- `POST /rag/initialize` - Build or rebuild the vector database from CSV
- `GET /rag/status` - View current RAG database statistics

## 🧠 Intelligent Processing System

### Hard-coded POC Values

**Categories**: technical, billing, general, complaint, feature_request, network, device, service

**Priorities**: low, medium, high, urgent, critical

**Products**: internet, mobile, tv, phone, router, app, website, general

**Subcategories** (automatically mapped):
- **Technical**: Internet Connectivity, Device Configuration, Software Issue, Hardware Problem
- **Billing**: Payment Issue, Bill Dispute, Refund Request, Plan Change
- **Network**: Slow Speed, Connection Drop, No Internet, Poor Signal
- And more...

### Bengali Keyword Recognition

**Technical Keywords**: ইন্টারনেট, নেটওয়ার্ক, কানেকশন, স্পিড, রাউটার, মডেম, ওয়াইফাই
**Billing Keywords**: বিল, পেমেন্ট, টাকা, চার্জ, রিচার্জ, রিফান্ড
**Urgency Keywords**: জরুরি, দ্রুত, তাড়াতাড়ি, এখনি, অবিলম্বে
**Complaint Keywords**: অভিযোগ, সমস্যা, খারাপ, বন্ধ, কাজ করছে না

## 📊 Enhanced Database Schema

### Tickets Table
```sql
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    bengali_description TEXT,
    audio_file_path VARCHAR(500),
    attachment_file_path VARCHAR(500),    -- NEW
    attachment_analysis TEXT,             -- NEW
    status VARCHAR(20) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'medium',
    category VARCHAR(50),
    subcategory VARCHAR(100),             -- NEW
    product VARCHAR(50),                  -- NEW
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(100),
    customer_phone VARCHAR(20),
    assigned_to VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
);
```

## 🎯 Real-World Use Cases

### Customer Support Centers
- **Bengali-speaking Customer Support**: Handle local language complaints efficiently
- **Visual Issue Documentation**: Screenshots and documents provide clear context
- **Automated Triage**: AI categorization reduces manual sorting time
- **Priority Queue Management**: Urgent issues automatically flagged
- **Performance Analytics**: Track resolution times and customer satisfaction

### Government Services
- **Citizen Complaint Processing**: Accept complaints in native Bengali language
- **Multi-modal Evidence**: Citizens can submit both voice and visual evidence
- **Automated Classification**: Route complaints to appropriate departments
- **Transparency Reports**: Generate analytics for public accountability

### E-commerce Platforms
- **Order Issue Resolution**: Voice complaints with order screenshots
- **Product Quality Issues**: Visual evidence with voice descriptions
- **Customer Experience Analytics**: Sentiment tracking and trend analysis
- **Multi-language Support**: Bengali customer base support

### Technical Support
- **Error Documentation**: Screenshots with voice descriptions
- **Troubleshooting Assistance**: AI-generated troubleshooting steps
- **Technical Issue Classification**: Automated categorization of technical problems
- **Knowledge Base Building**: Accumulate common issues and solutions

## 🔒 Security & Privacy

- **API Key Security**: Environment variables for sensitive credentials
- **File Storage**: Secure local storage with organized directory structure
- **Data Privacy**: Customer data handled according to privacy best practices
- **Database Security**: Support for encrypted database connections
- **Input Validation**: Comprehensive validation for all user inputs
- **File Type Restrictions**: Controlled file upload types and sizes

## 🧪 Testing & Quality Assurance

### Test Files Available
- `test_intelligent_processing.py` - Unit tests for the intelligent extraction logic

### Running Tests
```bash
# Test intelligent processing
python test_intelligent_processing.py

# Run the full test suite (if pytest is installed)
pytest
```

## 📈 Performance & Scalability

### Current Capabilities
- **Concurrent Processing**: Async FastAPI handles multiple requests
- **File Size Limits**: Configurable limits for audio and attachment files
- **Database Performance**: Indexed queries for fast ticket retrieval
- **Memory Management**: Efficient processing of large files

### Production Recommendations
- **Database**: PostgreSQL for production environments
- **File Storage**: Cloud storage (AWS S3, Google Cloud Storage) for scalability
- **Caching**: Redis for API response caching
- **Load Balancing**: Nginx for high-traffic scenarios
- **Monitoring**: Application performance monitoring and logging

## 🛠️ Configuration & Customization

### File Storage Configuration
```python
# Customize in environment variables
VOICES_DIR=./voices           # Audio files storage
ATTACHMENTS_DIR=./attachments # Attachment files storage
MAX_AUDIO_SIZE=50MB          # Maximum audio file size
MAX_ATTACHMENT_SIZE=100MB    # Maximum attachment file size
```

### AI Processing Configuration
```python
# Gemini AI settings
GEMINI_MODEL=gemini-pro           # Text processing model
GEMINI_VISION_MODEL=gemini-pro-vision  # Image/document processing
GEMINI_TEMPERATURE=0.3           # AI response creativity
GEMINI_MAX_OUTPUT_TOKENS=2048    # Maximum response length
```

## 📚 Directory Structure

```
bangla-vai/
├── 📁 venv/                     # Python virtual environment
├── 📁 voices/                   # Voice recordings storage
├── 📁 attachments/              # Attachment files storage
├── 📄 fastapi_app.py           # FastAPI backend server
├── 📄 streamlit_app.py         # Main Streamlit interface
├── 📄 start_app.py             # One-command startup script
├── 📄 bengali_stt.py           # Bengali speech-to-text processing
├── 📄 gemini_service.py        # Gemini AI service integration
├── 📄 intelligent_ticket_processor.py # Intelligent processing system
├── 📄 database.py              # Database models and operations
├── 📄 models.py                # Pydantic data models
├── 📄 requirements.txt         # Python dependencies
├── 📄 .env                     # Environment configuration
├── 📄 tickets.db               # SQLite database file
├── 📄 README.md                # This documentation file
├── 📄 VOICE_ATTACHMENT_FEATURE.md # Voice + attachment feature docs
├── 📄 rag_service.py           # Retrieval-Augmented (RAG) vector search service
├── 📄 initialize_rag_db.py     # Utility to build the ChromaDB index
├── 📁 chroma_db/               # Persistent ChromaDB storage
└── 📄 test_*.py                # Test files
```



## 📞 Support & Troubleshooting

### Common Issues

**API Keys Not Working**:
- Ensure keys are correctly set in `.env` file
- Check API quotas and billing status
- Verify key format and permissions

**File Upload Issues**:
- Check file size limits
- Verify supported file formats
- Ensure proper file permissions

**Database Connection Issues**:
- Verify database file permissions
- Check SQLite installation
- Consider switching to PostgreSQL for production

**Audio Recording Problems**:
- Use Chrome or Firefox browsers
- Allow microphone permissions
- Check system audio settings

### Getting Help
- Check the API documentation at `http://localhost:8000/docs`
- Review test files for usage examples
- Check logs in terminal for error messages
- Ensure all dependencies are installed correctly

---

**🎉 Ready to transform your Bengali customer support with advanced voice and attachment processing!**

*Built with ❤️ for Bengali-speaking communities worldwide* 