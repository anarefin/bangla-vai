import streamlit as st
import os
import tempfile
from bengali_stt import BengaliSTT, BengaliTTS
from dotenv import load_dotenv
import base64
from io import BytesIO
import time
import numpy as np
import streamlit.components.v1 as components
import re

# Load environment variables
load_dotenv()

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
    st.markdown("### Powered by ElevenLabs Scribe API & Google TTS")
    
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
            os.environ["ELEVENLABS_API_KEY"] = api_key
            st.success("✓ API Key configured")
        else:
            st.warning("⚠️ Please enter your API key for speech-to-text features")
    
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
                    # Create voices directory if it doesn't exist
                    voices_dir = "voices"
                    if not os.path.exists(voices_dir):
                        os.makedirs(voices_dir)
                    
                    # Generate timestamp for unique filename
                    timestamp = int(time.time())
                    file_extension = uploaded_file.name.split(".")[-1]
                    filename = f"uploaded_audio_{timestamp}.{file_extension}"
                    file_path = os.path.join(voices_dir, filename)
                    
                    # Save uploaded file to voices directory
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.read())
                    
                    st.info(f"📁 File saved to: {file_path}")
                    
                    # Initialize STT client
                    stt = BengaliSTT()
                    
                    # Show progress
                    with st.spinner("Transcribing audio... This may take a few moments."):
                        result = stt.transcribe_audio_file(file_path)
                    
                    # Note: File is kept in voices directory (not deleted)
                    
                    if result:
                        st.success("✅ Transcription completed!")
                        
                        # Extract transcription text
                        if 'text' in result:
                            transcription_text = result['text']
                        elif 'transcription' in result:
                            transcription_text = result['transcription']
                        else:
                            transcription_text = str(result)
                        
                        # Display language detection information
                        detected_lang = result.get('language_code', 'unknown')
                        lang_probability = result.get('language_probability', 0)
                        
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
                    else:
                        st.error("❌ Transcription failed. Please try again.")
                        
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
        7. 📤 Upload the downloaded file in the "Upload Audio" tab for transcription
        """)

    # Tab 2: Text to Speech
    with tab2:
        st.header("📝 Bengali Text to Speech")
        st.markdown("Enter Bengali text and convert it to speech.")
        
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
                        # Initialize TTS client
                        tts = BengaliTTS()
                        
                        with st.spinner("Converting text to speech..."):
                            # Generate speech
                            timestamp = int(time.time())
                            output_filename = f"bengali_speech_{timestamp}.mp3"
                            audio_path = tts.text_to_speech(bengali_text, output_filename, slow=slow_speech)
                        
                        if audio_path and os.path.exists(audio_path):
                            st.success("✅ Speech generated successfully!")
                            
                            # Play audio
                            with open(audio_path, "rb") as audio_file:
                                audio_bytes = audio_file.read()
                                st.audio(audio_bytes, format='audio/mp3')
                            
                            # Download button
                            st.download_button(
                                label="📥 Download Speech Audio",
                                data=audio_bytes,
                                file_name=output_filename,
                                mime="audio/mp3"
                            )
                            
                            # Also provide text download
                            st.download_button(
                                label="📄 Download Text File",
                                data=bengali_text,
                                file_name=f"bengali_text_{timestamp}.txt",
                                mime="text/plain"
                            )
                        else:
                            st.error("❌ Speech generation failed. Please try again.")
                            
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
    

    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Note:** This application supports Bengali voice recording, text-to-speech conversion, and speech recognition. "
        "ElevenLabs API key is required only for speech-to-text features."
    )

if __name__ == "__main__":
    main() 