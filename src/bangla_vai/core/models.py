from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TicketStatusEnum(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketCategoryEnum(str, Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    GENERAL = "general"
    COMPLAINT = "complaint"
    FEATURE_REQUEST = "feature_request"

# Request Models
class TicketCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=1, description="Detailed description of the issue")
    customer_name: str = Field(..., min_length=1, max_length=100, description="Customer name")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email address")
    customer_phone: Optional[str] = Field(None, max_length=20, description="Customer phone number")
    category: Optional[TicketCategoryEnum] = Field(TicketCategoryEnum.GENERAL, description="Issue category")
    priority: Optional[TicketPriorityEnum] = Field(TicketPriorityEnum.MEDIUM, description="Priority level")

class VoiceTicketRequest(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100, description="Customer name")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email address")
    customer_phone: Optional[str] = Field(None, max_length=20, description="Customer phone number")
    bengali_text: str = Field(..., min_length=1, description="Bengali complaint text from voice")
    audio_file_path: Optional[str] = Field(None, description="Path to the audio file")

class TicketUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    status: Optional[TicketStatusEnum] = Field(None, description="Updated status")
    priority: Optional[TicketPriorityEnum] = Field(None, description="Updated priority")
    category: Optional[TicketCategoryEnum] = Field(None, description="Updated category")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Assigned team member")

class TicketSearchRequest(BaseModel):
    status: Optional[TicketStatusEnum] = Field(None, description="Filter by status")
    priority: Optional[TicketPriorityEnum] = Field(None, description="Filter by priority")
    category: Optional[TicketCategoryEnum] = Field(None, description="Filter by category")
    customer_name: Optional[str] = Field(None, description="Filter by customer name")
    assigned_to: Optional[str] = Field(None, description="Filter by assigned person")
    date_from: Optional[datetime] = Field(None, description="Filter tickets from this date")
    date_to: Optional[datetime] = Field(None, description="Filter tickets to this date")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Number of tickets to return")
    offset: Optional[int] = Field(0, ge=0, description="Number of tickets to skip")

# Response Models
class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    bengali_description: Optional[str] = None
    audio_file_path: Optional[str] = None
    attachment_file_path: Optional[str] = None
    attachment_analysis: Optional[str] = None
    status: TicketStatusEnum
    priority: TicketPriorityEnum
    category: TicketCategoryEnum
    subcategory: Optional[str] = None
    product: Optional[str] = None
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int
    limit: int
    offset: int

class TicketCreateResponse(BaseModel):
    success: bool
    message: str
    ticket: TicketResponse
    ai_analysis: Optional[dict] = None

class VoiceProcessingResponse(BaseModel):
    success: bool
    message: str
    bengali_text: str
    english_translation: str
    ai_analysis: dict
    ticket: Optional[TicketResponse] = None

class TicketUpdateResponse(BaseModel):
    success: bool
    message: str
    ticket: TicketResponse

class TicketDeleteResponse(BaseModel):
    success: bool
    message: str

class TicketStatsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    urgent_tickets: int
    high_priority_tickets: int
    by_category: dict
    by_priority: dict
    by_status: dict

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

# Voice Processing Models
class VoiceTranscriptionResponse(BaseModel):
    success: bool
    transcription: str
    language_code: str
    language_probability: float
    filename: str
    saved_path: str

class BengaliProcessingResult(BaseModel):
    english_translation: str
    title: str
    category: str
    priority: str
    key_points: List[str]
    sentiment: str
    urgency_indicators: List[str]

class VoiceWithAttachmentRequest(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100, description="Customer name")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email address")
    customer_phone: Optional[str] = Field(None, max_length=20, description="Customer phone number")
    bengali_text: Optional[str] = Field(None, description="Bengali complaint text from voice (optional if audio provided)")
    audio_file_path: Optional[str] = Field(None, description="Path to the audio file")
    attachment_description: Optional[str] = Field(None, description="Description of what the attachment contains")

class VoiceWithAttachmentResponse(BaseModel):
    success: bool
    message: str
    bengali_text: Optional[str] = None
    english_translation: Optional[str] = None
    attachment_analysis: Optional[dict] = None
    combined_ai_analysis: dict
    ticket: Optional[TicketResponse] = None

class AttachmentAnalysisResult(BaseModel):
    attachment_type: str
    content_description: str
    extracted_text: Optional[str] = None
    technical_details: Optional[dict] = None
    relevance_to_complaint: str
    suggested_actions: List[str] 