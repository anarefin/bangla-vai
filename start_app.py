#!/usr/bin/env python3
"""
Start script for Bangla Vai - Starts both FastAPI backend and Streamlit frontend
"""
import os
import sys
import subprocess
import time
import signal
import threading
from dotenv import load_dotenv

# Global variables to track processes
fastapi_process = None
streamlit_process = None

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Shutdown signal received...")
    cleanup_processes()
    sys.exit(0)

def cleanup_processes():
    """Clean up both processes"""
    global fastapi_process, streamlit_process
    
    if streamlit_process:
        print("🔴 Stopping Streamlit app...")
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_process.kill()
    
    if fastapi_process:
        print("🔴 Stopping FastAPI server...")
        fastapi_process.terminate()
        try:
            fastapi_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            fastapi_process.kill()

def wait_for_server(host="localhost", port=8000, timeout=30):
    """Wait for FastAPI server to be ready"""
    import requests
    
    print(f"⏳ Waiting for FastAPI server at http://{host}:{port}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://{host}:{port}/health", timeout=2)
            if response.status_code == 200:
                print("✅ FastAPI server is ready!")
                return True
        except:
            pass
        time.sleep(1)
    
    print("❌ FastAPI server failed to start within timeout")
    return False

def start_fastapi():
    """Start FastAPI server in background"""
    global fastapi_process
    
    print("🚀 Starting FastAPI backend server...")
    
    try:
        fastapi_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "fastapi_app:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✓ FastAPI server started in background")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start FastAPI server: {e}")
        return False

def start_streamlit():
    """Start Streamlit app"""
    global streamlit_process
    
    print("🎨 Starting Streamlit frontend...")
    
    try:
        streamlit_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ])
        
        print("✓ Streamlit app started")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Streamlit app: {e}")
        return False

def main():
    """Start both FastAPI server and Streamlit app"""
    print("🎫 BANGLA VAI - Voice Ticketing System")
    print("=" * 60)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is configured
    api_key = os.getenv("ELEVENLABS_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    print("\n🔑 API Keys Status:")
    if not api_key:
        print("   ⚠️  ElevenLabs API Key: Not configured")
        print("      (Speech-to-text features will be limited)")
    else:
        print(f"   ✓ ElevenLabs API Key: Configured (...{api_key[-4:]})")
    
    if not google_key:
        print("   ⚠️  Google API Key: Not configured")
        print("      (AI analysis features will be limited)")
    else:
        print(f"   ✓ Google API Key: Configured (...{google_key[-4:]})")
    
    print("\n📋 System Configuration:")
    print("   🔧 FastAPI Backend:")
    print("      - Host: 0.0.0.0:8000")
    print("      - API Docs: http://localhost:8000/docs")
    print("      - Health Check: http://localhost:8000/health")
    print("   🎨 Streamlit Frontend:")
    print("      - Host: 0.0.0.0:8501")
    print("      - App URL: http://localhost:8501")
    
    print("\n🔗 Available Features:")
    print("   📢 Bengali Voice Recording")
    print("   🎯 AI-Powered Speech-to-Text")
    print("   🎫 Automatic Ticket Creation")
    print("   📊 Ticket Analytics Dashboard")
    print("   ⚙️  Ticket Management System")
    
    print("\n" + "=" * 60)
    print("🚀 Starting services...")
    print("=" * 60)
    
    try:
        # Step 1: Start FastAPI server
        if not start_fastapi():
            print("❌ Failed to start FastAPI server")
            return 1
        
        # Step 2: Wait for FastAPI to be ready
        if not wait_for_server():
            print("❌ FastAPI server not responding")
            cleanup_processes()
            return 1
        
        # Step 3: Start Streamlit app
        if not start_streamlit():
            print("❌ Failed to start Streamlit app")
            cleanup_processes()
            return 1
        
        # Success message
        print("\n" + "=" * 60)
        print("🎉 BANGLA VAI SYSTEM READY!")
        print("=" * 60)
        print("📱 Open your browser and go to:")
        print("   🎨 Frontend (Streamlit): http://localhost:8501")
        print("   🔧 Backend API Docs: http://localhost:8000/docs")
        print("\n💡 Tips:")
        print("   - Configure API keys in the Streamlit sidebar")
        print("   - Use Chrome/Firefox for best recording experience")
        print("   - Check voices/ folder for saved recordings")
        print("\n🛑 Press Ctrl+C to stop all services")
        print("=" * 60)
        
        # Wait for processes to finish
        try:
            streamlit_process.wait()
        except KeyboardInterrupt:
            pass
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        cleanup_processes()
        return 1
    
    finally:
        cleanup_processes()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 