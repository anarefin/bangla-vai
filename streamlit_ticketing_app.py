import streamlit as st
import os
import requests
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import streamlit.components.v1 as components
from dotenv import load_dotenv
import glob
from pathlib import Path
import time

# Load environment variables
load_dotenv()

# FastAPI base URL
FASTAPI_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Bangla Vai - Voice Ticketing System",
    page_icon="🎫",
    layout="wide"
)

def check_fastapi_connection():
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

def create_html5_recorder():
    return """
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; min-height: 300px; margin: 10px 0;">
        <h2 style="margin: 0 0 20px 0;">🎤 Bengali Voice Recorder</h2>
        <div id="status" style="margin: 20px 0; font-size: 18px; font-weight: bold; min-height: 40px; background: rgba(255,255,255,0.1); border-radius: 10px; padding: 10px;">Ready to record your complaint in Bengali</div>
        
        <!-- Recording Controls -->
        <div style="margin: 30px 0;">
            <button onclick="startRecording()" id="recordBtn" 
                style="background: #ff4757; color: white; border: none; padding: 20px 40px; border-radius: 30px; font-size: 18px; font-weight: bold; cursor: pointer; margin: 10px; min-width: 250px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: all 0.3s;">
                🔴 START RECORDING
            </button>
            <br>
            <button onclick="stopRecording()" id="stopBtn" 
                style="background: #2ed573; color: white; border: none; padding: 20px 40px; border-radius: 30px; font-size: 18px; font-weight: bold; cursor: pointer; margin: 10px; display: none; min-width: 250px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: all 0.3s;">
                ⏹️ STOP RECORDING
            </button>
        </div>
        
        <!-- Audio Playback -->
        <div style="margin: 30px 0;">
            <audio id="audioPlayback" controls style="display: none; margin: 15px; width: 350px; border-radius: 10px;"></audio>
        </div>
        
        <!-- Instructions -->
        <div style="margin: 20px 0; font-size: 14px; color: rgba(255,255,255,0.8);">
            After recording, use the buttons below this recorder to save and process your complaint.
        </div>
    </div>

    <style>
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important;
        }
        
        #recordBtn:hover {
            background: #ff3742 !important;
        }
        
        #stopBtn:hover {
            background: #27d764 !important;
        }
    </style>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let recordedBlob;

        function updateStatus(message) {
            document.getElementById('status').innerHTML = message;
            console.log('Status updated:', message);
        }

        function showElement(id) {
            const element = document.getElementById(id);
            element.style.display = 'inline-block';
            console.log('Showing element:', id);
        }

        function hideElement(id) {
            const element = document.getElementById(id);
            element.style.display = 'none';
            console.log('Hiding element:', id);
        }

        async function startRecording() {
            try {
                updateStatus('🎤 Requesting microphone access...');
                
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });
                
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = function(event) {
                    audioChunks.push(event.data);
                    console.log('Audio data chunk received');
                };
                
                mediaRecorder.onstop = function() {
                    console.log('Recording stopped, processing audio...');
                    
                    // Create audio blob
                    recordedBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    console.log('Audio blob created, size:', recordedBlob.size);
                    
                    // Create audio URL and show player
                    const audioUrl = URL.createObjectURL(recordedBlob);
                    const audioElement = document.getElementById('audioPlayback');
                    audioElement.src = audioUrl;
                    audioElement.style.display = 'block';
                    
                    // Update interface
                    showElement('recordBtn');
                    hideElement('stopBtn');
                    updateStatus('✅ Recording completed! Saving to voices folder...');
                    
                    // Auto-save the recording
                    saveRecordingToVoices();
                    
                    // Stop media tracks
                    stream.getTracks().forEach(track => track.stop());
                    console.log('Recording complete and saved');
                    
                    // Notify user about next steps
                    setTimeout(() => {
                        updateStatus('🎫 Recording ready! Use "CREATE TICKET FROM RECORDING" button below.');
                    }, 2000);
                };
                
                mediaRecorder.onerror = function(error) {
                    console.error('MediaRecorder error:', error);
                    updateStatus('❌ Recording error: ' + error.message);
                };
                
                // Start recording
                mediaRecorder.start();
                console.log('Recording started');
                
                // Update interface
                hideElement('recordBtn');
                showElement('stopBtn');
                updateStatus('🔴 Recording in progress... Speak your complaint in Bengali clearly.');
                
            } catch (error) {
                console.error('Error starting recording:', error);
                updateStatus('❌ Error accessing microphone: ' + error.message);
            }
        }

        function stopRecording() {
            console.log('Stop recording requested');
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                console.log('Stopping active recording...');
                mediaRecorder.stop();
                updateStatus('⏳ Processing your recording...');
            } else {
                console.log('No active recording to stop');
                updateStatus('❌ No active recording found');
            }
        }

        async function saveRecordingToVoices() {
            if (!recordedBlob) {
                updateStatus('❌ No recording found to save');
                return;
            }
            
            try {
                updateStatus('💾 Auto-saving your recording...');
                
                const timestamp = new Date().getTime();
                const filename = `bengali_complaint_${timestamp}.wav`;
                const formData = new FormData();
                formData.append('audio', recordedBlob, filename);
                
                try {
                    const response = await fetch('http://localhost:8000/save-audio', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        updateStatus('✅ Recording saved! Use the buttons below to process your complaint.');
                        console.log('File saved:', result.filename);
                    } else {
                        throw new Error('Server not available');
                    }
                } catch (fetchError) {
                    console.warn('FastAPI server not available');
                    updateStatus('⚠️ Server unavailable. Recording ready in browser. Use buttons below.');
                }
                
            } catch (error) {
                console.error('Save error:', error);
                updateStatus('❌ Error saving: ' + error.message);
            }
        }
    </script>
    """

def main():
    st.title("🎫 Bangla Vai - Voice Ticketing System")
    st.markdown("**AI-Powered Bengali Voice-to-Ticket Support System**")
    
    # Check API connection
    if not check_fastapi_connection():
        st.error("🚨 FastAPI Server Not Running. Please start with: `python start_api.py`")
        st.stop()
    
    st.success("✅ API Server Connected")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        elevenlabs_key = st.text_input(
            "ElevenLabs API Key",
            type="password",
            value=os.getenv("ELEVENLABS_API_KEY", ""),
            help="Required for Bengali speech-to-text"
        )
        
        google_key = st.text_input(
            "Google API Key",
            type="password", 
            value=os.getenv("GOOGLE_API_KEY", ""),
            help="Required for AI analysis (Gemini)"
        )
        
        if st.button("🔧 Configure Keys"):
            if elevenlabs_key:
                try:
                    response = requests.post(f"{FASTAPI_BASE_URL}/config/api-key", data={"api_key": elevenlabs_key})
                    if response.status_code == 200:
                        st.success("✓ ElevenLabs key configured")
                    else:
                        st.error("❌ ElevenLabs key failed")
                except:
                    st.error("❌ Error configuring ElevenLabs key")
            
            if google_key:
                os.environ["GOOGLE_API_KEY"] = google_key
                st.success("✓ Google key configured")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎤 Voice Complaint", 
        "📋 Ticket Dashboard", 
        "📊 Analytics", 
        "⚙️ Management"
    ])
    
    # Tab 1: Voice Complaint
    with tab1:
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
        
        # Create two options: File Upload (Primary) and Live Recording (Secondary)
        upload_tab, record_tab = st.tabs(["📁 Upload Audio File", "🎙️ Live Recording"])
        
        # Tab 1.1: File Upload (Primary Method)
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
                                                st.text_area("", value=ticket['bengali_description'], height=150, disabled=True, key="bengali_orig")
                                            else:
                                                st.info("No Bengali text available")
                                        
                                        with desc_tab2:
                                            st.markdown("**AI-Enhanced English Description:**")
                                            st.text_area("", value=ticket['description'], height=150, disabled=True, key="english_desc")
                                        
                                        # Clear the session state
                                        st.session_state.uploaded_audio_file = None
                                        
                                        # Option to create another ticket
                                        if st.button("🔄 Create Another Ticket", type="secondary"):
                                            st.session_state.uploaded_audio_file = None
                                            st.rerun()
                                        
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
            else:
                st.info("👆 Please upload a Bengali audio file to get started")
        
        # Tab 1.2: Live Recording (Secondary Method)  
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
                                                st.text_area("", value=ticket['bengali_description'], height=150, disabled=True, key="bengali_orig")
                                            else:
                                                st.info("No Bengali text available")
                                        
                                        with desc_tab2:
                                            st.markdown("**AI-Enhanced English Description:**")
                                            st.text_area("", value=ticket['description'], height=150, disabled=True, key="english_desc")
                                        
                                        # Clear the form state
                                        st.session_state.show_customer_form = False
                                        st.session_state.ready_to_create_ticket = False
                                        st.session_state.recorded_file_path = None
                                        st.session_state.recording_completed = False
                                        
                                        # Option to create another ticket
                                        if st.button("🔄 Create Another Ticket", type="secondary"):
                                            # Just reset session state, don't force rerun
                                            st.session_state.show_customer_form = False
                                            st.session_state.ready_to_create_ticket = False
                                            st.session_state.recorded_file_path = None
                                            st.session_state.recording_completed = False
                                            st.success("🔄 Cleared! You can now record a new complaint.")
                                        
                                    else:
                                        st.error(f"❌ Error creating ticket: {response.text}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error processing voice complaint: {str(e)}")
                        else:
                            st.error("⚠️ Please provide at least customer name and email")
    
    # Tab 2: Ticket Dashboard
    with tab2:
        st.header("📋 Support Ticket Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_filter = st.selectbox("Status:", ["All", "open", "in_progress", "resolved", "closed"])
        with col2:
            priority_filter = st.selectbox("Priority:", ["All", "low", "medium", "high", "urgent"])
        with col3:
            category_filter = st.selectbox("Category:", ["All", "technical", "billing", "general", "complaint", "feature_request"])
        with col4:
            limit = st.number_input("Show:", min_value=10, max_value=100, value=20)
        
        if st.button("🔄 Load Tickets", type="primary"):
            success, result = get_tickets(status_filter, priority_filter, category_filter, limit)
            
            if success:
                tickets = result.get("tickets", [])
                total = result.get("total", 0)
                
                st.success(f"✅ Found {total} tickets")
                
                if tickets:
                    df_data = []
                    for ticket in tickets:
                        df_data.append({
                            "ID": ticket["id"],
                            "Title": ticket["title"][:50] + "..." if len(ticket["title"]) > 50 else ticket["title"],
                            "Customer": ticket["customer_name"],
                            "Status": ticket["status"].title(),
                            "Priority": ticket["priority"].title(),
                            "Category": ticket["category"].title(),
                            "Created": datetime.fromisoformat(ticket["created_at"].replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M"),
                            "Voice": "🎤" if ticket.get("audio_file_path") else "📝"
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    # Ticket details
                    if tickets:
                        st.subheader("🔍 Ticket Details")
                        selected = st.selectbox(
                            "Select ticket:",
                            [f"#{t['id']} - {t['title'][:30]}..." for t in tickets]
                        )
                        
                        if selected:
                            ticket_id = int(selected.split("#")[1].split(" ")[0])
                            ticket = next(t for t in tickets if t["id"] == ticket_id)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.info(f"**Customer:** {ticket['customer_name']}")
                                st.info(f"**Email:** {ticket.get('customer_email', 'N/A')}")
                                st.info(f"**Phone:** {ticket.get('customer_phone', 'N/A')}")
                                st.info(f"**Status:** {ticket['status'].title()}")
                            
                            with col2:
                                st.info(f"**Priority:** {ticket['priority'].title()}")
                                st.info(f"**Category:** {ticket['category'].title()}")
                                if ticket.get('subcategory'):
                                    st.info(f"**Subcategory:** {ticket['subcategory']}")
                                created = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00'))  
                                st.info(f"**Created:** {created.strftime('%Y-%m-%d %H:%M')}")
                                if ticket.get('audio_file_path'):
                                    st.info("**Type:** 🎤 Voice")
                            
                            # Enhanced display for Bengali and English descriptions
                            st.markdown("### 📝 Complaint Details")
                            
                            # Create tabs for better organization  
                            desc_tab1, desc_tab2 = st.tabs(["🇧🇩 Bengali Original", "🇺🇸 English Analysis"])
                            
                            with desc_tab1:
                                st.markdown("**Original Bengali Complaint:**")
                                if ticket.get('bengali_description'):
                                    st.text_area("", value=ticket['bengali_description'], height=120, disabled=True, key="bengali_view")
                                else:
                                    st.info("No Bengali text available")
                            
                            with desc_tab2:
                                st.markdown("**AI-Enhanced English Description:**")
                                st.text_area("", value=ticket['description'], height=120, disabled=True, key="english_view")
                else:
                    st.info("No tickets found")
            else:
                st.error(f"❌ Error: {result}")
    
    # Tab 3: Analytics
    with tab3:
        st.header("📊 Ticket Analytics")
        
        if st.button("📈 Load Analytics", type="primary"):
            success, stats = get_ticket_stats()
            
            if success:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Tickets", stats["total_tickets"])
                with col2:
                    st.metric("Open Tickets", stats["open_tickets"])
                with col3:
                    st.metric("Urgent Tickets", stats["urgent_tickets"])
                with col4:
                    resolution_rate = (stats['resolved_tickets'] / max(stats['total_tickets'], 1) * 100)
                    st.metric("Resolution Rate", f"{resolution_rate:.1f}%")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Status pie chart
                    status_data = stats["by_status"]
                    if any(status_data.values()):
                        fig = px.pie(
                            values=list(status_data.values()),
                            names=[k.replace('_', ' ').title() for k in status_data.keys()],
                            title="Tickets by Status"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Priority bar chart
                    priority_data = stats["by_priority"]
                    if any(priority_data.values()):
                        fig = px.bar(
                            x=[k.title() for k in priority_data.keys()],
                            y=list(priority_data.values()),
                            title="Tickets by Priority"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Category horizontal bar chart
                category_data = stats["by_category"]
                if any(category_data.values()):
                    fig = px.bar(
                        x=list(category_data.values()),
                        y=[k.replace('_', ' ').title() for k in category_data.keys()],
                        orientation='h',
                        title="Tickets by Category"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"❌ Error loading analytics: {stats}")
    
    # Tab 4: Management
    with tab4:
        st.header("⚙️ Ticket Management")
        
        ticket_id = st.number_input("Ticket ID:", min_value=1, value=1)
        
        if st.button("🔍 Load Ticket"):
            try:
                response = requests.get(f"{FASTAPI_BASE_URL}/tickets/{ticket_id}")
                if response.status_code == 200:
                    st.session_state['current_ticket'] = response.json()
                    st.success(f"✅ Loaded Ticket #{ticket_id}")
                else:
                    st.error("❌ Ticket not found")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        if 'current_ticket' in st.session_state:
            ticket = st.session_state['current_ticket']
            
            with st.form("update_ticket"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_status = st.selectbox(
                        "Status:",
                        ["open", "in_progress", "resolved", "closed"],
                        index=["open", "in_progress", "resolved", "closed"].index(ticket['status'])
                    )
                    new_priority = st.selectbox(
                        "Priority:",
                        ["low", "medium", "high", "urgent"],
                        index=["low", "medium", "high", "urgent"].index(ticket['priority'])
                    )
                
                with col2:
                    new_category = st.selectbox(
                        "Category:",
                        ["technical", "billing", "general", "complaint", "feature_request"],
                        index=["technical", "billing", "general", "complaint", "feature_request"].index(ticket['category'])
                    )
                    assigned_to = st.text_input("Assigned To:", value=ticket.get('assigned_to', ''))
                
                new_title = st.text_input("Title:", value=ticket['title'])
                new_description = st.text_area("Description:", value=ticket['description'], height=150)
                
                if st.form_submit_button("💾 Update Ticket", type="primary"):
                    updates = {
                        "title": new_title,
                        "description": new_description,
                        "status": new_status,
                        "priority": new_priority,
                        "category": new_category,
                        "assigned_to": assigned_to if assigned_to else None
                    }
                    
                    try:
                        response = requests.put(f"{FASTAPI_BASE_URL}/tickets/{ticket['id']}", json=updates)
                        if response.status_code == 200:
                            st.success("✅ Ticket updated!")
                            st.session_state['current_ticket'] = response.json()['ticket']
                        else:
                            st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ Error updating: {str(e)}")

if __name__ == "__main__":
    main()
