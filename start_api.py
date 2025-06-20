#!/usr/bin/env python3
"""
Start script for Bangla Vai FastAPI server
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    """Start the FastAPI server"""
    print("🚀 Starting Bangla Vai FastAPI Server...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is configured
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("⚠️  WARNING: ELEVENLABS_API_KEY not found in environment variables")
        print("   Speech-to-text features will not work without a valid API key")
        print("   You can set it later through the Streamlit interface")
    else:
        print(f"✓ API Key configured (ends with: ...{api_key[-4:]})")
    
    print("\n📋 Server Configuration:")
    print("   - Host: 0.0.0.0 (accessible from other devices)")
    print("   - Port: 8000")
    print("   - Reload: Enabled (for development)")
    print("   - API Documentation: http://localhost:8000/docs")
    print("   - Health Check: http://localhost:8000/health")
    
    print("\n🔗 Endpoints:")
    print("   - POST /stt/transcribe - Speech to Text")
    print("   - POST /tts/convert - Text to Speech")
    print("   - POST /config/api-key - Set API Key")
    print("   - GET /health - Health Check")
    
    print("\n" + "=" * 50)
    print("🌐 Starting server... Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "fastapi_app:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting server: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure you've installed the requirements: pip install -r requirements.txt")
        print("   2. Check if port 8000 is already in use")
        print("   3. Try running: python fastapi_app.py")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 