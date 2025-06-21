from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import time
import json
from typing import Optional, List, Dict, Any
from bengali_stt import BengaliSTT, BengaliTTS
from dotenv import load_dotenv
import aiofiles
from sqlalchemy.orm import Session
from database import get_db, create_tables, Ticket, TicketStatus, TicketPriority, TicketCategory
from models import (
    TicketCreateRequest, TicketResponse, TicketListResponse, TicketCreateResponse,
    VoiceTicketRequest, VoiceProcessingResponse, TicketUpdateRequest, TicketUpdateResponse,
    TicketDeleteResponse, TicketSearchRequest, TicketStatsResponse
)
from gemini_service import get_gemini_processor
from intelligent_ticket_processor import get_intelligent_processor
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create database tables
create_tables()

app = FastAPI(
    title="Bangla Vai Ticketing API",
    description="Bengali Voice-to-Ticket System with Speech Processing and AI Analysis",
    version="2.0.0"
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
        "message": "Bangla Vai Ticketing API - Bengali Voice-to-Ticket System",
        "version": "2.0.0",
        "endpoints": {
            # Speech processing endpoints
            "transcribe": "/stt/transcribe - Upload audio file for Bengali speech-to-text",
            "text_to_speech": "/tts/convert - Convert Bengali text to speech",
            "download_audio": "/tts/download/{timestamp} - Download generated speech file",
            "list_files": "/files/list - List all uploaded audio files",
            "config_api_key": "/config/api-key - Configure ElevenLabs API key",
            "health": "/health - API health check",
            # Ticketing endpoints
            "create_ticket": "/tickets/create - Create a new ticket",
            "voice_to_ticket": "/tickets/voice-to-ticket - Create ticket from Bengali voice",
            "get_ticket": "/tickets/{ticket_id} - Get specific ticket",
            "list_tickets": "/tickets - List all tickets with filters",
            "update_ticket": "/tickets/{ticket_id} - Update ticket",
            "delete_ticket": "/tickets/{ticket_id} - Delete ticket",
            "ticket_stats": "/tickets/stats - Get ticket statistics",
            "process_voice_complaint": "/process/voice-complaint - Process Bengali voice complaint",
            "save_audio": "/save-audio - Save recorded audio file to voices folder",
            "process_voice_with_attachment": "/process/voice-with-attachment - Process voice complaint with attachment"
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

# ============================================================================
# TICKETING SYSTEM ENDPOINTS
# ============================================================================

@app.post("/tickets/create", response_model=TicketCreateResponse)
async def create_ticket(
    ticket_data: TicketCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new support ticket
    """
    try:
        # Create new ticket
        new_ticket = Ticket(
            title=ticket_data.title,
            description=ticket_data.description,
            customer_name=ticket_data.customer_name,
            customer_email=ticket_data.customer_email,
            customer_phone=ticket_data.customer_phone,
            category=TicketCategory(ticket_data.category.value),
            priority=TicketPriority(ticket_data.priority.value),
            status=TicketStatus.OPEN
        )
        
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        
        return TicketCreateResponse(
            success=True,
            message=f"Ticket #{new_ticket.id} created successfully",
            ticket=TicketResponse.from_orm(new_ticket)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating ticket: {str(e)}")

@app.post("/tickets/voice-to-ticket", response_model=VoiceProcessingResponse)
async def create_ticket_from_voice(
    voice_data: VoiceTicketRequest,
    db: Session = Depends(get_db)
):
    """
    Create a ticket from Bengali voice complaint using AI processing
    """
    try:
        # Process Bengali text with Gemini AI
        gemini = get_gemini_processor()
        ai_analysis = gemini.process_bengali_complaint(voice_data.bengali_text)
        
        # Enhance the description
        enhanced_description = gemini.enhance_ticket_description(
            ai_analysis["english_translation"],
            ai_analysis["key_points"]
        )
        
        # Create ticket from AI analysis
        new_ticket = Ticket(
            title=ai_analysis["title"],
            description=enhanced_description,
            bengali_description=voice_data.bengali_text,
            audio_file_path=voice_data.audio_file_path,
            customer_name=voice_data.customer_name,
            customer_email=voice_data.customer_email,
            customer_phone=voice_data.customer_phone,
            category=TicketCategory(ai_analysis["category"]),
            priority=TicketPriority(ai_analysis["priority"]),
            status=TicketStatus.OPEN
        )
        
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        
        return VoiceProcessingResponse(
            success=True,
            message=f"Voice ticket #{new_ticket.id} created successfully with AI analysis",
            bengali_text=voice_data.bengali_text,
            english_translation=ai_analysis["english_translation"],
            ai_analysis=ai_analysis,
            ticket=TicketResponse.from_orm(new_ticket)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating voice ticket: {str(e)}")

@app.post("/process/voice-complaint")
async def process_voice_complaint(
    file: UploadFile = File(..., description="Bengali audio file"),
    customer_name: str = Form(..., description="Customer name"),
    customer_email: Optional[str] = Form(None, description="Customer email"),
    customer_phone: Optional[str] = Form(None, description="Customer phone"),
    db: Session = Depends(get_db)
):
    """
    Complete voice-to-ticket pipeline: transcribe Bengali audio → AI analysis → create ticket
    """
    try:
        # Step 1: Transcribe audio
        voices_dir = "voices"
        if not os.path.exists(voices_dir):
            os.makedirs(voices_dir)
        
        timestamp = int(time.time())
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "wav"
        saved_filename = f"complaint_audio_{timestamp}.{file_extension}"
        saved_file_path = os.path.join(voices_dir, saved_filename)
        
        content = await file.read()
        with open(saved_file_path, "wb") as f:
            f.write(content)
        
        # Transcribe audio
        stt = get_stt_client()
        transcription_result = stt.transcribe_audio_file(saved_file_path, "bengali")
        
        if not transcription_result:
            raise HTTPException(status_code=500, detail="Audio transcription failed")
        
        bengali_text = transcription_result.get('text', '') or transcription_result.get('transcription', '')
        
        if not bengali_text.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        # Step 2: Process with Intelligent AI Pipeline
        intelligent_processor = get_intelligent_processor()
        extracted_data = intelligent_processor.process_bengali_voice_input(bengali_text)
        
        # Get enhanced description from Gemini
        gemini = get_gemini_processor()
        enhanced_description = gemini.enhance_ticket_description(
            extracted_data["ai_analysis"].get("english_translation", ""),
            extracted_data["ai_analysis"].get("key_points", [])
        )
        
        # Use the intelligent processor's structured description if available
        if extracted_data["description"]:
            enhanced_description = extracted_data["description"]
        
        # Step 3: Create ticket with intelligent processing results
        new_ticket = Ticket(
            title=extracted_data["title"],
            description=enhanced_description,
            bengali_description=bengali_text,
            audio_file_path=saved_file_path,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            category=TicketCategory(extracted_data["category"]),
            subcategory=extracted_data["subcategory"],
            product=extracted_data["product"],
            priority=TicketPriority(extracted_data["priority"]),
            status=TicketStatus.OPEN
        )
        
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        
        return {
            "success": True,
            "message": f"Voice complaint processed and ticket #{new_ticket.id} created",
            "transcription": {
                "bengali_text": bengali_text,
                "language_code": transcription_result.get('language_code', 'unknown'),
                "language_probability": transcription_result.get('language_probability', 0),
                "audio_file": saved_file_path
            },
            "intelligent_analysis": {
                "category": extracted_data["category"],
                "subcategory": extracted_data["subcategory"],
                "priority": extracted_data["priority"],
                "product": extracted_data["product"],
                "keywords": extracted_data["keywords"],
                "sentiment": extracted_data["sentiment"],
                "urgency_indicators": extracted_data["urgency_indicators"]
            },
            "ai_analysis": extracted_data["ai_analysis"],
            "ticket": TicketResponse.from_orm(new_ticket)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing voice complaint: {str(e)}")

@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Get a specific ticket by ID
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return TicketResponse.from_orm(ticket)

@app.get("/tickets", response_model=TicketListResponse)
async def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    customer_name: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List tickets with optional filters
    """
    query = db.query(Ticket)
    
    # Apply filters
    if status:
        query = query.filter(Ticket.status == TicketStatus(status))
    if priority:
        query = query.filter(Ticket.priority == TicketPriority(priority))
    if category:
        query = query.filter(Ticket.category == TicketCategory(category))
    if customer_name:
        query = query.filter(Ticket.customer_name.ilike(f"%{customer_name}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination and get results
    tickets = query.offset(offset).limit(limit).all()
    
    return TicketListResponse(
        tickets=[TicketResponse.from_orm(ticket) for ticket in tickets],
        total=total,
        limit=limit,
        offset=offset
    )

@app.put("/tickets/{ticket_id}", response_model=TicketUpdateResponse)
async def update_ticket(
    ticket_id: int,
    update_data: TicketUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a ticket
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    try:
        # Update fields if provided
        if update_data.title is not None:
            ticket.title = update_data.title
        if update_data.description is not None:
            ticket.description = update_data.description
        if update_data.status is not None:
            ticket.status = TicketStatus(update_data.status.value)
            if update_data.status.value == "resolved":
                ticket.resolved_at = datetime.utcnow()
        if update_data.priority is not None:
            ticket.priority = TicketPriority(update_data.priority.value)
        if update_data.category is not None:
            ticket.category = TicketCategory(update_data.category.value)
        if update_data.assigned_to is not None:
            ticket.assigned_to = update_data.assigned_to
        
        ticket.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ticket)
        
        return TicketUpdateResponse(
            success=True,
            message=f"Ticket #{ticket_id} updated successfully",
            ticket=TicketResponse.from_orm(ticket)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")

@app.delete("/tickets/{ticket_id}", response_model=TicketDeleteResponse)
async def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Delete a ticket
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    try:
        db.delete(ticket)
        db.commit()
        
        return TicketDeleteResponse(
            success=True,
            message=f"Ticket #{ticket_id} deleted successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting ticket: {str(e)}")

@app.get("/tickets/stats", response_model=TicketStatsResponse)
async def get_ticket_stats(db: Session = Depends(get_db)):
    """
    Get ticket statistics
    """
    try:
        total_tickets = db.query(Ticket).count()
        open_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.OPEN).count()
        in_progress_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.IN_PROGRESS).count()
        resolved_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.RESOLVED).count()
        closed_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.CLOSED).count()
        urgent_tickets = db.query(Ticket).filter(Ticket.priority == TicketPriority.URGENT).count()
        high_priority_tickets = db.query(Ticket).filter(Ticket.priority == TicketPriority.HIGH).count()
        
        # Statistics by category
        by_category = {}
        for category in TicketCategory:
            count = db.query(Ticket).filter(Ticket.category == category).count()
            by_category[category.value] = count
        
        # Statistics by priority
        by_priority = {}
        for priority in TicketPriority:
            count = db.query(Ticket).filter(Ticket.priority == priority).count()
            by_priority[priority.value] = count
        
        # Statistics by status
        by_status = {}
        for status in TicketStatus:
            count = db.query(Ticket).filter(Ticket.status == status).count()
            by_status[status.value] = count
        
        return TicketStatsResponse(
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            in_progress_tickets=in_progress_tickets,
            resolved_tickets=resolved_tickets,
            closed_tickets=closed_tickets,
            urgent_tickets=urgent_tickets,
            high_priority_tickets=high_priority_tickets,
            by_category=by_category,
            by_priority=by_priority,
            by_status=by_status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ticket stats: {str(e)}")

@app.post("/process/intelligent-analysis")
async def test_intelligent_processing(
    bengali_text: str = Form(..., description="Bengali text to analyze"),
):
    """
    Test the intelligent processing pipeline with Bengali text
    
    This endpoint allows testing the intelligent ticket processor directly
    with Bengali text input to see the categorization, priority detection,
    product identification, and description formatting.
    """
    try:
        # Process with intelligent processor
        intelligent_processor = get_intelligent_processor()
        extracted_data = intelligent_processor.process_bengali_voice_input(bengali_text)
        
        # Import the constants for reference
        from intelligent_ticket_processor import CATEGORIES, PRIORITIES, PRODUCTS, SUBCATEGORIES
        
        return {
            "success": True,
            "message": "Text processed successfully with intelligent analysis",
            "input_text": bengali_text,
            "extracted_data": {
                "category": extracted_data["category"],
                "subcategory": extracted_data["subcategory"],
                "priority": extracted_data["priority"],
                "product": extracted_data["product"],
                "title": extracted_data["title"],
                "description": extracted_data["description"],
                "keywords": extracted_data["keywords"],
                "sentiment": extracted_data["sentiment"],
                "urgency_indicators": extracted_data["urgency_indicators"]
            },
            "ai_analysis": extracted_data["ai_analysis"],
            "hard_coded_values": {
                "available_categories": list(CATEGORIES.keys()),
                "available_priorities": list(PRIORITIES.keys()),
                "available_products": list(PRODUCTS.keys()),
                "available_subcategories": {k: v for k, v in SUBCATEGORIES.items()}
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in intelligent processing: {str(e)}")

@app.post("/save-audio")
async def save_audio(audio: UploadFile = File(...)):
    """Save recorded audio file to voices folder"""
    try:
        # Create voices directory if it doesn't exist
        voices_dir = Path("voices")
        voices_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = int(time.time() * 1000)
        filename = f"bengali_complaint_{timestamp}.wav"
        filepath = voices_dir / filename
        
        # Save the audio file
        with open(filepath, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
        
        return {
            "success": True,
            "filename": filename,
            "filepath": str(filepath),
            "message": "Audio file saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error saving audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving audio file: {str(e)}")

@app.post("/process/voice-with-attachment")
async def process_voice_with_attachment(
    audio_file: UploadFile = File(..., description="Bengali audio file"),
    attachment_file: Optional[UploadFile] = File(None, description="Attachment file (screenshot, document, etc.) - OPTIONAL"),
    customer_name: str = Form(..., description="Customer name"),
    customer_email: Optional[str] = Form(None, description="Customer email"),
    customer_phone: Optional[str] = Form(None, description="Customer phone"),
    attachment_description: Optional[str] = Form(None, description="Description of what the attachment contains"),
    db: Session = Depends(get_db)
):
    """
    Enhanced voice processing pipeline: transcribe Bengali audio → optionally analyze attachment → combined AI analysis → create enhanced ticket
    
    Attachment is now OPTIONAL - you can process voice complaints without attachments
    """
    try:
        # Create directories
        voices_dir = "voices"
        attachments_dir = "attachments"
        for directory in [voices_dir, attachments_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        timestamp = int(time.time())
        
        # Step 1: Save and transcribe audio file
        audio_extension = audio_file.filename.split(".")[-1] if "." in audio_file.filename else "wav"
        audio_filename = f"complaint_audio_{timestamp}.{audio_extension}"
        audio_path = os.path.join(voices_dir, audio_filename)
        
        audio_content = await audio_file.read()
        with open(audio_path, "wb") as f:
            f.write(audio_content)
        
        # Transcribe audio
        stt = get_stt_client()
        transcription_result = stt.transcribe_audio_file(audio_path, "bengali")
        
        if not transcription_result:
            raise HTTPException(status_code=500, detail="Audio transcription failed")
        
        bengali_text = transcription_result.get('text', '') or transcription_result.get('transcription', '')
        
        if not bengali_text.strip():
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        # Step 2: Process Bengali text with Gemini
        gemini = get_gemini_processor()
        voice_analysis = gemini.process_bengali_complaint(bengali_text)
        
        # Step 3: Optionally analyze attachment if provided
        attachment_path = None
        attachment_filename = None
        combined_analysis = None
        
        if attachment_file is not None:
            # Save attachment file
            attachment_extension = attachment_file.filename.split(".")[-1] if "." in attachment_file.filename else "jpg"
            attachment_filename = f"attachment_{timestamp}.{attachment_extension}"
            attachment_path = os.path.join(attachments_dir, attachment_filename)
            
            attachment_content = await attachment_file.read()
            with open(attachment_path, "wb") as f:
                f.write(attachment_content)
            
            # Analyze attachment with voice context
            combined_analysis = gemini.analyze_attachment_with_voice(
                attachment_content, attachment_file.filename, bengali_text, voice_analysis
            )
        
        # Step 4: Create enhanced ticket with analysis (attachment analysis if available)
        if combined_analysis:
            enhanced_ticket_info = combined_analysis.get("enhanced_ticket", {})
            # Use enhanced information from attachment analysis
            final_title = enhanced_ticket_info.get("title", voice_analysis.get("title", "Voice Complaint with Attachment"))
            final_description = enhanced_ticket_info.get("description", voice_analysis.get("english_translation", ""))
            raw_category = enhanced_ticket_info.get("category", voice_analysis.get("category", "general"))
            raw_priority = enhanced_ticket_info.get("priority", voice_analysis.get("priority", "medium"))
        else:
            # Use voice analysis only
            final_title = voice_analysis.get("title", "Voice Complaint")
            final_description = voice_analysis.get("english_translation", "")
            raw_category = voice_analysis.get("category", "general")
            raw_priority = voice_analysis.get("priority", "medium")
        
        # Map AI-generated categories to valid enum values
        final_category = gemini._map_category_to_enum(raw_category)
        final_priority = gemini._map_priority_to_enum(raw_priority)
        
        # Create the ticket
        new_ticket = Ticket(
            title=final_title,
            description=final_description,
            bengali_description=bengali_text,
            audio_file_path=audio_path,
            attachment_file_path=attachment_path,  # Will be None if no attachment
            attachment_analysis=json.dumps(combined_analysis, ensure_ascii=False) if combined_analysis else None,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            category=TicketCategory(final_category),
            priority=TicketPriority(final_priority),
            status=TicketStatus.OPEN
        )
        
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        
        # Prepare response based on whether attachment was provided
        response_data = {
            "success": True,
            "message": f"Voice complaint processed and ticket #{new_ticket.id} created" + (" with attachment analysis" if attachment_file else ""),
            "bengali_text": bengali_text,
            "english_translation": voice_analysis.get("english_translation", ""),
            "transcription_details": {
                "language_code": transcription_result.get('language_code', 'unknown'),
                "language_probability": transcription_result.get('language_probability', 0),
                "audio_file": audio_path
            },
            "ticket": TicketResponse.from_orm(new_ticket),
            "has_attachment": attachment_file is not None
        }
        
        # Add attachment-related data only if attachment was provided
        if attachment_file is not None and combined_analysis:
            response_data.update({
                "attachment_analysis": combined_analysis.get("attachment_analysis", {}),
                "voice_image_correlation": combined_analysis.get("voice_image_correlation", {}),
                "technical_assessment": combined_analysis.get("technical_assessment", {}),
                "combined_ai_analysis": combined_analysis,
                "attachment_details": {
                    "filename": attachment_file.filename,
                    "saved_as": attachment_filename,
                    "file_path": attachment_path,
                    "description": attachment_description
                }
            })
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing voice complaint: {str(e)}")

@app.post("/rag/search")
async def search_similar_tickets(
    query: str = Form(..., description="Search query to find similar tickets"),
    max_results: int = Form(5, description="Maximum number of results to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    RAG-based search: Find similar tickets from the knowledge base using vector similarity
    """
    try:
        # Validate inputs
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Limit max_results to prevent abuse
        max_results = max(1, min(max_results, 20))
        
        logger.info(f"RAG search request: query='{query[:50]}...', max_results={max_results}")
        
        # Use singleton ChromaDB RAG service
        from rag_service import get_rag_service
        rag_service = get_rag_service()
        
        # Perform the search
        results = rag_service.search_similar_tickets(query.strip(), max_results)
        
        logger.info(f"RAG search completed: found {len(results)} results")
        
        return {
            "success": True,
            "query": query.strip(),
            "results": results,
            "total_results": len(results),
            "database_stats": rag_service.get_database_stats()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG search error: {str(e)}")
        logger.error(f"Query was: '{query}', max_results: {max_results}")
        raise HTTPException(status_code=500, detail=f"Error in RAG search: {str(e)}")

@app.post("/rag/initialize")
async def initialize_rag_database() -> Dict[str, Any]:
    """
    Initialize the RAG database with customer support tickets from CSV
    """
    try:
        logger.info("RAG database initialization requested")
        
        # Use singleton ChromaDB RAG service
        from rag_service import get_rag_service
        rag_service = get_rag_service()
        count = rag_service.initialize_database()
        
        logger.info(f"RAG database initialized with {count} tickets")
        
        return {
            "success": True,
            "message": f"RAG database initialized with {count} tickets",
            "tickets_loaded": count,
            "database_stats": rag_service.get_database_stats()
        }
        
    except Exception as e:
        logger.error(f"RAG initialization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing RAG database: {str(e)}")

@app.get("/rag/status")
async def get_rag_status() -> Dict[str, Any]:
    """
    Get RAG database status and statistics
    """
    try:
        from rag_service import get_rag_service
        
        # Check if ChromaDB directory exists
        chroma_db_path = "./chroma_db"
        if not os.path.exists(chroma_db_path):
            return {
                "success": False,
                "status": "not_initialized", 
                "message": "ChromaDB directory not found. Please initialize first.",
                "database_path": chroma_db_path
            }
        
        # Get database stats using singleton ChromaDB service
        rag_service = get_rag_service()
        stats = rag_service.get_database_stats()
        
        return {
            "success": True,
            "status": "ready",
            "stats": stats,
            "database_path": chroma_db_path
        }
        
    except Exception as e:
        logger.error(f"RAG status error: {str(e)}")
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 