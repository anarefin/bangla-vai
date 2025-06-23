# Bangla Vai - Project Architecture

## Overview

This document describes the architecture and structure of the Bangla Vai ticketing system, a Bengali voice-based customer support platform with AI processing capabilities.

## Project Structure

```
bangla-vai/
├── src/
│   └── bangla_vai/                 # Main application package
│       ├── __init__.py
│       ├── api/                    # FastAPI REST API
│       │   ├── __init__.py
│       │   ├── main.py            # Main FastAPI application
│       │   ├── routes/            # API route modules (future expansion)
│       │   │   ├── __init__.py
│       │   │   ├── tickets.py
│       │   │   ├── speech.py
│       │   │   └── rag.py
│       │   └── middleware/        # Custom middleware
│       ├── core/                  # Core application components
│       │   ├── __init__.py
│       │   ├── config.py         # Configuration management
│       │   ├── database.py       # Database models and setup
│       │   └── models.py         # Pydantic request/response models
│       ├── services/             # Business logic layer
│       │   ├── __init__.py
│       │   ├── speech_service.py # Bengali STT/TTS functionality
│       │   ├── ai_service.py     # Gemini AI integration
│       │   ├── ticket_service.py # Ticket processing logic
│       │   └── rag_service.py    # RAG (Retrieval Augmented Generation)
│       ├── ui/                   # User interface components
│       │   ├── __init__.py
│       │   ├── app.py           # Main Streamlit application
│       │   ├── components/      # Reusable UI components
│       │   └── pages/           # Streamlit pages
│       └── utils/               # Utility functions
│           ├── __init__.py
│           └── helpers.py
├── data/                        # Data storage
│   ├── databases/              # Database files
│   │   ├── chroma/            # ChromaDB vector database
│   │   │   ├── chroma_db/     # Default ChromaDB instance
│   │   │   ├── advanced_chromadb/
│   │   │   └── my_chromadb/
│   │   └── sqlite/            # SQLite databases
│   │       └── tickets.db
│   ├── uploads/               # User uploads
│   │   ├── voices/           # Audio files
│   │   └── attachments/      # Document attachments
│   └── sample_data/          # Sample datasets
│       └── customer_support_tickets.csv
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration
│   ├── test_api/            # API tests
│   └── test_services/       # Service tests
├── scripts/                 # Utility scripts
│   ├── start_app.py        # Application startup script
│   ├── initialize_rag_db.py # RAG database initialization
│   └── check_rag_status.py # RAG status checker
├── docs/                   # Documentation
│   └── ARCHITECTURE.md     # This file
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore patterns
├── requirements.txt      # Python dependencies
├── setup.py             # Package setup configuration
└── README.md            # Project documentation
```

## Architecture Layers

### 1. Core Layer (`src/bangla_vai/core/`)

**Purpose**: Fundamental application components and configuration.

- **`config.py`**: Centralized configuration management using Pydantic settings
- **`database.py`**: SQLAlchemy ORM models, database connection, and table definitions
- **`models.py`**: Pydantic models for API request/response validation

### 2. Services Layer (`src/bangla_vai/services/`)

**Purpose**: Business logic and external service integrations.

- **`speech_service.py`**: Bengali speech-to-text and text-to-speech using ElevenLabs API
- **`ai_service.py`**: Gemini AI integration for Bengali text processing and vision analysis
- **`ticket_service.py`**: Intelligent ticket processing and categorization
- **`rag_service.py`**: Retrieval Augmented Generation using ChromaDB

### 3. API Layer (`src/bangla_vai/api/`)

**Purpose**: REST API endpoints and HTTP handling.

- **`main.py`**: FastAPI application with all endpoints
- **`routes/`**: Modular route organization (future expansion)
- **`middleware/`**: Custom middleware for authentication, logging, etc.

### 4. UI Layer (`src/bangla_vai/ui/`)

**Purpose**: User interface components and pages.

- **`app.py`**: Main Streamlit application
- **`components/`**: Reusable UI components
- **`pages/`**: Individual Streamlit pages

### 5. Data Layer (`data/`)

**Purpose**: Data storage and management.

- **`databases/`**: Database files (SQLite, ChromaDB)
- **`uploads/`**: User-uploaded files (audio, attachments)
- **`sample_data/`**: Sample datasets and initialization data

## Key Design Patterns

### 1. Dependency Injection

Services are injected as dependencies using factory functions:

```python
# Example from main.py
def get_stt_client():
    if not settings.ELEVENLABS_API_KEY:
        raise HTTPException(status_code=400, detail="API key not configured")
    return BengaliSTT()

@app.post("/stt/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    stt_client: BengaliSTT = Depends(get_stt_client)
):
    return stt_client.transcribe(file)
```

### 2. Configuration Management

Centralized configuration using Pydantic Settings:

```python
# config.py
class Settings:
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/databases/sqlite/tickets.db")
    
settings = Settings()
```

### 3. Service Layer Pattern

Business logic is separated into service classes:

```python
# services/speech_service.py
class BengaliSTT:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        
    def transcribe_audio_file(self, file_path: str) -> Dict[str, Any]:
        # Implementation
        pass
```

### 4. Repository Pattern

Database operations are abstracted through SQLAlchemy ORM:

```python
# core/database.py
class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    # ... other fields
```

## Data Flow

### 1. Voice-to-Ticket Pipeline

```
Audio Upload → STT Service → AI Analysis → Ticket Creation → Database Storage
     ↓              ↓            ↓             ↓              ↓
  File System → ElevenLabs → Gemini AI → SQLAlchemy → SQLite/PostgreSQL
```

### 2. RAG (Retrieval Augmented Generation)

```
User Query → Embedding → Vector Search → Similar Tickets → Response Generation
     ↓           ↓           ↓              ↓                ↓
  Streamlit → Sentence- → ChromaDB → Historical Data → Streamlit UI
              Transformers
```

### 3. Attachment Processing

```
File Upload → Vision Analysis → Content Extraction → Ticket Enhancement
     ↓             ↓               ↓                   ↓
  Multipart → Gemini Vision → Structured Data → Database Update
```

## Technology Stack

### Backend
- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server

### Frontend
- **Streamlit**: Interactive web applications
- **Plotly**: Data visualization
- **Pandas**: Data manipulation

### AI/ML
- **Google Gemini Pro**: Text processing and analysis
- **Google Gemini Vision**: Image and document analysis
- **ElevenLabs Scribe**: Bengali speech-to-text
- **Sentence Transformers**: Text embeddings
- **ChromaDB**: Vector database for similarity search

### Data Storage
- **SQLite**: Primary database (development)
- **PostgreSQL**: Production database option
- **ChromaDB**: Vector database for RAG
- **File System**: Audio and attachment storage

## Security Considerations

### 1. API Key Management
- Environment variables for sensitive data
- No hardcoded credentials
- Validation of API keys before use

### 2. File Upload Security
- File type validation
- Size limits
- Secure file storage paths
- Sanitized filenames

### 3. Database Security
- SQL injection prevention via ORM
- Connection pooling
- Prepared statements

### 4. CORS Configuration
- Configurable allowed origins
- Proper headers for cross-origin requests

## Performance Optimizations

### 1. Async Operations
- FastAPI async endpoints
- Non-blocking I/O operations
- Concurrent processing

### 2. Database Optimization
- Database connection pooling
- Efficient query design
- Indexing on frequently queried fields

### 3. Caching Strategy
- Vector embeddings caching
- API response caching
- Static file caching

### 4. File Handling
- Streaming file uploads
- Temporary file cleanup
- Efficient file processing

## Testing Strategy

### 1. Unit Tests
- Service layer testing
- Business logic validation
- Mock external dependencies

### 2. Integration Tests
- API endpoint testing
- Database operations
- File upload/download

### 3. End-to-End Tests
- Complete workflow testing
- UI interaction testing
- Cross-service communication

## Deployment Considerations

### 1. Environment Configuration
- Separate configs for dev/staging/prod
- Environment-specific settings
- Secrets management

### 2. Scalability
- Horizontal scaling capabilities
- Load balancing ready
- Stateless service design

### 3. Monitoring
- Health check endpoints
- Logging and metrics
- Error tracking

### 4. Backup Strategy
- Database backups
- File system backups
- Configuration backups

## Future Enhancements

### 1. Microservices Architecture
- Service decomposition
- API gateway
- Service mesh

### 2. Advanced AI Features
- Multi-language support
- Advanced sentiment analysis
- Automated ticket routing

### 3. Enhanced UI
- React/Vue.js frontend
- Mobile application
- Real-time updates

### 4. Analytics & Reporting
- Advanced dashboards
- Predictive analytics
- Business intelligence

## Contributing

When contributing to this project, please follow the established architecture patterns:

1. **Separation of Concerns**: Keep business logic in services, API logic in routes, and UI logic in components
2. **Dependency Injection**: Use FastAPI's dependency system for service injection
3. **Configuration Management**: Use the centralized config system
4. **Testing**: Write tests for new functionality
5. **Documentation**: Update documentation for architectural changes

## Conclusion

This architecture provides a solid foundation for a scalable, maintainable Bengali voice-based ticketing system. The modular design allows for easy extension and modification while maintaining clean separation of concerns. 