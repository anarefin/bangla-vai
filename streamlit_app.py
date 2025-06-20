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
    tab1, tab2, tab3 = st.tabs(["🎙️ Voice Recorder", "📝 Text to Speech", "🔴 Real-time STT"])
    
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

    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Note:** This application uses FastAPI endpoints for Bengali voice recording, text-to-speech conversion, and speech recognition. "
        "The Real-time STT feature uses your browser's built-in speech recognition with Bengali language support. "
        "Make sure the FastAPI server is running and ElevenLabs API key is configured for file-based speech-to-text features."
    )

if __name__ == "__main__":
    main() 