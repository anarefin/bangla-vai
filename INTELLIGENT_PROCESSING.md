# Intelligent Ticket Processing System

## Overview

This system implements an intelligent ticket processing pipeline following the specified pattern:

```python
def process_bengali_voice_input(transcribed_text):
    extracted_data = {
        'category': extract_category(transcribed_text),
        'priority': detect_urgency_keywords(transcribed_text),
        'product': identify_product_mentions(transcribed_text),
        'description': clean_and_format_description(transcribed_text)
    }
    return extracted_data
```

The system uses hard-coded values for POC (Proof of Concept) combined with AI analysis from Gemini for intelligent categorization and processing.

## Key Features

- **Pattern-based Processing**: Follows the exact pattern specified in requirements
- **Hard-coded Values**: Uses predefined categories, subcategories, priorities, and products for POC
- **AI Integration**: Leverages Gemini AI for Bengali text translation and analysis
- **Keyword Detection**: Intelligent Bengali keyword matching for categorization
- **Structured Output**: Provides comprehensive ticket data with formatted descriptions

## Hard-coded Values for POC

### Categories
- `technical` - Technical Issue
- `billing` - Billing Issue
- `general` - General Inquiry
- `complaint` - Customer Complaint
- `feature_request` - Feature Request
- `network` - Network Problem
- `device` - Device Issue
- `service` - Service Problem

### Priorities
- `low` - Low Priority
- `medium` - Medium Priority
- `high` - High Priority
- `urgent` - Urgent Priority
- `critical` - Critical Priority

### Products
- `internet` - Internet Service
- `mobile` - Mobile Service
- `tv` - Television Service
- `phone` - Phone Service
- `router` - Router/Modem
- `app` - Mobile App
- `website` - Website
- `general` - General Service

### Subcategories (by Category)
- **Technical**: Internet Connectivity, Device Configuration, Software Issue, Hardware Problem
- **Billing**: Payment Issue, Bill Dispute, Refund Request, Plan Change
- **General**: Information Request, Account Help, Service Inquiry, Other
- **Complaint**: Service Quality, Customer Service, Billing Dispute, Technical Problem
- **Feature Request**: New Feature, Enhancement, Integration Request, Custom Solution
- **Network**: Slow Speed, Connection Drop, No Internet, Poor Signal
- **Device**: Setup Help, Troubleshooting, Replacement, Configuration
- **Service**: Outage, Maintenance, Installation, Upgrade

## Usage

### 1. Basic Usage

```python
from intelligent_ticket_processor import get_intelligent_processor

# Initialize processor
processor = get_intelligent_processor()

# Process Bengali text
bengali_text = "আমার ইন্টারনেট কানেকশন খুবই ধীর হচ্ছে। দয়া করে দ্রুত সমাধান করুন।"
result = processor.process_bengali_voice_input(bengali_text)

# Access extracted data
print(f"Category: {result['category']}")
print(f"Subcategory: {result['subcategory']}")
print(f"Priority: {result['priority']}")
print(f"Product: {result['product']}")
print(f"Title: {result['title']}")
```

### 2. API Integration

The system is integrated into the FastAPI application:

- **Main Endpoint**: `/process/voice-complaint` - Full voice-to-ticket pipeline
- **Test Endpoint**: `/process/intelligent-analysis` - Test processing with Bengali text

### 3. Testing

Run the test script to see the system in action:

```bash
python test_intelligent_processing.py
```

## Processing Pipeline

### 1. AI Analysis
- Uses Gemini AI to translate Bengali text to English
- Extracts key points and sentiment analysis
- Provides initial categorization suggestions

### 2. Pattern-based Extraction
- `extract_category()`: Determines ticket category using AI + keyword matching
- `extract_subcategory()`: Maps to specific subcategory based on main category
- `detect_urgency_keywords()`: Analyzes urgency indicators for priority assignment
- `identify_product_mentions()`: Identifies relevant product/service mentions
- `clean_and_format_description()`: Creates structured, professional description

### 3. Output Structure

```python
{
    'category': 'technical',           # Main category
    'subcategory': 'Internet Connectivity',  # Specific subcategory
    'priority': 'high',               # Urgency level
    'product': 'internet',            # Related product/service
    'title': 'Technical Issue - Internet Service',  # Generated title
    'description': '...',             # Formatted description
    'keywords': ['ইন্টারনেট', 'সমস্যা'],  # Extracted Bengali keywords
    'sentiment': 'negative',          # Customer sentiment
    'urgency_indicators': ['দ্রুত'],   # Urgency keywords found
    'ai_analysis': {...}              # Full AI analysis data
}
```

## Bengali Keyword Mapping

### Technical Keywords
- ইন্টারনেট (Internet), নেটওয়ার্ক (Network), কানেকশন (Connection)
- স্পিড (Speed), রাউটার (Router), মডেম (Modem), ওয়াইফাই (WiFi)

### Billing Keywords
- বিল (Bill), পেমেন্ট (Payment), টাকা (Money), চার্জ (Charge)
- রিচার্জ (Recharge), রিফান্ড (Refund)

### Urgency Keywords
- জরুরি (Urgent), দ্রুত (Quick), তাড়াতাড়ি (Hurry)
- এখনি (Now), অবিলম্বে (Immediately)

### Complaint Keywords
- অভিযোগ (Complaint), সমস্যা (Problem), খারাপ (Bad)
- বন্ধ (Closed/Stopped), কাজ করছে না (Not working)

## Database Integration

The system updates the database schema to include:
- `subcategory` field for storing POC subcategory
- `product` field for storing identified product/service
- These fields are populated automatically during ticket creation

## API Endpoints

### Process Voice Complaint
```
POST /process/voice-complaint
```
- Uploads Bengali audio file
- Transcribes using ElevenLabs STT
- Processes with intelligent analyzer
- Creates ticket with extracted data

### Test Intelligent Analysis
```
POST /process/intelligent-analysis
```
- Tests processing with Bengali text
- Shows hard-coded values
- Demonstrates extraction results

## Example Results

### Input
```
"আমার ইন্টারনেট কানেকশন খুবই ধীর হচ্ছে। কয়েকদিন ধরে এই সমস্যা হচ্ছে। দয়া করে দ্রুত সমাধান করুন।"
```

### Output
```python
{
    'category': 'technical',
    'subcategory': 'Internet Connectivity',
    'priority': 'high',
    'product': 'internet',
    'title': 'Slow Internet Connection Issue',
    'description': 'Structured complaint with Bengali original and English translation',
    'keywords': ['ইন্টারনেট', 'কানেকশন', 'সমস্যা', 'দ্রুত'],
    'sentiment': 'negative',
    'urgency_indicators': ['দ্রুত']
}
```

## Benefits

1. **Consistent Categorization**: Hard-coded values ensure consistent ticket classification
2. **AI Enhancement**: Gemini provides intelligent translation and analysis
3. **Pattern Compliance**: Follows the exact pattern specified in requirements
4. **Scalable**: Easy to extend with more categories, products, and keywords
5. **Multilingual**: Handles Bengali input with English output for support teams

## Configuration

Required environment variables:
- `GOOGLE_API_KEY`: For Gemini AI integration
- `ELEVENLABS_API_KEY`: For Bengali speech-to-text (if using voice input)

## Future Enhancements

1. **Dynamic Categories**: Load categories from database instead of hard-coding
2. **Machine Learning**: Train models on historical ticket data
3. **Advanced NLP**: Use specialized Bengali NLP models
4. **Custom Rules**: Allow configuration of keyword mappings
5. **Analytics**: Track categorization accuracy and adjust rules

This system provides a solid foundation for intelligent ticket processing while maintaining the simplicity needed for a POC implementation. 