# 🎤📎 Voice + Attachment Ticketing Feature (Refactored)

## Overview

The Voice + Attachment feature enhances the existing Bengali voice ticketing system by allowing customers to submit both voice complaints and supporting attachments (screenshots, documents, etc.) simultaneously. This creates more contextual and accurate tickets through advanced AI analysis.

**✅ Refactored for simplicity:**
- **No Pillow dependency** - Gemini Vision API handles raw image bytes directly
- **Extended existing streamlit_app.py** - Uses the proven working voice complaint system
- **Simplified architecture** - Less dependencies, same functionality

## 🚀 Key Features

### 1. Multi-Modal Input Processing
- **Bengali Voice Transcription**: Uses ElevenLabs Scribe API for accurate Bengali speech-to-text
- **Attachment Analysis**: Supports images (PNG, JPG, JPEG, GIF), documents (PDF, DOC, DOCX), and text files
- **Combined AI Analysis**: Gemini Vision API analyzes both voice and visual content together using raw bytes

### 2. Enhanced AI Processing
- **Voice-Image Correlation**: AI determines how the attachment relates to the voice complaint
- **Technical Assessment**: Automatically identifies technical issues from screenshots
- **Contextual Understanding**: Combines voice context with visual evidence for better ticket categorization

### 3. Comprehensive Ticket Creation
- **Enhanced Descriptions**: AI-generated descriptions that combine voice and visual information
- **Smart Categorization**: More accurate category and priority assignment based on multiple inputs
- **Detailed Analysis**: Stores comprehensive analysis results for customer service review

## 🔧 Technical Architecture (Refactored)

### API Endpoints

#### Enhanced Endpoint: `/process/voice-with-attachment`
```http
POST /process/voice-with-attachment
Content-Type: multipart/form-data

Form Data:
- audio_file: Bengali audio file (wav, mp3, ogg, m4a, webm)
- attachment_file: Supporting file (png, jpg, jpeg, gif, pdf, doc, docx, txt)
- customer_name: Customer's full name
- customer_email: Customer's email address
- customer_phone: Customer's phone number (optional)
- attachment_description: Description of the attachment (optional)
```

#### Response Format
```json
{
  "success": true,
  "message": "Voice + attachment complaint processed and ticket #123 created",
  "bengali_text": "Transcribed Bengali text",
  "english_translation": "English translation of voice",
  "attachment_analysis": {
    "type": "screenshot",
    "content_description": "Detailed description of what's shown",
    "technical_details": {"error_code": "404"},
    "extracted_text": "Any text visible in the image",
    "key_visual_elements": ["error message", "UI elements"]
  },
  "voice_image_correlation": {
    "relationship": "How attachment relates to voice complaint",
    "consistency": "Does attachment support the voice complaint?",
    "additional_context": "What new information does attachment provide?"
  },
  "technical_assessment": {
    "is_technical_issue": true,
    "error_codes": ["404", "CONNECTION_FAILED"],
    "system_state": "Application showing error state",
    "troubleshooting_steps": ["Check network connection", "Retry operation"]
  },
  "ticket": {
    // Standard ticket object with enhanced fields
  }
}
```

### Database Schema Updates

#### Enhanced Ticket Model
```sql
-- New fields added to tickets table
ALTER TABLE tickets ADD COLUMN attachment_file_path VARCHAR(500);
ALTER TABLE tickets ADD COLUMN attachment_analysis TEXT;
```

### AI Processing Pipeline (Simplified)

1. **Voice Transcription** (ElevenLabs Scribe API)
   - Convert Bengali audio to text
   - Language detection and confidence scoring

2. **Attachment Analysis** (Gemini Vision API)
   - Direct processing of raw attachment bytes
   - No image preprocessing required
   - Support for multiple file formats

3. **Combined Analysis** (Gemini Pro API)
   - Voice-attachment correlation analysis
   - Enhanced ticket information generation
   - Technical assessment and troubleshooting suggestions

4. **Ticket Creation**
   - Store all analysis results
   - Create enhanced ticket with combined context
   - Save both voice and attachment files

## 🎯 Usage Guide

### For End Users (streamlit_app.py)

1. **Navigate to Voice Complaint Tab**
   - Open the Streamlit application: `streamlit run streamlit_app.py`
   - Click on "🎤 Voice Complaint" tab
   - Select "🎤📎 Voice + Attachment" sub-tab

2. **Upload Files**
   - Upload Bengali audio file (your voice complaint)
   - Upload attachment file (screenshot, document, etc.)
   - Both files are required to proceed

3. **Provide Context**
   - Enter customer information (name, email, phone)
   - Optionally describe what the attachment contains
   - Select priority level

4. **Create Enhanced Ticket**
   - Click "🚀 CREATE ENHANCED TICKET"
   - Wait 30-60 seconds for AI processing
   - Review the enhanced ticket with detailed analysis

### For Developers (API Usage)

```python
import requests

# Prepare files
with open("complaint.wav", "rb") as audio_file, \
     open("screenshot.png", "rb") as attachment_file:
    
    files = {
        "audio_file": ("complaint.wav", audio_file, "audio/wav"),
        "attachment_file": ("screenshot.png", attachment_file, "image/png")
    }
    
    data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "customer_phone": "+8801234567890",
        "attachment_description": "Error screenshot from mobile app"
    }
    
    response = requests.post(
        "http://localhost:8000/process/voice-with-attachment",
        files=files,
        data=data,
        timeout=180
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Ticket created: #{result['ticket']['id']}")
    else:
        print(f"Error: {response.text}")
```

## 🛠️ Configuration Requirements (Simplified)

### Environment Variables
```bash
# Required for voice processing
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Required for AI analysis
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./tickets.db
```

### Dependencies (Simplified)
```bash
# No additional dependencies required for image processing
# Gemini handles raw bytes directly
```

### Directory Structure
```
bangla-vai/
├── voices/          # Audio files storage
├── attachments/     # Attachment files storage
├── bengali_stt.py   # Voice processing
├── gemini_service.py # AI analysis (simplified)
├── fastapi_app.py   # API endpoints
├── streamlit_app.py # Main UI with voice + attachment feature
└── models.py        # Data models
```

## 🧪 Testing

### Test Script
Run the refactored test script:
```bash
python test_voice_attachment_feature.py
```

### Manual Testing
1. Start the FastAPI server: `python start_app.py`
2. Start the Streamlit app: `streamlit run streamlit_app.py`
3. Go to Tab 4: "🎤 Voice Complaint"
4. Click "🎤📎 Voice + Attachment" sub-tab
5. Test the enhanced voice+attachment workflow

### Test Data Requirements
- Place Bengali audio files in `voices/` directory
- Place test images in `attachments/` directory
- Ensure API keys are configured in environment

## 🔧 Refactoring Benefits

### Simplified Architecture
- **✅ No Pillow dependency** - Reduced complexity and installation requirements
- **✅ Direct byte processing** - Gemini handles raw image/document bytes
- **✅ Extended proven codebase** - Built on working streamlit_app.py foundation

### Improved Maintainability
- **✅ Single UI file** - All voice features in one cohesive interface
- **✅ Consistent patterns** - Follows same structure as existing voice complaint system
- **✅ Reduced dependencies** - Fewer external libraries to manage

### Better User Experience
- **✅ Familiar interface** - Users already know Tab 4 voice complaint system
- **✅ Progressive enhancement** - Voice + Attachment is natural extension
- **✅ Same performance** - No additional overhead from image processing

## 🚀 Deployment Considerations

### Performance
- Voice + attachment processing takes 30-60 seconds
- **Improved**: No image preprocessing overhead
- **Improved**: Direct memory processing (no temp files for images)

### Storage
- Both voice and attachment files are stored locally
- **Simplified**: Raw bytes sent directly to Gemini
- Monitor disk space usage

### API Rate Limits
- ElevenLabs Scribe API has monthly quota limits
- Google Gemini API has request rate limits
- **Improved**: Fewer API calls (no preprocessing steps)

## 🆘 Troubleshooting

### Common Issues

1. **"No speech detected in audio"**
   - Ensure audio file contains clear Bengali speech
   - Check audio quality and file format
   - Verify ElevenLabs API key is valid

2. **"Error analyzing attachment"**
   - Verify attachment file is a supported format
   - Check file size is reasonable (<10MB recommended)
   - Ensure Google API key has Gemini Vision access
   - **New**: No PIL/image processing errors

3. **"Timeout processing request"**
   - AI processing can take 30-60 seconds
   - **Improved**: Faster processing without image preprocessing

4. **"FastAPI server not running"**
   - Start server with: `python start_app.py`
   - Check server logs for errors
   - **Simplified**: Fewer dependencies to install

## 📞 Support

For technical support or feature requests:
1. Check the troubleshooting section above
2. Review API error messages for specific issues
3. Test with the provided test script: `python test_voice_attachment_feature.py`
4. Check server logs for detailed error information

---

**Version**: 2.0.0 (Refactored)  
**Last Updated**: December 2024  
**Compatibility**: Python 3.8+, FastAPI 0.104+, Streamlit 1.28+  
**Dependencies**: Standard requirements (no Pillow needed)