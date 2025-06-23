#!/usr/bin/env python3
"""
Application Startup Script for Bangla Vai Ticketing System
Starts both FastAPI backend and Streamlit frontend with proper configuration
"""

import subprocess
import sys
import time
import os
import signal
import socket
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

# Import our configuration
from bangla_vai.core.config import settings

def print_banner():
    """Print application banner"""
    print("=" * 80)
    print("🎫 BANGLA VAI TICKETING SYSTEM")
    print("=" * 80)
    print(f"Version: {settings.APP_VERSION}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"FastAPI Host: {settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
    print(f"Streamlit Port: {settings.STREAMLIT_PORT}")
    print("=" * 80)

def check_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

def kill_processes_on_port(port):
    """Kill processes running on a specific port"""
    try:
        # Get PIDs of processes using the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"🔪 Killing process {pid} on port {port}")
                    subprocess.run(['kill', '-9', pid], capture_output=True)
            time.sleep(1)  # Give processes time to die
            return True
    except Exception as e:
        print(f"⚠️  Could not kill processes on port {port}: {e}")
    return False

def ensure_port_available(port, service_name):
    """Ensure a port is available, killing processes if needed"""
    if not check_port_available(port):
        print(f"⚠️  Port {port} is in use. Attempting to free it for {service_name}...")
        if kill_processes_on_port(port):
            if check_port_available(port):
                print(f"✅ Port {port} is now available for {service_name}")
                return True
            else:
                print(f"❌ Could not free port {port} for {service_name}")
                return False
        else:
            print(f"❌ Could not kill processes on port {port}")
            return False
    return True

def check_requirements():
    """Check if required directories exist"""
    required_dirs = [
        settings.VOICES_DIR,
        settings.ATTACHMENTS_DIR,
        settings.CHROMA_DB_PATH,
        Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent if settings.DATABASE_URL.startswith("sqlite") else None
    ]
    
    for dir_path in required_dirs:
        if dir_path and not Path(dir_path).exists():
            print(f"📁 Creating directory: {dir_path}")
            Path(dir_path).mkdir(parents=True, exist_ok=True)

def check_api_keys():
    """Check if required API keys are configured"""
    missing_keys = []
    
    if not settings.ELEVENLABS_API_KEY:
        missing_keys.append("ELEVENLABS_API_KEY")
    
    if not settings.GOOGLE_API_KEY:
        missing_keys.append("GOOGLE_API_KEY")
    
    if missing_keys:
        print("⚠️  WARNING: Missing API Keys:")
        for key in missing_keys:
            print(f"   - {key}")
        print("   Please configure these in your .env file")
        print("   Some features may not work without proper API keys")
        print()

def start_fastapi():
    """Start FastAPI server"""
    print("🚀 Starting FastAPI Backend...")
    
    # Ensure FastAPI port is available
    if not ensure_port_available(settings.FASTAPI_PORT, "FastAPI"):
        raise RuntimeError(f"Cannot start FastAPI - port {settings.FASTAPI_PORT} is not available")
    
    # Change to project root directory
    os.chdir(project_root)
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.bangla_vai.api.main:app",
        "--host", settings.FASTAPI_HOST,
        "--port", str(settings.FASTAPI_PORT)
    ]
    
    if settings.DEBUG:
        cmd.append("--reload")
    
    # Set environment variables for proper imports
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir)
    
    return subprocess.Popen(cmd, env=env)

def start_streamlit():
    """Start Streamlit frontend"""
    print("🎨 Starting Streamlit Frontend...")
    
    # Ensure Streamlit port is available
    if not ensure_port_available(settings.STREAMLIT_PORT, "Streamlit"):
        raise RuntimeError(f"Cannot start Streamlit - port {settings.STREAMLIT_PORT} is not available")
    
    # Change to project root directory  
    os.chdir(project_root)
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "src/bangla_vai/ui/app.py",
        "--server.port", str(settings.STREAMLIT_PORT),
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ]
    
    # Set environment variables for proper imports
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir)
    
    return subprocess.Popen(cmd, env=env)

def wait_for_service(host, port, service_name, timeout=30):
    """Wait for a service to become available"""
    print(f"⏳ Waiting for {service_name} to start...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                if result == 0:
                    print(f"✅ {service_name} is ready!")
                    return True
        except:
            pass
        time.sleep(1)
    
    print(f"⚠️  {service_name} did not start within {timeout} seconds")
    return False

def main():
    """Main startup function"""
    print_banner()
    check_requirements()
    check_api_keys()
    
    # Store process references
    processes = []
    
    def signal_handler(signum, frame):
        """Handle shutdown gracefully"""
        print("\n🛑 Shutting down applications...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass
        sys.exit(0)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start FastAPI
        fastapi_process = start_fastapi()
        processes.append(fastapi_process)
        
        # Wait for FastAPI to be ready
        if not wait_for_service('localhost', settings.FASTAPI_PORT, 'FastAPI', 15):
            raise RuntimeError("FastAPI failed to start")
        
        # Start Streamlit
        streamlit_process = start_streamlit()
        processes.append(streamlit_process)
        
        # Wait for Streamlit to be ready
        if not wait_for_service('localhost', settings.STREAMLIT_PORT, 'Streamlit', 15):
            raise RuntimeError("Streamlit failed to start")
        
        print("\n✅ APPLICATION STARTUP COMPLETE!")
        print("=" * 80)
        print("🔗 ACCESS URLS:")
        print(f"   🎨 Streamlit UI: http://localhost:{settings.STREAMLIT_PORT}")
        print(f"   🔧 FastAPI Docs: http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}/docs")
        print(f"   💚 Health Check: http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}/health")
        print("=" * 80)
        print("🎯 USAGE TIPS:")
        print("   1. Configure API keys in the Streamlit sidebar")
        print("   2. Use 'Voice Complaint' tab for basic voice-to-ticket")
        print("   3. Use 'Voice + Attachment' for enhanced processing")
        print("   4. Check 'Ticket Dashboard' for analytics")
        print("   5. Press Ctrl+C to stop both servers")
        print("=" * 80)
        
        # Keep the main process alive and monitor subprocesses
        while True:
            # Check if processes are still running
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"⚠️  Process {i} ({'FastAPI' if i == 0 else 'Streamlit'}) has stopped unexpectedly")
                    print(f"   Exit code: {process.returncode}")
                    return
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    main() 