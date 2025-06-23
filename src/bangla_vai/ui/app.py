import streamlit as st
import os
import tempfile
import requests
import base64
from io import BytesIO
import time
import numpy as np
import streamlit.components.v1 as components
import re
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import glob
from pathlib import Path
import logging

# Import from our new configuration
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from bangla_vai.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI base URL - use configuration
FASTAPI_BASE_URL = f"http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}"

def check_fastapi_connection():
    """Check if FastAPI server is running"""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def process_voice_complaint(file_bytes, filename, customer_name, customer_email=None, customer_phone=None):
    try:
        files = {"file": (filename, file_bytes, "audio/mpeg")}
        data = {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone
        }
        
        response = requests.post(
            f"{FASTAPI_BASE_URL}/process/voice-complaint",
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Unknown error")
    except Exception as e:
        return False, f"Error: {str(e)}"

def process_voice_with_attachment(voice_file_bytes, voice_filename, attachment_file_bytes, attachment_filename, 
                                customer_name, customer_email=None, customer_phone=None, attachment_description=""):
    """Process voice complaint with optional attachment using the enhanced API endpoint"""
    try:
        files = {
            "audio_file": (voice_filename, voice_file_bytes, "audio/mpeg")
        }
        
        # Only add attachment if it's provided
        if attachment_file_bytes is not None and attachment_filename is not None:
            files["attachment_file"] = (attachment_filename, attachment_file_bytes, "application/octet-stream")
        
        data = {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "attachment_description": attachment_description
        }
        
        response = requests.post(
            f"{FASTAPI_BASE_URL}/process/voice-with-attachment",
            files=files,
            data=data,
            timeout=180  # Longer timeout for AI processing
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Unknown error")
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_tickets(status=None, priority=None, category=None, limit=50):
    try:
        params = {"limit": limit}
        if status and status != "All":
            params["status"] = status
        if priority and priority != "All":
            params["priority"] = priority
        if category and category != "All":
            params["category"] = category
            
        response = requests.get(f"{FASTAPI_BASE_URL}/tickets", params=params, timeout=30)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Unknown error")
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_ticket_stats():
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/tickets/stats", timeout=30)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Unknown error")
    except Exception as e:
        return False, f"Error: {str(e)}"

def set_api_key(api_key: str):
    """Set API key in FastAPI server"""
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/config/api-key",
            data={"api_key": api_key},
            timeout=10
        )
        if response.status_code == 200:
            return True, "API key configured successfully"
        else:
            return False, response.json().get("detail", "Failed to set API key")
    except Exception as e:
        return False, f"Error connecting to API server: {str(e)}"

def transcribe_audio_via_api(file_bytes: bytes, filename: str, language: str = "bengali"):
    """Transcribe audio using FastAPI endpoint"""
    try:
        files = {"file": (filename, file_bytes, "audio/mpeg")}
        data = {"language": language}
        
        response = requests.post(
            f"{FASTAPI_BASE_URL}/stt/transcribe",
            files=files,
            data=data,
            timeout=60  # Longer timeout for transcription
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return False, error_detail
            
    except Exception as e:
        return False, f"Error during transcription: {str(e)}"

def text_to_speech_via_api(text: str, slow: bool = False, return_file: bool = False):
    """Convert text to speech using FastAPI endpoint"""
    try:
        data = {
            "text": text,
            "slow": slow,
            "return_file": return_file
        }
        
        if return_file:
            response = requests.post(
                f"{FASTAPI_BASE_URL}/tts/convert",
                data=data,
                timeout=30
            )
            if response.status_code == 200:
                return True, response.content  # Return audio bytes
            else:
                return False, "Failed to generate speech"
        else:
            response = requests.post(
                f"{FASTAPI_BASE_URL}/tts/convert",
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                error_detail = response.json().get("detail", "Unknown error")
                return False, error_detail
                
    except Exception as e:
        return False, f"Error during text-to-speech conversion: {str(e)}"

def download_speech_file(timestamp: int):
    """Download generated speech file by timestamp"""
    try:
        response = requests.get(
            f"{FASTAPI_BASE_URL}/tts/download/{timestamp}",
            timeout=30
        )
        
        if response.status_code == 200:
            return True, response.content
        else:
            return False, "File not found"
            
    except Exception as e:
        return False, f"Error downloading file: {str(e)}"

def create_html5_recorder():
    """Create HTML5 audio recorder component"""
    html_code = """
    <div id="audio-recorder">
        <style>
            .recorder-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                margin: 10px 0;
            }
            .record-btn {
                background: #ff4757;
                color: white;
                border: none;
                border-radius: 50px;
                padding: 15px 30px;
                font-size: 18px;
                cursor: pointer;
                margin: 10px;
                transition: all 0.3s ease;
            }
            .record-btn:hover {
                background: #ff3742;
                transform: scale(1.05);
            }
            .record-btn:disabled {
                background: #95a5a6;
                cursor: not-allowed;
                transform: none;
            }
            .stop-btn {
                background: #2ed573;
            }
            .stop-btn:hover {
                background: #20b85a;
            }
            .status {
                margin: 10px 0;
                font-weight: bold;
                color: white;
            }
            .recording {
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
        </style>
        
        <div class="recorder-container">
            <div class="status" id="status">🎤 Ready to Record</div>
            <button class="record-btn" id="recordBtn" onclick="startRecording()">🔴 START RECORDING</button>
            <button class="record-btn stop-btn" id="stopBtn" onclick="stopRecording()" style="display: none;">⏹️ STOP RECORDING</button>
            <audio id="audioPlayback" controls style="margin-top: 15px; display: none;"></audio>
            <button class="record-btn" id="downloadBtn" onclick="downloadRecording()" style="display: none;">💾 DOWNLOAD RECORDING</button>
        </div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let recordedBlob;

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 16000
                    } 
                });
                
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = function(event) {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = function() {
                    recordedBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(recordedBlob);
                    
                    const audioPlayback = document.getElementById('audioPlayback');
                    audioPlayback.src = audioUrl;
                    audioPlayback.style.display = 'block';
                    
                    document.getElementById('downloadBtn').style.display = 'inline-block';
                    document.getElementById('status').innerHTML = '✅ Recording Complete!';
                };
                
                mediaRecorder.start();
                
                document.getElementById('recordBtn').style.display = 'none';
                document.getElementById('stopBtn').style.display = 'inline-block';
                document.getElementById('status').innerHTML = '🔴 Recording...';
                document.getElementById('status').classList.add('recording');
                
            } catch (error) {
                console.error('Error accessing microphone:', error);
                document.getElementById('status').innerHTML = '❌ Microphone access denied. Please allow permissions and try again.';
            }
        }

        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                
                document.getElementById('recordBtn').style.display = 'inline-block';
                document.getElementById('stopBtn').style.display = 'none';
                document.getElementById('status').classList.remove('recording');
            }
        }

        function downloadRecording() {
            if (recordedBlob) {
                const url = URL.createObjectURL(recordedBlob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `recording_${Date.now()}.wav`;
                a.click();
                URL.revokeObjectURL(url);
            }
        }
    </script>
    """
    return html_code

def main():
    st.set_page_config(
        page_title="Bangla Vai",
        page_icon="🎤",
        layout="wide"
    )
    
    # Initialize session state variables
    if 'show_rag_section' not in st.session_state:
        st.session_state.show_rag_section = False
    if 'current_ticket' not in st.session_state:
        st.session_state.current_ticket = None
    if 'show_rag_search' not in st.session_state:
        st.session_state.show_rag_search = False
    
    st.title("🎤 Bangla Vai")
    st.markdown("### Powered by FastAPI, ElevenLabs Scribe API & Google TTS")
    
    # Check FastAPI connection
    api_connected = check_fastapi_connection()
    
    if not api_connected:
        st.error("🚨 **FastAPI Server Not Running**")
        st.markdown("""
        **To start the API server, run this command in your terminal:**
        ```bash
        uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
        ```
        
        **Or use this command:**
        ```bash
        python fastapi_app.py
        ```
        
        Then refresh this page.
        """)
        st.stop()
    
    st.success("✅ API Server Connected")
    
    # Sidebar for API key configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "ElevenLabs API Key",
            type="password",
            value=os.getenv("ELEVENLABS_API_KEY", ""),
            help="Enter your ElevenLabs API key (required for speech-to-text)"
        )
        
        if api_key:
            if st.button("🔧 Configure API Key"):
                success, message = set_api_key(api_key)
                if success:
                    st.success(f"✓ {message}")
                else:
                    st.error(f"❌ {message}")
        else:
            st.warning("⚠️ Please enter your API key for speech-to-text features")
        
        st.markdown("---")
        st.markdown("**API Server Status**: ✅ Connected")
        st.markdown(f"**Base URL**: `{FASTAPI_BASE_URL}`")
    
    # Create tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs(["🎙️ Voice Recorder", "📝 Text to Speech", "🔴 Real-time STT", "🎤 Voice Complaint"])
    
    # Tab 1: HTML5 Recorder
    with tab1:
        st.header("🎙️ Voice Recorder")
        st.markdown("**Record your voice directly in the browser**")
        
        # HTML5 Audio Recorder
        components.html(create_html5_recorder(), height=300)
       
        # Upload area for transcription
        st.markdown("---")
        st.markdown("### 📤 Upload Your Recording for Transcription")
        uploaded_file = st.file_uploader(
            "Upload the audio file you just downloaded:",
            type=['wav', 'mp3', 'ogg', 'm4a', 'webm'],
            help="Upload the audio file you downloaded from the recorder above"
        )
        
        if uploaded_file and api_key:
            if st.button("🎯 Transcribe Uploaded Recording", type="primary"):
                try:
                    # Get file bytes
                    file_bytes = uploaded_file.read()
                    filename = uploaded_file.name
                    
                    st.info(f"📁 Processing file: {filename}")
                    
                    # Show progress
                    with st.spinner("Transcribing audio via API... This may take a few moments."):
                        success, result = transcribe_audio_via_api(file_bytes, filename)
                    
                    if success:
                        st.success("✅ Transcription completed!")
                        
                        # Extract transcription text and other info
                        transcription_text = result.get('transcription', '')
                        detected_lang = result.get('language_code', 'unknown')
                        lang_probability = result.get('language_probability', 0)
                        saved_filename = result.get('saved_as', 'Unknown')
                        saved_path = result.get('saved_path', 'Unknown')
                        
                        # Display file save information
                        st.info(f"📁 **File saved as:** `{saved_filename}` in voices folder")
                        
                        # Display language detection information
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"**Detected Language:** {detected_lang}")
                        with col2:
                            st.info(f"**Confidence:** {lang_probability:.2f}")
                        
                        # Check if the result looks like Bengali
                        bengali_pattern = r'[\u0980-\u09FF]'  # Bengali Unicode range
                        has_bengali = bool(re.search(bengali_pattern, transcription_text))
                        
                        if not has_bengali and detected_lang not in ['ben', 'bengali']:
                            st.warning(f"""
                            ⚠️ **Language Detection Issue**: 
                            - Detected as '{detected_lang}' instead of Bengali
                            - The transcription may not be accurate
                            - Please ensure your audio contains clear Bengali speech
                            """)
                        elif has_bengali:
                            st.success("✓ Bengali characters detected - transcription looks good!")
                        
                        # Display transcription
                        st.subheader("📝 Transcription Result")
                        st.text_area(
                            "Bengali Text:",
                            value=transcription_text,
                            height=100
                        )
                        
                        # Download transcription
                        st.download_button(
                            label="📥 Download Transcription",
                            data=transcription_text,
                            file_name=f"transcription_{int(time.time())}.txt",
                            mime="text/plain"
                        )
                        
                        # Show full API response in expander
                        with st.expander("🔍 View Full API Response"):
                            st.json(result)
                    else:
                        st.error(f"❌ Transcription failed: {result}")
                        
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        
        elif uploaded_file and not api_key:
            st.warning("⚠️ Please configure your ElevenLabs API key in the sidebar to transcribe audio.")
        
        st.markdown("---")
        st.markdown("### 📋 How to use:")
        st.markdown("""
        1. 🔴 Click **START RECORDING**
        2. 🎤 Allow microphone permissions when prompted
        3. 🗣️ Speak into your microphone
        4. ⏹️ Click **STOP RECORDING** when done
        5. 🎧 Listen to your recording (audio player will appear)
        6. 💾 Click **DOWNLOAD RECORDING** to save the file
        7. 📤 Upload the downloaded file in the "Upload Audio" section for transcription
        """)

    # Tab 2: Text to Speech
    with tab2:
        st.header("📝 Bengali Text to Speech")
        st.markdown("Enter Bengali text and convert it to speech using the API.")
        
        # Text input
        bengali_text = st.text_area(
            "Enter Bengali Text:",
            height=150,
            placeholder="এখানে বাংলা টেক্সট লিখুন...",
            help="Type or paste Bengali text here"
        )
        
        if bengali_text.strip():
            col1, col2 = st.columns(2)
            
            with col1:
                # Speed control
                slow_speech = st.checkbox("🐌 Slow Speech", help="Enable for slower speech")
            
            with col2:
                # Convert to speech button
                if st.button("🔊 Convert to Speech", type="primary"):
                    try:
                        with st.spinner("Converting text to speech via API..."):
                            # First get metadata
                            success, result = text_to_speech_via_api(bengali_text, slow=slow_speech, return_file=False)
                        
                        if success:
                            st.success("✅ Speech generated successfully!")
                            
                            # Get the timestamp for downloading
                            timestamp = result.get('timestamp')
                            
                            if timestamp:
                                # Download the audio file
                                download_success, audio_bytes = download_speech_file(timestamp)
                                
                                if download_success:
                                    # Play audio
                                    st.audio(audio_bytes, format='audio/mp3')
                                    
                                    # Download button
                                    st.download_button(
                                        label="📥 Download Speech Audio",
                                        data=audio_bytes,
                                        file_name=f"bengali_speech_{timestamp}.mp3",
                                        mime="audio/mp3"
                                    )
                                    
                                    # Also provide text download
                                    st.download_button(
                                        label="📄 Download Text File",
                                        data=bengali_text,
                                        file_name=f"bengali_text_{timestamp}.txt",
                                        mime="text/plain"
                                    )
                                    
                                    # Show API response details
                                    with st.expander("🔍 View API Response"):
                                        st.json(result)
                                else:
                                    st.error(f"❌ Failed to download audio: {audio_bytes}")
                            else:
                                st.error("❌ No timestamp received from API")
                        else:
                            st.error(f"❌ Speech generation failed: {result}")
                            
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
    
    # Tab 3: Real-time Speech to Text
    with tab3:
        st.header("🔴 Real-time Bengali Voice to Text")
        st.markdown("**Live transcription of your Bengali speech**")
        
        if not api_key:
            st.warning("⚠️ Please configure your ElevenLabs API key in the sidebar to use real-time transcription.")
        else:
            # Real-time transcription interface
            st.markdown("### 🎤 Live Transcription")
            
            # Create columns for controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                start_realtime = st.button("🔴 Start Live Transcription", type="primary")
            with col2:
                stop_realtime = st.button("⏹️ Stop Transcription")
            with col3:
                clear_text = st.button("🗑️ Clear Text")
            
            # Initialize session state for real-time transcription
            if 'realtime_active' not in st.session_state:
                st.session_state.realtime_active = False
            if 'transcription_text' not in st.session_state:
                st.session_state.transcription_text = ""
            if 'audio_chunks' not in st.session_state:
                st.session_state.audio_chunks = []
            if 'clear_requested' not in st.session_state:
                st.session_state.clear_requested = False
            
            # Handle button clicks
            if start_realtime:
                st.session_state.realtime_active = True
            if stop_realtime:
                st.session_state.realtime_active = False
            if clear_text:
                st.session_state.transcription_text = ""
                st.session_state.audio_chunks = []
                # Set a flag to trigger JavaScript clear
                st.session_state.clear_requested = True
            
            # Status indicator
            if st.session_state.realtime_active:
                st.success("🟢 **LIVE**: Recording and transcribing...")
            else:
                st.info("🔴 **STOPPED**: Click 'Start Live Transcription' to begin")
            
            # Real-time transcription component
            realtime_html = f"""
            <div id="realtime-stt">
                <style>
                    .realtime-container {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 15px;
                        padding: 20px;
                        margin: 10px 0;
                        color: white;
                        text-align: center;
                    }}
                    .status-indicator {{
                        font-size: 18px;
                        font-weight: bold;
                        margin: 10px 0;
                    }}
                    .transcription-display {{
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        padding: 15px;
                        margin: 15px 0;
                        min-height: 100px;
                        max-height: 300px;
                        overflow-y: auto;
                        text-align: left;
                        font-family: 'SolaimanLipi', 'Kalpurush', sans-serif;
                        font-size: 16px;
                        line-height: 1.6;
                    }}
                    .recording-indicator {{
                        display: inline-block;
                        width: 12px;
                        height: 12px;
                        background: red;
                        border-radius: 50%;
                        animation: pulse 1s infinite;
                        margin-right: 8px;
                    }}
                    @keyframes pulse {{
                        0% {{ opacity: 1; }}
                        50% {{ opacity: 0.3; }}
                        100% {{ opacity: 1; }}
                    }}
                    .language-info {{
                        font-size: 14px;
                        margin: 10px 0;
                        opacity: 0.8;
                    }}
                    .copy-button {{
                        background: #28a745;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 8px 16px;
                        cursor: pointer;
                        margin-top: 10px;
                        font-size: 14px;
                    }}
                    .copy-button:hover {{
                        background: #218838;
                    }}
                </style>
                
                <div class="realtime-container">
                    <div class="status-indicator">
                        <span id="status-text">🎤 Real-time Bengali Speech Recognition</span>
                    </div>
                    
                    <div class="language-info">
                        Language: Bengali (বাংলা) | Mode: Continuous Recognition
                    </div>
                    
                    <div class="transcription-display" id="transcription-output">
                        <div style="text-align: center; opacity: 0.7; padding: 20px;">
                            {st.session_state.transcription_text if st.session_state.transcription_text else "Transcribed text will appear here..."}
                        </div>
                    </div>
                    
                    <button class="copy-button" onclick="copyTranscriptToClipboard()" id="copy-btn" style="display: none;">
                        📋 Copy Current Transcript
                    </button>
                </div>
            </div>

            <script>
                let recognition;
                let isListening = false;
                let transcriptionOutput = document.getElementById('transcription-output');
                let statusText = document.getElementById('status-text');
                let copyBtn = document.getElementById('copy-btn');
                
                // Initialize with existing session state content
                let currentTranscript = `{st.session_state.transcription_text}`;
                
                // Display initial content
                if (currentTranscript) {{
                    transcriptionOutput.innerHTML = '<div style="padding: 10px;">' + currentTranscript + '</div>';
                    copyBtn.style.display = 'inline-block';
                }}

                // Check if browser supports Web Speech API
                if ('webkitSpeechRecognition' in window) {{
                    recognition = new webkitSpeechRecognition();
                }} else if ('SpeechRecognition' in window) {{
                    recognition = new SpeechRecognition();
                }} else {{
                    statusText.textContent = '❌ Speech Recognition not supported in this browser';
                    transcriptionOutput.innerHTML = '<div style="text-align: center; color: #ff6b6b;">Web Speech API is not supported in your browser. Please use Chrome, Edge, or Safari.</div>';
                }}

                if (recognition) {{
                    // Configure recognition
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    recognition.lang = 'bn-BD'; // Bengali (Bangladesh)
                    
                    recognition.onstart = function() {{
                        isListening = true;
                        statusText.innerHTML = '<span class="recording-indicator"></span>🔴 LISTENING - Speak in Bengali';
                        console.log('Speech recognition started');
                    }};
                    
                    recognition.onresult = function(event) {{
                        let interimTranscript = '';
                        let finalTranscript = '';
                        
                        for (let i = event.resultIndex; i < event.results.length; i++) {{
                            const transcript = event.results[i][0].transcript;
                            if (event.results[i].isFinal) {{
                                finalTranscript += transcript + ' ';
                            }} else {{
                                interimTranscript += transcript;
                            }}
                        }}
                        
                        if (finalTranscript) {{
                            currentTranscript += finalTranscript;
                            copyBtn.style.display = 'inline-block';
                            
                            // Store in localStorage for persistence
                            localStorage.setItem('bengali_transcript', currentTranscript);
                        }}
                        
                        // Always show current + interim
                        transcriptionOutput.innerHTML = '<div style="padding: 10px;">' + currentTranscript + '<span style="color: #a0a0a0; font-style: italic;">' + interimTranscript + '</span></div>';
                        
                        // Auto-scroll to bottom
                        transcriptionOutput.scrollTop = transcriptionOutput.scrollHeight;
                    }};
                    
                    recognition.onerror = function(event) {{
                        console.error('Speech recognition error:', event.error);
                        statusText.textContent = '❌ Error: ' + event.error;
                        
                        if (event.error === 'not-allowed') {{
                            transcriptionOutput.innerHTML = '<div style="text-align: center; color: #ff6b6b; padding: 20px;">Microphone access denied. Please allow microphone permissions and refresh the page.</div>';
                        }} else if (event.error === 'no-speech') {{
                            statusText.textContent = '🔴 No speech detected - Please speak clearly';
                            if (isListening) {{
                                setTimeout(() => {{
                                    if (isListening) recognition.start();
                                }}, 1000);
                            }}
                        }} else if (event.error === 'network') {{
                            transcriptionOutput.innerHTML = '<div style="text-align: center; color: #ff6b6b; padding: 20px;">Network error. Please check your internet connection.</div>';
                        }}
                    }};
                    
                    recognition.onend = function() {{
                        console.log('Speech recognition ended');
                        if (isListening) {{
                            setTimeout(() => {{
                                if (isListening) recognition.start();
                            }}, 100);
                        }} else {{
                            statusText.textContent = '⏹️ STOPPED - Click Start to begin transcription';
                            if (currentTranscript) {{
                                localStorage.setItem('bengali_transcript', currentTranscript);
                            }}
                        }}
                    }};
                }}

                // Function to start recognition
                function startRealtimeRecognition() {{
                    if (recognition && !isListening) {{
                        if (!currentTranscript) {{
                            transcriptionOutput.innerHTML = '<div style="text-align: center; opacity: 0.7; padding: 20px;">Starting recognition...</div>';
                        }}
                        isListening = true;
                        recognition.start();
                    }}
                }}

                // Function to stop recognition
                function stopRealtimeRecognition() {{
                    if (recognition && isListening) {{
                        isListening = false;
                        recognition.stop();
                        statusText.textContent = '⏹️ STOPPED - Transcription paused';
                        if (currentTranscript) {{
                            localStorage.setItem('bengali_transcript', currentTranscript);
                        }}
                    }}
                }}

                // Function to clear transcript
                function clearTranscript() {{
                    currentTranscript = '';
                    transcriptionOutput.innerHTML = '<div style="text-align: center; opacity: 0.7; padding: 20px;">Transcribed text will appear here...</div>';
                    copyBtn.style.display = 'none';
                    localStorage.removeItem('bengali_transcript');
                }}
                
                // Function to copy transcript to clipboard
                function copyTranscriptToClipboard() {{
                    if (currentTranscript) {{
                        const textarea = document.createElement('textarea');
                        textarea.value = currentTranscript;
                        document.body.appendChild(textarea);
                        textarea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textarea);
                        
                        const originalText = copyBtn.textContent;
                        copyBtn.textContent = '✅ Copied!';
                        setTimeout(() => {{
                            copyBtn.textContent = originalText;
                        }}, 2000);
                    }}
                }}

                // Auto-start based on Streamlit state
                {'startRealtimeRecognition();' if st.session_state.realtime_active else 'stopRealtimeRecognition();'}
                
                // Check if clear was requested from Streamlit
                {'clearTranscript();' if st.session_state.clear_requested else ''}
                
                // Try to restore transcript from localStorage if session state is empty
                if (!currentTranscript && localStorage.getItem('bengali_transcript')) {{
                    currentTranscript = localStorage.getItem('bengali_transcript');
                    transcriptionOutput.innerHTML = '<div style="padding: 10px;">' + currentTranscript + '</div>';
                    copyBtn.style.display = 'inline-block';
                }}
            </script>
            """
            
            # Display the real-time component
            components.html(realtime_html, height=400)
            
            # Reset clear flag after processing
            if st.session_state.clear_requested:
                st.session_state.clear_requested = False
            
            # Additional controls and features
            st.markdown("---")
            st.markdown("### 📊 Transcription Controls")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Save transcription
                if st.session_state.transcription_text:
                    if st.button("💾 Save Transcription"):
                        timestamp = int(time.time())
                        st.download_button(
                            label="📥 Download Transcription",
                            data=st.session_state.transcription_text,
                            file_name=f"realtime_transcription_{timestamp}.txt",
                            mime="text/plain"
                        )
            
            with col2:
                # Copy to clipboard (visual feedback)
                if st.session_state.transcription_text:
                    if st.button("📋 Copy Text"):
                        st.info("💡 Text is ready - you can manually copy from the display above")
            
            with col3:
                # Text length info
                if st.session_state.transcription_text:
                    word_count = len(st.session_state.transcription_text.split())
                    char_count = len(st.session_state.transcription_text)
                    st.metric("Words", word_count)
                    st.caption(f"{char_count} characters")
            
            # Manual text input area for editing - this will persist the transcription
            st.markdown("### ✏️ View & Edit Transcription")
            
            # Use a unique key for the text area to maintain state
            edited_text = st.text_area(
                "Transcribed text (automatically updated):",
                value=st.session_state.transcription_text,
                height=150,
                key="persistent_transcription",
                help="This shows your transcribed text. You can edit it manually here. Text will persist even after stopping recording."
            )
            
            # Update session state if user manually edits
            if edited_text != st.session_state.transcription_text:
                st.session_state.transcription_text = edited_text
                
            # Instructions
            st.markdown("---")
            st.markdown("### 📋 How to use Real-time Transcription:")
            st.markdown("""
            1. 🔴 Click **Start Live Transcription** to begin
            2. 🎤 Allow microphone permissions when prompted  
            3. 🗣️ Speak clearly in Bengali - transcription will appear in real-time
            4. ⏹️ Click **Stop Transcription** when done
            5. ✏️ Edit the transcription manually if needed
            6. 💾 Save or copy your transcription
            
            **Tips for better results:**
            - Speak clearly and at a moderate pace
            - Use a quiet environment 
            - Ensure good internet connection
            - The system works best with modern Bengali pronunciation
            """)
            
            # Browser compatibility note
            st.info("""
            **Browser Compatibility**: 
            - ✅ **Chrome** (Recommended)
            - ✅ **Microsoft Edge** 
            - ✅ **Safari** (macOS/iOS)
            - ❌ **Firefox** (Limited support)
            
            For best results, use Chrome or Edge browsers.
            """)

    # Tab 4: Voice Complaint
    with tab4:
        st.header("🎤 Bengali Voice Complaint System")
        
        # Initialize session state for recorded files
        if 'recorded_file_path' not in st.session_state:
            st.session_state.recorded_file_path = None
        if 'recording_completed' not in st.session_state:
            st.session_state.recording_completed = False
        if 'temp_recording_blob' not in st.session_state:
            st.session_state.temp_recording_blob = None
        if 'show_customer_form' not in st.session_state:
            st.session_state.show_customer_form = False
        if 'ready_to_create_ticket' not in st.session_state:
            st.session_state.ready_to_create_ticket = False
        if 'uploaded_audio_file' not in st.session_state:
            st.session_state.uploaded_audio_file = None
        
        # Create three options: File Upload, Live Recording, and Voice + Attachment
        upload_tab, record_tab, voice_attachment_tab = st.tabs(["📁 Upload Audio File", "🎙️ Live Recording", "🎤📎 Voice + Attachment"])
        
        # Tab 4.1: File Upload (Primary Method)
        with upload_tab:
            st.subheader("📁 Upload Bengali Audio File")
            st.info("💡 **Recommended Method**: Upload your Bengali audio file directly for faster processing")
            
            # File uploader
            uploaded_file = st.file_uploader(
                "Choose a Bengali audio file",
                type=['wav', 'mp3', 'ogg', 'm4a', 'webm'],
                help="Supported formats: WAV, MP3, OGG, M4A, WEBM",
                key="audio_uploader"
            )
            
            if uploaded_file is not None:
                st.success(f"✅ Audio file uploaded: {uploaded_file.name}")
                st.session_state.uploaded_audio_file = uploaded_file
                
                # Audio player to preview the uploaded file
                st.audio(uploaded_file, format=f"audio/{uploaded_file.type.split('/')[-1]}")
                
                # Show file details
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File Name", uploaded_file.name)
                with col2:
                    st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
                with col3:
                    st.metric("File Type", uploaded_file.type)
                
                st.markdown("---")
                
                # Customer information form
                st.subheader("👤 Customer Information")
                st.info("📝 Please provide customer details to create the ticket:")
                
                with st.form("upload_customer_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        customer_name = st.text_input("Customer Name *", placeholder="Enter customer's full name")
                        customer_email = st.text_input("Email *", placeholder="customer@example.com")
                    
                    with col2:
                        customer_phone = st.text_input("Phone", placeholder="+880XXXXXXXXX")
                        priority = st.selectbox("Priority", ["medium", "low", "high", "urgent"])
                    
                    # Submit button
                    if st.form_submit_button("🚀 **CREATE TICKET FROM UPLOADED FILE**", type="primary", use_container_width=True):
                        if customer_name and customer_email:
                            # Process the uploaded audio and create ticket
                            with st.spinner("🎯 Processing your voice complaint..."):
                                try:
                                    # Save uploaded file temporarily
                                    voices_dir = Path("voices")
                                    voices_dir.mkdir(exist_ok=True)
                                    
                                    timestamp = int(time.time())
                                    file_extension = uploaded_file.name.split(".")[-1] if "." in uploaded_file.name else "wav"
                                    temp_filename = f"uploaded_audio_{timestamp}.{file_extension}"
                                    temp_filepath = voices_dir / temp_filename
                                    
                                    # Write uploaded file to disk
                                    with open(temp_filepath, "wb") as f:
                                        f.write(uploaded_file.getbuffer())
                                    
                                    # Call the process voice complaint API (handles complete pipeline)
                                    with open(temp_filepath, "rb") as audio_file:
                                        files = {"file": (temp_filename, audio_file, "audio/mpeg")}
                                        data = {
                                            "customer_name": customer_name,
                                            "customer_email": customer_email,
                                            "customer_phone": customer_phone or ""
                                        }
                                        
                                        response = requests.post(f"{FASTAPI_BASE_URL}/process/voice-complaint", 
                                                               files=files, data=data, timeout=120)
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        ticket = result["ticket"]
                                        
                                        st.success("🎉 **Ticket Created Successfully!**")
                                        
                                        # Show ticket details
                                        st.markdown("### 📋 Ticket Details")
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.metric("Ticket ID", f"#{ticket['id']}")
                                            st.metric("Status", ticket['status'].upper())
                                            st.metric("Priority", ticket['priority'].upper())
                                        
                                        with col2:
                                            st.metric("Category", ticket['category'].replace('_', ' ').title())
                                            if ticket.get('subcategory'):
                                                st.metric("Subcategory", ticket['subcategory'])
                                            created_date = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00'))
                                            st.metric("Created", created_date.strftime("%Y-%m-%d %H:%M"))
                                        
                                        st.markdown("**Title:**")
                                        st.info(ticket['title'])
                                        
                                        # Display both Bengali and English descriptions side by side
                                        st.markdown("### 📝 Complaint Details")
                                        
                                        # Create tabs for better organization
                                        desc_tab1, desc_tab2 = st.tabs(["🇧🇩 Bengali Original", "🇺🇸 English Analysis"])
                                        
                                        with desc_tab1:
                                            st.markdown("**Original Bengali Complaint:**")
                                            if ticket.get('bengali_description'):
                                                st.text_area("Bengali Description", value=ticket['bengali_description'], height=150, disabled=True, key="bengali_orig_upload", label_visibility="collapsed")
                                            else:
                                                st.info("No Bengali text available")
                                        
                                        with desc_tab2:
                                            st.markdown("**AI-Enhanced English Description:**")
                                            st.text_area("English Description", value=ticket['description'], height=150, disabled=True, key="english_desc_upload", label_visibility="collapsed")
                                        
                                        # Show transcription if available
                                        if result.get('transcription'):
                                            st.markdown("### 🎤 Audio Transcription Details")
                                            transcription_data = result['transcription']
                                            if isinstance(transcription_data, dict):
                                                bengali_text = transcription_data.get('bengali_text', '')
                                                st.text_area("Transcribed Bengali Text", value=bengali_text, height=100, disabled=True, key="transcribed_text_upload")
                                                if transcription_data.get('language_code'):
                                                    st.caption(f"Language: {transcription_data['language_code']} (Confidence: {transcription_data.get('language_probability', 0):.2f})")
                                            else:
                                                st.text_area("Transcribed Text", value=str(transcription_data), height=100, disabled=True, key="transcribed_raw_upload")
                                        
                                        # Clear the session state
                                        st.session_state.uploaded_audio_file = None
                                        st.session_state.ticket_created = True
                                        
                                    else:
                                        st.error(f"❌ Error creating ticket: {response.text}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error processing voice complaint: {str(e)}")
                                finally:
                                    # Clean up temporary file
                                    try:
                                        if temp_filepath.exists():
                                            temp_filepath.unlink()
                                    except:
                                        pass
                        else:
                            st.error("⚠️ Please provide at least customer name and email")
                
                # Option to create another ticket (outside the form)
                if st.session_state.get('ticket_created', False):
                    if st.button("🔄 Create Another Ticket", type="secondary", key="create_another_upload"):
                        st.session_state.uploaded_audio_file = None
                        st.session_state.ticket_created = False
                        st.rerun()
            else:
                st.info("👆 Please upload a Bengali audio file to get started")
        
        # Tab 4.2: Live Recording (Secondary Method)  
        with record_tab:
            st.subheader("🎙️ Record Your Complaint")
            st.warning("⚠️ **Alternative Method**: If the upload method doesn't work, try live recording")
            
            # Recording section (outside form)
            col_record1, col_record2 = st.columns([3, 1])
            
            with col_record1:
                components.html(create_html5_recorder(), height=350)
            
            with col_record2:
                st.write("")  # Add some space
                st.write("")  # Add some space
                if st.button("🔄 Check for New Recording", help="Click after recording to check for saved audio"):
                    # Check for latest recorded file
                    voices_dir = Path("voices")
                    if voices_dir.exists():
                        recorded_files = list(voices_dir.glob("bengali_complaint_*.wav"))
                        if recorded_files:
                            # Get the most recent file
                            latest_file = max(recorded_files, key=os.path.getctime)
                            st.session_state.recorded_file_path = latest_file
                            st.success(f"🎙️ Found recording: {latest_file.name}")
                            st.rerun()
                        else:
                            st.info("No recordings found yet")
                    else:
                        st.info("No recordings found yet")
            
            # Recording Action Buttons - Separate from HTML component
            st.subheader("📝 Recording Actions")

            # Simple recording status check - NO AUTO-UPDATES
            voices_dir = Path("voices")
            recorded_files = []
            latest_file = None

            # Just check what files exist, don't auto-update session state
            if voices_dir.exists():
                recorded_files = list(voices_dir.glob("bengali_complaint_*.wav"))
                if recorded_files:
                    latest_file = max(recorded_files, key=os.path.getctime)

            # Show current session state status
            current_recording = st.session_state.get('recorded_file_path')
            recording_completed = st.session_state.get('recording_completed', False)
            
            if current_recording and Path(current_recording).exists() and recording_completed:
                st.success(f"✅ Active recording: {Path(current_recording).name}")
                st.info("🎫 **Button Status**: CREATE TICKET button is ENABLED!")
            elif recorded_files:
                st.info(f"📁 Found {len(recorded_files)} recording(s) in voices folder.")
                st.warning("🎫 **Button Status**: Use 'Check for New Recording' to activate ticket creation")
            else:
                st.warning("📁 No recordings found. Please record audio first using the recorder above.")
                st.error("🎫 **Button Status**: CREATE TICKET button is DISABLED")

            # Always show action buttons with proper state
            col1, col2, col3 = st.columns([2, 1, 1])

            # Simple button enabling logic
            has_recording = (st.session_state.get('recorded_file_path') is not None and 
                            Path(st.session_state.get('recorded_file_path', '')).exists() and 
                            st.session_state.get('recording_completed', False))

            with col1:
                if has_recording:
                    create_ticket_clicked = st.button("🎫 **CREATE TICKET FROM RECORDING**", 
                                type="primary", 
                                help="✅ Recording ready! Click to process and create support ticket",
                                use_container_width=True,
                                key="create_ticket_btn")
                    
                    if create_ticket_clicked:
                        # Set state immediately and show confirmation
                        st.session_state.show_customer_form = True
                        st.session_state.ready_to_create_ticket = True
                        st.success("🎫 Button clicked! Customer form will appear below.")
                else:
                    st.button("🎫 **CREATE TICKET FROM RECORDING**", 
                             type="secondary", 
                             disabled=True,
                             help="🔴 Record audio first, then this button will be enabled",
                             use_container_width=True,
                             key="create_ticket_btn_disabled")

            with col2:
                if has_recording:
                    # Read the file and provide download
                    try:
                        with open(st.session_state.recorded_file_path, 'rb') as audio_file:
                            audio_bytes = audio_file.read()
                            st.download_button(
                                label="📥 Backup",
                                data=audio_bytes,
                                file_name=st.session_state.recorded_file_path.name,
                                mime="audio/wav",
                                use_container_width=True,
                                help="Download a backup copy",
                                key="download_btn_enabled"
                            )
                    except:
                        st.button("📥 Backup", 
                                 disabled=True,
                                 help="Error reading file",
                                 use_container_width=True,
                                 key="download_btn_error")
                else:
                    st.button("📥 Backup", 
                             disabled=True,
                             help="Record audio first",
                             use_container_width=True,
                             key="download_btn_disabled")

            with col3:
                if has_recording:
                    if st.button("🗑️ Clear", 
                                help="Clear current recording",
                                use_container_width=True,
                                key="clear_btn_enabled"):
                        st.session_state.recorded_file_path = None
                        st.session_state.recording_completed = False
                        st.session_state.show_customer_form = False
                        st.session_state.ready_to_create_ticket = False
                        st.success("🗑️ Recording cleared!")
                else:
                    st.button("🗑️ Clear", 
                             disabled=True,
                             help="No recording to clear",
                             use_container_width=True,
                             key="clear_btn_disabled")

            # Auto-refresh button for immediate detection
            col_refresh1, col_refresh2 = st.columns([1, 1])

            with col_refresh1:
                if st.button("🔄 Check for New Recording", 
                            help="Click after recording to detect new audio immediately",
                            use_container_width=True,
                            key="check_recording_btn"):
                    # Force check for very recent files with expanded time window
                    if voices_dir.exists():
                        all_files = list(voices_dir.glob("bengali_complaint_*.wav"))
                        if all_files:
                            newest_file = max(all_files, key=os.path.getctime)
                            newest_age = datetime.now().timestamp() - newest_file.stat().st_ctime
                            
                            if newest_age < 300:  # 5 minutes window for manual check
                                st.session_state.recorded_file_path = newest_file
                                st.session_state.recording_completed = True
                                st.success(f"🎉 Recording found and activated: {newest_file.name}")
                                st.balloons()  # Celebration animation
                                # Don't rerun immediately - let user see the result
                            else:
                                st.warning(f"⏰ Latest file is {newest_age:.0f} seconds old. Please record a new audio.")
                        else:
                            st.warning("📁 No recordings found in voices folder")
                    else:
                        st.error("📂 Voices folder not found. Please ensure recording is working.")
                        # Try to create voices directory
                        try:
                            voices_dir.mkdir(exist_ok=True)
                            st.info("Created voices directory")
                        except:
                            pass

            with col_refresh2:
                if st.button("🔄 Reset All", 
                            help="Clear all session data and start fresh",
                            use_container_width=True,
                            key="reset_all_btn"):
                    # Clear all session state without rerun
                    st.session_state.recorded_file_path = None
                    st.session_state.recording_completed = False
                    st.session_state.show_customer_form = False
                    st.session_state.ready_to_create_ticket = False
                    st.success("🔄 All data cleared! Start fresh recording.")
            
            # Show customer form if ticket creation was initiated
            if st.session_state.get('show_customer_form', False):
                st.markdown("---")
                st.subheader("👤 Customer Information")
                
                # Check recording status again
                if not has_recording:
                    st.error("⚠️ Recording not found! Please record audio again.")
                    st.session_state.show_customer_form = False
                    st.session_state.ready_to_create_ticket = False
                    st.stop()
                
                st.info("📝 Please provide customer details to create the ticket:")
                
                with st.form("quick_customer_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        customer_name = st.text_input("Customer Name *", placeholder="Enter customer's full name")
                        customer_email = st.text_input("Email *", placeholder="customer@example.com")
                    
                    with col2:
                        customer_phone = st.text_input("Phone", placeholder="+880XXXXXXXXX")
                        priority = st.selectbox("Priority", ["medium", "low", "high", "urgent"])
                    
                    # Submit button
                    if st.form_submit_button("🚀 **CREATE TICKET NOW**", type="primary", use_container_width=True):
                        if customer_name and customer_email:
                            # Process the audio and create ticket
                            with st.spinner("🎯 Processing your voice complaint..."):
                                try:
                                    # Call the process voice complaint API (handles complete pipeline)
                                    with open(st.session_state.recorded_file_path, "rb") as audio_file:
                                        filename = os.path.basename(st.session_state.recorded_file_path)
                                        files = {"file": (filename, audio_file, "audio/mpeg")}
                                        data = {
                                            "customer_name": customer_name,
                                            "customer_email": customer_email,
                                            "customer_phone": customer_phone or ""
                                        }
                                        
                                        response = requests.post(f"{FASTAPI_BASE_URL}/process/voice-complaint", 
                                                               files=files, data=data, timeout=120)
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        ticket = result["ticket"]
                                        
                                        st.success("🎉 **Ticket Created Successfully!**")
                                        
                                        # Show ticket details
                                        st.markdown("### 📋 Ticket Details")
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.metric("Ticket ID", f"#{ticket['id']}")
                                            st.metric("Status", ticket['status'].upper())
                                            st.metric("Priority", ticket['priority'].upper())
                                        
                                        with col2:
                                            st.metric("Category", ticket['category'].replace('_', ' ').title())
                                            if ticket.get('subcategory'):
                                                st.metric("Subcategory", ticket['subcategory'])
                                            created_date = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00'))
                                            st.metric("Created", created_date.strftime("%Y-%m-%d %H:%M"))
                                        
                                        st.markdown("**Title:**")
                                        st.info(ticket['title'])
                                        
                                        # Display both Bengali and English descriptions side by side
                                        st.markdown("### 📝 Complaint Details")
                                        
                                        # Create tabs for better organization
                                        desc_tab1, desc_tab2 = st.tabs(["🇧🇩 Bengali Original", "🇺🇸 English Analysis"])
                                        
                                        with desc_tab1:
                                            st.markdown("**Original Bengali Complaint:**")
                                            if ticket.get('bengali_description'):
                                                st.text_area("Bengali Description", value=ticket['bengali_description'], height=150, disabled=True, key="bengali_orig_record", label_visibility="collapsed")
                                            else:
                                                st.info("No Bengali text available")
                                        
                                        with desc_tab2:
                                            st.markdown("**AI-Enhanced English Description:**")
                                            st.text_area("English Description", value=ticket['description'], height=150, disabled=True, key="english_desc_record", label_visibility="collapsed")
                                        
                                        # Clear the form state
                                        st.session_state.show_customer_form = False
                                        st.session_state.ready_to_create_ticket = False
                                        st.session_state.recorded_file_path = None
                                        st.session_state.recording_completed = False
                                        st.session_state.ticket_created_recording = True
                                        
                                    else:
                                        st.error(f"❌ Error creating ticket: {response.text}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error processing voice complaint: {str(e)}")
                        else:
                            st.error("⚠️ Please provide at least customer name and email")
                
                # Option to create another ticket (outside the form)
                if st.session_state.get('ticket_created_recording', False):
                    if st.button("🔄 Create Another Ticket", type="secondary", key="create_another_recording"):
                        st.session_state.show_customer_form = False
                        st.session_state.ready_to_create_ticket = False
                        st.session_state.recorded_file_path = None
                        st.session_state.recording_completed = False
                        st.session_state.ticket_created_recording = False
                        st.success("🔄 Cleared! You can now record a new complaint.")
                        st.rerun()
        
        # Tab 4.3: Voice + Attachment (Enhanced Method)
        with voice_attachment_tab:
            st.subheader("🎤📎 Voice + Attachment Enhanced Ticketing")
            st.info("🚀 **NEW FEATURE**: Upload voice complaint PLUS attachment (screenshot, document, etc.) for more accurate AI analysis!")
            
            # Initialize session state for voice + attachment feature
            if 'voice_attachment_audio' not in st.session_state:
                st.session_state.voice_attachment_audio = None
            if 'voice_attachment_file' not in st.session_state:
                st.session_state.voice_attachment_file = None
                
            # File Upload Section
            st.markdown("### 📁 Upload Files")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🎤 Bengali Voice File")
                voice_file = st.file_uploader(
                    "Choose Bengali audio file",
                    type=['wav', 'mp3', 'ogg', 'm4a', 'webm'],
                    help="Your Bengali voice complaint",
                    key="voice_attachment_audio_uploader"
                )
                
                if voice_file is not None:
                    st.success(f"✅ Voice: {voice_file.name}")
                    st.audio(voice_file, format=f"audio/{voice_file.type.split('/')[-1]}")
                    st.session_state.voice_attachment_audio = voice_file
                else:
                    st.session_state.voice_attachment_audio = None
            
            with col2:
                st.markdown("#### 📎 Attachment File")
                attachment_file = st.file_uploader(
                    "Choose attachment file",
                    type=['png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'],
                    help="Screenshot, document, or any relevant file",
                    key="voice_attachment_file_uploader"
                )
                
                if attachment_file is not None:
                    st.success(f"✅ Attachment: {attachment_file.name}")
                    
                    # Show preview if it's an image
                    if attachment_file.type.startswith('image/'):
                        st.image(attachment_file, caption="Attachment Preview", use_column_width=True)
                    else:
                        st.info(f"📄 File type: {attachment_file.type}")
                        st.info(f"📊 File size: {attachment_file.size / 1024:.1f} KB")
                    
                    st.session_state.voice_attachment_file = attachment_file
                else:
                    st.session_state.voice_attachment_file = None
            
            # Show status
            voice_uploaded = st.session_state.voice_attachment_audio is not None
            attachment_uploaded = st.session_state.voice_attachment_file is not None
            
            if voice_uploaded and attachment_uploaded:
                st.success("🎉 Both files uploaded! Ready to create enhanced ticket with attachment analysis.")
            elif voice_uploaded:
                st.info("🎤 Voice file uploaded! You can create a ticket now. Attachment is optional for enhanced analysis.")
            else:
                st.warning("⚠️ Please upload a voice file to continue. Attachment is optional.")
            
            # Customer Information Section (show when voice is uploaded)
            if voice_uploaded:
                st.markdown("---")
                st.subheader("👤 Customer Information")
                st.info("📝 Please provide customer details to create the enhanced ticket:")
                
                # Optional attachment description
                attachment_description = st.text_area(
                    "📝 Describe your attachment (optional but recommended)",
                    placeholder="e.g., 'Screenshot of error message', 'Invoice copy', 'System log file'...",
                    height=80,
                    key="attachment_description_input"
                )
                
                with st.form("voice_attachment_customer_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        customer_name = st.text_input("Customer Name *", placeholder="Enter customer's full name")
                        customer_email = st.text_input("Email *", placeholder="customer@example.com")
                    
                    with col2:
                        customer_phone = st.text_input("Phone", placeholder="+880XXXXXXXXX")
                        priority = st.selectbox("Priority", ["medium", "low", "high", "urgent"])
                    
                    # Submit button with dynamic text
                    button_text = "🚀 **CREATE ENHANCED TICKET**" + (" (with attachment)" if attachment_uploaded else " (voice only)")
                    if st.form_submit_button(button_text, type="primary", use_container_width=True):
                        if customer_name and customer_email:
                            # Process voice with optional attachment
                            processing_text = "🤖 Processing voice" + (" + attachment" if attachment_uploaded else "") + " with AI... This may take 30-60 seconds..."
                            with st.spinner(processing_text):
                                try:
                                    # Get file bytes
                                    voice_file_bytes = st.session_state.voice_attachment_audio.getvalue()
                                    attachment_file_bytes = st.session_state.voice_attachment_file.getvalue() if attachment_uploaded else None
                                    
                                    # Process with the enhanced API (attachment is optional)
                                    success, result = process_voice_with_attachment(
                                        voice_file_bytes,
                                        st.session_state.voice_attachment_audio.name,
                                        attachment_file_bytes,
                                        st.session_state.voice_attachment_file.name if attachment_uploaded else None,
                                        customer_name,
                                        customer_email,
                                        customer_phone,
                                        attachment_description if attachment_uploaded else None
                                    )
                                    
                                    if success:
                                        ticket = result["ticket"]
                                        has_attachment = result.get("has_attachment", False)
                                        
                                        success_msg = "🎉 **Enhanced Ticket Created Successfully!**"
                                        if has_attachment:
                                            success_msg += " (with attachment analysis)"
                                        st.success(success_msg)
                                        
                                        # Show enhanced ticket details
                                        st.markdown("### 🎫 Enhanced Ticket Details")
                                        
                                        # Metrics row
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Ticket ID", f"#{ticket['id']}")
                                        with col2:
                                            st.metric("Priority", ticket['priority'].upper())
                                        with col3:
                                            st.metric("Category", ticket['category'].replace('_', ' ').title())
                                        
                                        st.markdown("**Enhanced Title:**")
                                        st.info(ticket['title'])
                                        
                                        # Enhanced Analysis Tabs
                                        analysis_tab1, analysis_tab2, analysis_tab3, analysis_tab4 = st.tabs([
                                            "🎤 Voice Analysis", 
                                            "📎 Attachment Analysis", 
                                            "🔗 Combined Analysis",
                                            "🔧 Technical Assessment"
                                        ])
                                        
                                        with analysis_tab1:
                                            st.markdown("#### 🎤 Voice Transcription & Analysis")
                                            if result.get('bengali_text'):
                                                st.text_area("Bengali Voice Text", 
                                                            value=result['bengali_text'], 
                                                            height=100, disabled=True, 
                                                            key="enhanced_bengali_text")
                                            if result.get('english_translation'):
                                                st.text_area("English Translation", 
                                                            value=result['english_translation'], 
                                                            height=100, disabled=True,
                                                            key="enhanced_english_translation")
                                        
                                        with analysis_tab2:
                                            st.markdown("#### 📎 Attachment Analysis")
                                            attachment_analysis = result.get('attachment_analysis', {})
                                            
                                            if attachment_analysis:
                                                st.info(f"**Type:** {attachment_analysis.get('type', 'Unknown')}")
                                                st.text_area("Content Description", 
                                                            value=attachment_analysis.get('content_description', 'No description'), 
                                                            height=80, disabled=True,
                                                            key="attachment_content_desc")
                                                
                                                if attachment_analysis.get('extracted_text'):
                                                    st.text_area("Extracted Text", 
                                                                value=attachment_analysis['extracted_text'], 
                                                                height=80, disabled=True,
                                                                key="attachment_extracted_text")
                                                
                                                if attachment_analysis.get('key_visual_elements'):
                                                    st.write("**Key Visual Elements:**")
                                                    for element in attachment_analysis['key_visual_elements']:
                                                        st.write(f"• {element}")
                                        
                                        with analysis_tab3:
                                            st.markdown("#### 🔗 Voice-Attachment Correlation")
                                            correlation = result.get('voice_image_correlation', {})
                                            
                                            if correlation:
                                                st.text_area("Relationship Analysis", 
                                                            value=correlation.get('relationship', 'No analysis'), 
                                                            height=80, disabled=True,
                                                            key="correlation_relationship")
                                                st.text_area("Consistency Check", 
                                                            value=correlation.get('consistency', 'No analysis'), 
                                                            height=60, disabled=True,
                                                            key="correlation_consistency")
                                                st.text_area("Additional Context", 
                                                            value=correlation.get('additional_context', 'No analysis'), 
                                                            height=80, disabled=True,
                                                            key="correlation_context")
                                        
                                        with analysis_tab4:
                                            st.markdown("#### 🔧 Technical Assessment")
                                            tech_assessment = result.get('technical_assessment', {})
                                            
                                            if tech_assessment:
                                                is_technical = tech_assessment.get('is_technical_issue', False)
                                                st.info(f"**Technical Issue:** {'Yes' if is_technical else 'No'}")
                                                
                                                if tech_assessment.get('error_codes'):
                                                    st.write("**Error Codes Found:**")
                                                    for code in tech_assessment['error_codes']:
                                                        st.write(f"• {code}")
                                                
                                                if tech_assessment.get('system_state'):
                                                    st.text_area("System State", 
                                                                value=tech_assessment['system_state'], 
                                                                height=60, disabled=True,
                                                                key="tech_system_state")
                                                
                                                if tech_assessment.get('troubleshooting_steps'):
                                                    st.write("**Recommended Steps:**")
                                                    for i, step in enumerate(tech_assessment['troubleshooting_steps'], 1):
                                                        st.write(f"{i}. {step}")
                                        
                                        # Final enhanced description
                                        st.markdown("### 📋 Final Ticket Description")
                                        st.text_area("Final Description", value=ticket['description'], height=150, disabled=True, key="enhanced_final_desc", label_visibility="collapsed")
                                        
                                        # Clear session state
                                        st.session_state.voice_attachment_audio = None
                                        st.session_state.voice_attachment_file = None
                                        
                                        # Store ticket info in session state for RAG search
                                        st.session_state.current_ticket = ticket
                                        st.session_state.show_rag_section = True
                                        
                                    else:
                                        st.error(f"❌ Error creating enhanced ticket: {result}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error processing voice + attachment: {str(e)}")
                                    st.write("**Debug Info:**", str(e))
                        else:
                            st.error("⚠️ Please provide at least customer name and email")
            
            # RAG Search Section (Outside the form to avoid button conflicts)
            if st.session_state.get('show_rag_section', False) and st.session_state.get('current_ticket'):
                ticket = st.session_state.current_ticket
                
                st.markdown("---")
                st.markdown("### 🔍 Find Similar Previous Tickets (RAG Search)")
                st.info("🤖 **NEW**: Search our knowledge base of 29K+ customer support tickets to find similar issues and their resolutions!")
                
                # Initialize RAG search section
                if 'show_rag_search' not in st.session_state:
                    st.session_state.show_rag_search = False
                
                # Check RAG database status using ChromaDB RAG service directly
                try:
                    # Use session state to cache ChromaDB RAG service and avoid repeated initialization
                    if 'rag_service' not in st.session_state:
                        from bangla_vai.services.rag_service import get_rag_service
                        st.session_state.rag_service = get_rag_service()
                    
                    rag_service = st.session_state.rag_service
                    test_results = rag_service.search_similar_tickets("test", 1)
                    rag_db_ready = len(test_results) > 0 or rag_service.get_database_stats().get('total_tickets', 0) > 0
                except Exception as e:
                    logger.error(f"ChromaDB RAG service error: {e}")
                    rag_db_ready = False
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button("🔍 **Search Similar Tickets**", type="secondary", use_container_width=True, key="rag_search_btn"):
                        if rag_db_ready:
                            st.session_state.show_rag_search = True
                        else:
                            st.error("❌ RAG database not initialized. Please run: python scripts/initialize_rag_db.py")
                with col2:
                    if rag_db_ready:
                        st.success("✅ RAG DB Ready")
                    else:
                        st.error("❌ RAG DB Not Ready")
                        st.info("💡 Try running: `python scripts/initialize_rag_db.py` to initialize the ChromaDB database")
                
                # Show RAG search interface
                if st.session_state.show_rag_search:
                    with st.form("rag_search_form"):
                        st.markdown("#### 🔍 Search Query")
                        
                        # Default search query based on current ticket
                        default_query = ticket.get('title', '') + ' ' + ticket.get('description', '')[:100]
                        
                        search_query = st.text_area(
                            "Enter your search query (problem description, keywords, etc.)",
                            value=default_query,
                            height=80,
                            help="Describe the problem or use keywords to find similar tickets"
                        )
                        
                        max_results = st.slider("Maximum results", min_value=3, max_value=10, value=5)
                        
                        if st.form_submit_button("🔍 **SEARCH**", type="primary"):
                            if search_query.strip():
                                with st.spinner("🤖 Searching for similar tickets..."):
                                    try:
                                        # Use cached ChromaDB RAG service from session state
                                        rag_service = st.session_state.get('rag_service')
                                        if not rag_service:
                                            from bangla_vai.services.rag_service import get_rag_service
                                            rag_service = get_rag_service()
                                            st.session_state.rag_service = rag_service
                                        
                                        search_results = rag_service.search_similar_tickets(search_query, max_results)
                                        
                                        if search_results:
                                            st.markdown("#### 📊 Similar Tickets Found")
                                            
                                            for i, similar_ticket in enumerate(search_results, 1):
                                                with st.expander(f"#{i} - Ticket {similar_ticket['ticket_id']} (Similarity: {similar_ticket['similarity_score']:.1%})"):
                                                    col1, col2 = st.columns([2, 1])
                                                    
                                                    with col1:
                                                        st.markdown(f"**Subject:** {similar_ticket['subject']}")
                                                        st.markdown(f"**Description:** {similar_ticket['description']}")
                                                        if similar_ticket['resolution']:
                                                            st.markdown(f"**Resolution:** {similar_ticket['resolution']}")
                                                    
                                                    with col2:
                                                        st.metric("Similarity", f"{similar_ticket['similarity_score']:.1%}")
                                                        st.info(f"**Type:** {similar_ticket['ticket_type']}")
                                                        st.info(f"**Product:** {similar_ticket['product']}")
                                                        st.info(f"**Status:** {similar_ticket['status']}")
                                                        st.info(f"**Priority:** {similar_ticket['priority']}")
                                                        # Fix: Check if customer_satisfaction is valid and not 'unknown'
                                                        satisfaction = similar_ticket.get('customer_satisfaction', '')
                                                        if satisfaction and satisfaction != 'unknown' and satisfaction.strip():
                                                            st.metric("Satisfaction", satisfaction)
                                        else:
                                            st.warning("No similar tickets found. Try adjusting your search query.")
                                            
                                    except Exception as e:
                                        st.error(f"❌ Error searching tickets: {str(e)}")
                                        st.info("💡 Try running: `python scripts/initialize_rag_db.py` to initialize the ChromaDB database")
                            else:
                                st.warning("Please enter a search query")
            
            # Instructions
            st.markdown("---")
            st.markdown("### 📋 How to use Enhanced Voice Ticketing:")
            st.markdown("""
            1. 📁 Upload your Bengali audio file (complaint) - **Required**
            2. 📎 Upload an attachment (screenshot, document, etc.) - **Optional**
            3. 📝 Describe the attachment (optional but recommended if you upload one)
            4. 👤 Fill in customer information
            5. 🚀 Click "CREATE ENHANCED TICKET"
            6. ⏳ Wait 30-60 seconds for AI analysis
            7. 📊 Review the comprehensive analysis
            8. 🔍 Use RAG search to find similar previous tickets and solutions
            
            **NEW Features:**
            - ✅ **Attachment is now optional** - create tickets with voice only
            - 🤖 **RAG Search** - find similar tickets from 29K+ knowledge base
            - 🔄 **Smart correlation** - attachment analysis when provided
            
            **Supported attachment types:**
            - 🖼️ Images: PNG, JPG, JPEG, GIF
            - 📄 Documents: PDF, DOC, DOCX, TXT
            """)

    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Note:** This application uses FastAPI endpoints for Bengali voice recording, text-to-speech conversion, and speech recognition. "
        "The Real-time STT feature uses your browser's built-in speech recognition with Bengali language support. "
        "Make sure the FastAPI server is running and ElevenLabs API key is configured for file-based speech-to-text features."
    )

if __name__ == "__main__":
    main() 