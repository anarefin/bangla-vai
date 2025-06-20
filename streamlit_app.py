import streamlit as st
import os
import tempfile
from bengali_stt import BengaliSTT, BengaliTTS
from dotenv import load_dotenv
import base64
from io import BytesIO
import time
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import threading
import queue
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()

# Global variables for audio recording
audio_frames = []
audio_lock = threading.Lock()

def audio_frame_callback(frame: av.AudioFrame) -> av.AudioFrame:
    """Callback function to capture audio frames"""
    global audio_frames, audio_lock
    
    try:
        # Convert frame to numpy array
        audio_array = frame.to_ndarray()
        
        # Debug: Print frame info (remove after testing)
        print(f"Audio frame received: shape={audio_array.shape}, dtype={audio_array.dtype}")
        
        with audio_lock:
            audio_frames.append(audio_array)
        
        # Also store in session state for immediate access
        if 'temp_audio_frames' not in st.session_state:
            st.session_state.temp_audio_frames = []
        st.session_state.temp_audio_frames.append(audio_array)
        
    except Exception as e:
        print(f"Error in audio callback: {e}")
    
    return frame

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
        page_title="Bengali Voice & Text Converter",
        page_icon="🎤",
        layout="wide"
    )
    
    st.title("🎤 Bengali Voice & Text Converter")
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
    tab1, tab2, tab3, tab4 = st.tabs(["🎙️ Simple Recorder", "🎙️ WebRTC Recorder", "📝 Text to Speech", "📁 Upload Audio"])
    
    # Tab 1: Simple HTML5 Recorder
    with tab1:
        st.header("🎙️ Simple Voice Recorder")
        st.markdown("**✅ Recommended**: Use this simpler recorder - it works better with browser permissions!")
        
        # HTML5 Audio Recorder
        components.html(create_html5_recorder(), height=350)
        
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
        
        st.info("💡 **Tip**: This recorder works on both HTTP and HTTPS, and doesn't require special WebRTC setup!")
        
        # Upload area for transcription
        st.markdown("### 📤 Upload Your Recording for Transcription")
        uploaded_file = st.file_uploader(
            "Upload the audio file you just downloaded:",
            type=['wav', 'mp3', 'ogg', 'm4a', 'webm'],
            help="Upload the audio file you downloaded from the recorder above"
        )
        
        if uploaded_file and api_key:
            if st.button("🎯 Transcribe Uploaded Recording", type="primary"):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{uploaded_file.name.split(".")[-1]}') as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_file_path = tmp_file.name
                    
                    # Initialize STT client
                    stt = BengaliSTT()
                    
                    # Show progress
                    with st.spinner("Transcribing audio... This may take a few moments."):
                        result = stt.transcribe_audio_file(tmp_file_path)
                    
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
                    
                    if result:
                        st.success("✅ Transcription completed!")
                        
                        # Extract transcription text
                        if 'text' in result:
                            transcription_text = result['text']
                        elif 'transcription' in result:
                            transcription_text = result['transcription']
                        else:
                            transcription_text = str(result)
                        
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

    # Tab 2: Advanced WebRTC Recorder  
    with tab2:
        st.header("🎙️ Record Your Voice")
        st.markdown("Record your voice directly from the browser and save it as a file.")
        
        # Initialize session state
        if 'recording_complete' not in st.session_state:
            st.session_state.recording_complete = False
        if 'recorded_audio' not in st.session_state:
            st.session_state.recorded_audio = None
        
        # WebRTC configuration
        rtc_configuration = RTCConfiguration({
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        })
        
        # Microphone permission notice
        st.info("🎤 **Important**: Please allow microphone permissions when prompted by your browser!")
        
        # Audio recorder using streamlit-webrtc
        webrtc_ctx = webrtc_streamer(
            key="speech-to-text",
            mode=WebRtcMode.SENDONLY,
            audio_frame_callback=audio_frame_callback,
            rtc_configuration=rtc_configuration,
            media_stream_constraints={
                "video": False, 
                "audio": {
                    "echoCancellation": True,
                    "noiseSuppression": True,
                    "autoGainControl": True,
                    "channelCount": 1,
                    "sampleRate": 16000
                }
            },
            async_processing=True,
        )
        
        # Instructions
        st.info("🎤 Click 'START' to begin recording, then 'STOP' when finished.")
        
        # Process recorded audio when recording stops
        if webrtc_ctx.state.playing:
            st.write("🔴 Recording in progress...")
            # Clear previous audio frames when starting new recording
            with audio_lock:
                audio_frames.clear()
            # Reset session state when starting new recording
            st.session_state.recording_complete = False
            st.session_state.recorded_audio = None
            st.session_state.temp_audio_frames = []
        elif not webrtc_ctx.state.playing:
            # Check both global audio_frames and session state temp_audio_frames
            total_frames = len(audio_frames) + len(st.session_state.get('temp_audio_frames', []))
            
            if total_frames > 0:
                # Recording has stopped and we have audio data
                st.success("✅ Recording completed!")
                
                # Process audio frames from both sources
                all_frames = []
                
                # Add global frames
                with audio_lock:
                    all_frames.extend(audio_frames)
                
                # Add session state frames
                if 'temp_audio_frames' in st.session_state:
                    all_frames.extend(st.session_state.temp_audio_frames)
                
                if all_frames:
                    try:
                        # Combine all audio frames
                        audio_data = np.concatenate(all_frames, axis=0)
                        
                        # Convert to bytes (simple WAV format)
                        # This is a simplified approach - in production you'd want proper WAV formatting
                        audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
                        
                        st.session_state.recorded_audio = audio_bytes
                        st.session_state.recording_complete = True
                        
                        st.info(f"📊 Audio data captured: {len(audio_bytes)} bytes from {len(all_frames)} frames")
                    except Exception as e:
                        st.error(f"Error processing audio: {str(e)}")
                        st.session_state.recording_complete = False
                        st.session_state.recorded_audio = None
            elif hasattr(webrtc_ctx, 'state') and hasattr(webrtc_ctx.state, 'signalling') and not webrtc_ctx.state.signalling:
                # Recording stopped but no frames captured
                st.warning("⚠️ Recording stopped but no audio was captured. Please check:")
                st.markdown("""
                - 🎤 **Microphone permissions**: Allow microphone access in your browser
                - 🔊 **Audio input**: Check your microphone is working
                - 🌐 **HTTPS**: This app works best on HTTPS
                - 🔄 **Refresh**: Try refreshing the page and recording again
                """)
                
                # Add a button to reset and try again
                if st.button("🔄 Reset and Try Again"):
                    st.session_state.clear()
                    st.rerun()
        
        # Debug information (remove after testing)
        if not webrtc_ctx.state.playing:
            with st.expander("🔍 Debug Information"):
                st.write(f"Global audio frames: {len(audio_frames)}")
                st.write(f"Session temp frames: {len(st.session_state.get('temp_audio_frames', []))}")
                st.write(f"Total frames: {len(audio_frames) + len(st.session_state.get('temp_audio_frames', []))}")
                st.write(f"Recording complete: {st.session_state.get('recording_complete', False)}")
                st.write(f"Has recorded audio: {st.session_state.get('recorded_audio') is not None}")
                st.write(f"WebRTC state: {webrtc_ctx.state}")
                st.write(f"Microphone permissions: Check browser settings")
                st.write(f"Session state keys: {list(st.session_state.keys())}")
        
        # Alternative: Show save button when recording stops (even if audio processing fails)
        total_frames = len(audio_frames) + len(st.session_state.get('temp_audio_frames', []))
        if not webrtc_ctx.state.playing and total_frames > 0 and not st.session_state.get('recording_complete', False):
            st.warning("⚠️ Audio processing may have failed, but you can still try to save the recording manually.")
            if st.button("💾 Try Save Recording Anyway", key="manual_save_recording"):
                try:
                    # Collect all frames
                    all_frames = []
                    with audio_lock:
                        all_frames.extend(audio_frames)
                    if 'temp_audio_frames' in st.session_state:
                        all_frames.extend(st.session_state.temp_audio_frames)
                    
                    if all_frames:
                        # Try to process audio frames manually
                        audio_data = np.concatenate(all_frames, axis=0)
                        audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
                        
                        timestamp = int(time.time())
                        filename = f"recorded_audio_{timestamp}.wav"
                        
                        import wave
                        with wave.open(filename, 'wb') as wav_file:
                            wav_file.setnchannels(1)  # Mono
                            wav_file.setsampwidth(2)  # 16-bit
                            wav_file.setframerate(16000)  # 16kHz
                            wav_file.writeframes(audio_bytes)
                        
                        st.success(f"🎉 Recording saved as '{filename}' ({len(all_frames)} frames)")
                        
                        # Provide download link
                        with open(filename, "rb") as file:
                            st.download_button(
                                label="📥 Download Recording",
                                data=file.read(),
                                file_name=filename,
                                mime="audio/wav",
                                key="manual_download"
                            )
                        
                        # Update session state
                        st.session_state.recorded_audio = audio_bytes
                        st.session_state.recording_complete = True
                    else:
                        st.error("No audio frames found to save")
                        
                except Exception as e:
                    st.error(f"Failed to save recording: {str(e)}")
        
        # Show controls and options if recording is complete
        if st.session_state.recording_complete and st.session_state.recorded_audio:
            col1, col2 = st.columns(2)
            
            with col1:
                # Save recording button
                if st.button("💾 Save Recording", key="save_recording"):
                    timestamp = int(time.time())
                    filename = f"recorded_audio_{timestamp}.wav"
                    
                    # Create a simple WAV file
                    import wave
                    with wave.open(filename, 'wb') as wav_file:
                        wav_file.setnchannels(1)  # Mono
                        wav_file.setsampwidth(2)  # 16-bit
                        wav_file.setframerate(16000)  # 16kHz
                        wav_file.writeframes(st.session_state.recorded_audio)
                    
                    st.success(f"🎉 Recording saved as '{filename}'")
                    
                    # Provide download link
                    with open(filename, "rb") as file:
                        st.download_button(
                            label="📥 Download Recording",
                            data=file.read(),
                            file_name=filename,
                            mime="audio/wav"
                        )
            
            with col2:
                # Transcribe recording button
                if st.button("🎯 Transcribe Recording", key="transcribe_recording") and api_key:
                    try:
                        # Initialize STT client
                        stt = BengaliSTT()
                        
                        # Create temporary WAV file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            import wave
                            with wave.open(tmp_file.name, 'wb') as wav_file:
                                wav_file.setnchannels(1)  # Mono
                                wav_file.setsampwidth(2)  # 16-bit
                                wav_file.setframerate(16000)  # 16kHz
                                wav_file.writeframes(st.session_state.recorded_audio)
                            tmp_file_path = tmp_file.name
                        
                        # Show progress
                        with st.spinner("Transcribing recording... This may take a few moments."):
                            result = stt.transcribe_audio_file(tmp_file_path)
                        
                        # Clean up temporary file
                        os.unlink(tmp_file_path)
                        
                        if result:
                            st.success("✅ Transcription completed!")
                            
                            # Extract transcription text
                            if 'text' in result:
                                transcription_text = result['text']
                            elif 'transcription' in result:
                                transcription_text = result['transcription']
                            else:
                                transcription_text = str(result)
                            
                            # Display transcription
                            st.subheader("📝 Transcription Result")
                            st.text_area(
                                "Bengali Text:",
                                value=transcription_text,
                                height=100,
                                key="recording_transcription"
                            )
                            
                            # Download transcription
                            st.download_button(
                                label="📥 Download Transcription",
                                data=transcription_text,
                                file_name=f"transcription_recording_{int(time.time())}.txt",
                                mime="text/plain"
                            )
                        else:
                            st.error("❌ Transcription failed. Please try again.")
                            
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                
                elif not api_key:
                    st.warning("⚠️ Please configure your ElevenLabs API key to transcribe recordings.")
            
            # Reset button
            if st.button("🔄 Record Again"):
                st.session_state.recording_complete = False
                st.session_state.recorded_audio = None
                with audio_lock:
                    audio_frames.clear()
                st.rerun()
    
    # Tab 3: Text to Speech
    with tab3:
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
    
    # Tab 4: Upload Audio (existing functionality)
    with tab4:
        st.header("📁 Upload Bengali Audio File")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['mp3', 'wav', 'm4a', 'ogg', 'flac'],
            help="Upload a Bengali audio file for transcription"
        )
        
        if uploaded_file is not None and api_key:
            st.success(f"✓ File uploaded: {uploaded_file.name}")
            
            # Display file details
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**File Name:** {uploaded_file.name}")
            with col2:
                st.info(f"**File Size:** {uploaded_file.size / 1024:.1f} KB")
            
            # Play uploaded audio
            st.audio(uploaded_file.getvalue(), format=f'audio/{uploaded_file.name.split(".")[-1]}')
            
            # Transcribe button
            if st.button("🎯 Transcribe Audio", type="primary"):
                try:
                    # Initialize STT client
                    stt = BengaliSTT()
                    
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # Show progress
                    with st.spinner("Transcribing audio... This may take a few moments."):
                        result = stt.transcribe_audio_file(tmp_file_path)
                    
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
                    
                    if result:
                        st.success("✅ Transcription completed!")
                        
                        # Display transcription
                        st.header("📝 Transcription Result")
                        
                        # Extract transcription text
                        if 'text' in result:
                            transcription_text = result['text']
                        elif 'transcription' in result:
                            transcription_text = result['transcription']
                        else:
                            transcription_text = str(result)
                        
                        # Display in a text area for easy copying
                        st.text_area(
                            "Bengali Text:",
                            value=transcription_text,
                            height=200,
                            help="Click to select and copy the transcribed text"
                        )
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Transcription",
                            data=transcription_text,
                            file_name=f"transcription_{uploaded_file.name}.txt",
                            mime="text/plain"
                        )
                        
                        # Display additional info if available
                        if isinstance(result, dict) and len(result) > 1:
                            with st.expander("📊 Additional Information"):
                                st.json(result)
                    
                    else:
                        st.error("❌ Transcription failed. Please check your audio file and try again.")
                        
                except ValueError as e:
                    st.error(f"Configuration Error: {e}")
                    st.info("Please ensure your ElevenLabs API key is correctly configured.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        
        elif uploaded_file is not None and not api_key:
            st.warning("⚠️ Please configure your ElevenLabs API key in the sidebar to proceed.")
    
    # Instructions
    with st.expander("📖 How to Use"):
        st.markdown("""
        ### Features Available:
        
        #### 🎙️ Record Voice
        - Click 'START' to begin recording your voice
        - Speak clearly in Bengali
        - Click 'STOP' when finished
        - Save the recording as a WAV file
        - Optionally transcribe the recording to text
        
        #### 📝 Text to Speech
        - Enter Bengali text in the text area
        - Choose normal or slow speech speed
        - Generate and download MP3 audio file
        - Also save the text as a TXT file
        
        #### 📁 Upload Audio
        - Upload existing audio files (MP3, WAV, M4A, OGG, FLAC)
        - Transcribe to Bengali text using ElevenLabs API
        - Download transcription results
        
        ### Setup Instructions:
        
        1. **Get ElevenLabs API Key** (for speech-to-text):
           - Sign up at [ElevenLabs](https://elevenlabs.io/)
           - Go to your profile and copy your API key
           - Enter it in the sidebar configuration
        
        2. **Text-to-Speech** works without API key using Google TTS
        
        3. **Voice Recording** works directly in your browser using WebRTC
        
        ### Tips for Better Results:
        - Use clear audio with minimal background noise
        - Speak clearly and at a moderate pace
        - Ensure good microphone quality for recordings
        - Use proper Bengali spelling for text-to-speech
        - Allow microphone access when prompted by your browser
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Note:** This application supports Bengali voice recording, text-to-speech conversion, and speech recognition. "
        "ElevenLabs API key is required only for speech-to-text features."
    )

if __name__ == "__main__":
    main() 