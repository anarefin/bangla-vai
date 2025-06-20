import streamlit as st
import os
import tempfile
import requests
from dotenv import load_dotenv
import base64
from io import BytesIO
import time
import numpy as np
import streamlit.components.v1 as components
import re
import json

# Load environment variables
load_dotenv()

# FastAPI base URL - adjust this based on your setup
FASTAPI_BASE_URL = "http://localhost:8000"

def check_fastapi_connection():
    """Check if FastAPI server is running"""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

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
    tab1, tab2 = st.tabs(["🎙️ Voice Recorder", "📝 Text to Speech"])
    
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
    

    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Note:** This application uses FastAPI endpoints for Bengali voice recording, text-to-speech conversion, and speech recognition. "
        "Make sure the FastAPI server is running and ElevenLabs API key is configured for speech-to-text features."
    )

if __name__ == "__main__":
    main() 