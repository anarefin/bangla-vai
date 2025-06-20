from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import time
import json
from typing import Optional
from bengali_stt import BengaliSTT, BengaliTTS
from dotenv import load_dotenv
import aiofiles

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Bangla Vai API",
    description="Bengali Speech-to-Text and Text-to-Speech API",
    version="1.0.0"
)

# Add CORS middleware to allow requests from Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients (will be created per request to avoid issues)
def get_stt_client():
    """Get STT client with API key validation"""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="ELEVENLABS_API_KEY not configured")
    return BengaliSTT()

def get_tts_client():
    """Get TTS client"""
    return BengaliTTS()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Bangla Vai API - Bengali Speech Processing",
        "version": "1.0.0",
        "endpoints": {
            "transcribe": "/stt/transcribe - Upload audio file for Bengali speech-to-text",
            "text_to_speech": "/tts/convert - Convert Bengali text to speech",
            "download_audio": "/tts/download/{timestamp} - Download generated speech file",
            "list_files": "/files/list - List all uploaded audio files",
            "config_api_key": "/config/api-key - Configure ElevenLabs API key",
            "health": "/health - API health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/stt/transcribe")
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form("bengali", description="Language for transcription")
):
    """
    Transcribe audio file to Bengali text using ElevenLabs Scribe API
    
    - **file**: Audio file (supported formats: wav, mp3, ogg, m4a, webm)
    - **language**: Language for transcription (default: bengali)
    """
    try:
        # Validate file type
        allowed_types = ['audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/mp4', 'audio/webm']
        if file.content_type not in allowed_types:
            # Also check file extension as fallback
            allowed_extensions = ['.wav', '.mp3', '.ogg', '.m4a', '.webm']
            if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type. Supported types: {allowed_extensions}"
                )
        
        # Create voices directory if it doesn't exist
        voices_dir = "voices"
        if not os.path.exists(voices_dir):
            os.makedirs(voices_dir)
        
        # Generate timestamp for unique filename
        timestamp = int(time.time())
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "wav"
        saved_filename = f"uploaded_audio_{timestamp}.{file_extension}"
        saved_file_path = os.path.join(voices_dir, saved_filename)
        
        # Save uploaded file to voices directory
        content = await file.read()
        with open(saved_file_path, "wb") as f:
            f.write(content)
        
        try:
            # Initialize STT client
            stt = get_stt_client()
            
            # Transcribe the audio
            result = stt.transcribe_audio_file(saved_file_path, language)
            
            if result:
                # Extract transcription text
                if 'text' in result:
                    transcription_text = result['text']
                elif 'transcription' in result:
                    transcription_text = result['transcription']
                else:
                    transcription_text = str(result)
                
                return {
                    "success": True,
                    "transcription": transcription_text,
                    "language_code": result.get('language_code', 'unknown'),
                    "language_probability": result.get('language_probability', 0),
                    "full_result": result,
                    "filename": file.filename,
                    "saved_as": saved_filename,
                    "saved_path": saved_file_path
                }
            else:
                raise HTTPException(status_code=500, detail="Transcription failed")
                
        except Exception as transcription_error:
            # If transcription fails, we still keep the uploaded file
            raise HTTPException(
                status_code=500, 
                detail=f"Transcription failed: {str(transcription_error)}. File saved as: {saved_filename}"
            )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during transcription: {str(e)}")

@app.post("/tts/convert")
async def convert_text_to_speech(
    text: str = Form(..., description="Bengali text to convert to speech"),
    slow: bool = Form(False, description="Whether to speak slowly"),
    return_file: bool = Form(False, description="Whether to return file download link")
):
    """
    Convert Bengali text to speech using Google TTS
    
    - **text**: Bengali text to convert
    - **slow**: Enable slower speech (default: False)  
    - **return_file**: Return downloadable file response (default: False)
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Initialize TTS client
        tts = get_tts_client()
        
        # Generate timestamp for unique filename
        timestamp = int(time.time())
        
        if return_file:
            # Create voices directory if it doesn't exist
            voices_dir = "voices"
            if not os.path.exists(voices_dir):
                os.makedirs(voices_dir)
            
            output_filename = f"bengali_speech_{timestamp}.mp3"
            output_path = os.path.join(voices_dir, output_filename)
        else:
            output_path = None
        
        # Convert text to speech
        audio_path = tts.text_to_speech(text, output_path, slow=slow)
        
        if audio_path and os.path.exists(audio_path):
            if return_file:
                # Return file for download
                return FileResponse(
                    path=audio_path,
                    media_type='audio/mpeg',
                    filename=f"bengali_speech_{timestamp}.mp3"
                )
            else:
                # Return file path and metadata
                return {
                    "success": True,
                    "message": "Speech generated successfully",
                    "audio_path": audio_path,
                    "text": text,
                    "slow": slow,
                    "timestamp": timestamp
                }
        else:
            raise HTTPException(status_code=500, detail="Speech generation failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during text-to-speech conversion: {str(e)}")

@app.get("/tts/download/{timestamp}")
async def download_speech_file(timestamp: int):
    """
    Download generated speech file by timestamp
    
    - **timestamp**: Timestamp of the generated file
    """
    try:
        voices_dir = "voices"
        filename = f"bengali_speech_{timestamp}.mp3"
        file_path = os.path.join(voices_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=file_path,
            media_type='audio/mpeg',
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.get("/files/list")
async def list_uploaded_files():
    """
    List all uploaded audio files in the voices directory
    """
    try:
        voices_dir = "voices"
        if not os.path.exists(voices_dir):
            return {
                "success": True,
                "files": [],
                "message": "No files uploaded yet"
            }
        
        files = []
        for filename in os.listdir(voices_dir):
            if filename.startswith("uploaded_audio_"):
                file_path = os.path.join(voices_dir, filename)
                file_stats = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size_bytes": file_stats.st_size,
                    "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                    "created_time": file_stats.st_ctime,
                    "modified_time": file_stats.st_mtime
                })
        
        # Sort by creation time (most recent first)
        files.sort(key=lambda x: x["created_time"], reverse=True)
        
        return {
            "success": True,
            "files": files,
            "total_files": len(files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.post("/config/api-key")
async def set_api_key(api_key: str = Form(..., description="ElevenLabs API key")):
    """
    Set ElevenLabs API key for the session
    
    - **api_key**: Your ElevenLabs API key
    """
    try:
        if not api_key.strip():
            raise HTTPException(status_code=400, detail="API key cannot be empty")
        
        # Set environment variable
        os.environ["ELEVENLABS_API_KEY"] = api_key.strip()
        
        # Test the API key by initializing the client
        try:
            stt = BengaliSTT()
            return {
                "success": True,
                "message": "API key configured successfully"
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid API key: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting API key: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 