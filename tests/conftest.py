import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import from our new structure
from src.bangla_vai.core.database import Base, get_db, Ticket
from src.bangla_vai.core.config import Settings
from src.bangla_vai.api.main import app

# Test settings that override main settings
class TestSettings(Settings):
    """Test-specific settings"""
    DATABASE_URL: str = "sqlite:///:memory:"
    VOICES_DIR: str = "./test_data/voices"
    ATTACHMENTS_DIR: str = "./test_data/attachments"
    CHROMA_DB_PATH: str = "./test_data/chroma"
    DEBUG: bool = True

@pytest.fixture(scope="session")
def test_settings():
    """Provide test settings"""
    return TestSettings()

@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test"""
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def override_get_db(test_db):
    """Override the get_db dependency for testing"""
    def _override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_client(override_get_db):
    """Create a test client"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    return client

@pytest.fixture(scope="function")
def sample_ticket_data():
    """Provide sample ticket data for testing"""
    return {
        "title": "Test Ticket",
        "description": "This is a test ticket description",
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "customer_phone": "1234567890",
        "category": "technical",
        "priority": "medium"
    }

@pytest.fixture(scope="function")
def create_test_directories():
    """Create test directories"""
    test_dirs = [
        "./test_data/voices",
        "./test_data/attachments", 
        "./test_data/chroma"
    ]
    
    for directory in test_dirs:
        os.makedirs(directory, exist_ok=True)
    
    yield test_dirs
    
    # Cleanup
    import shutil
    if os.path.exists("./test_data"):
        shutil.rmtree("./test_data")

@pytest.fixture(scope="function")
def mock_audio_file():
    """Create a mock audio file for testing"""
    # Create a temporary audio file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"mock audio content")
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path) 