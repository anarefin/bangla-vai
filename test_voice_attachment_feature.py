#!/usr/bin/env python3
"""
Test script for the Voice + Attachment Ticketing Feature
This script demonstrates how to create tickets using Bengali voice + attachment files.
"""

import requests
import json
import os
from pathlib import Path
import time

FASTAPI_BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Test if the FastAPI server is running"""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI server is running")
            return True
        else:
            print(f"❌ FastAPI server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to FastAPI server: {e}")
        return False

def test_voice_only_endpoint():
    """Test the original voice-only endpoint"""
    print("\n🎤 Testing Voice-Only Endpoint...")
    
    # Check for audio files in voices directory
    voices_dir = Path("voices")
    if not voices_dir.exists():
        print("❌ No voices directory found")
        return
    
    audio_files = list(voices_dir.glob("*.wav")) + list(voices_dir.glob("*.mp3"))
    if not audio_files:
        print("❌ No audio files found in voices directory")
        return
    
    # Use the first audio file found
    audio_file = audio_files[0]
    print(f"📁 Using audio file: {audio_file.name}")
    
    try:
        with open(audio_file, "rb") as f:
            files = {"file": (audio_file.name, f, "audio/mpeg")}
            data = {
                "customer_name": "Test Customer Voice",
                "customer_email": "test.voice@example.com",
                "customer_phone": "+8801234567890"
            }
            
            response = requests.post(
                f"{FASTAPI_BASE_URL}/process/voice-complaint",
                files=files,
                data=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Voice-only ticket created successfully!")
                print(f"🎫 Ticket ID: #{result['ticket']['id']}")
                print(f"📝 Title: {result['ticket']['title']}")
                print(f"📊 Category: {result['ticket']['category']}")
                print(f"🔥 Priority: {result['ticket']['priority']}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"❌ Error testing voice endpoint: {e}")

def test_voice_attachment_endpoint():
    """Test the new voice + attachment endpoint"""
    print("\n🎤📎 Testing Voice + Attachment Endpoint...")
    
    # Check for audio files
    voices_dir = Path("voices")
    audio_files = []
    if voices_dir.exists():
        audio_files = list(voices_dir.glob("*.wav")) + list(voices_dir.glob("*.mp3"))
    
    if not audio_files:
        print("❌ No audio files found in voices directory")
        return
    
    # Check for attachment files
    attachments_dir = Path("attachments")
    attachment_files = []
    if attachments_dir.exists():
        attachment_files = (list(attachments_dir.glob("*.png")) + 
                          list(attachments_dir.glob("*.jpg")) + 
                          list(attachments_dir.glob("*.jpeg")))
    
    # If no attachments, look for any image in current directory
    if not attachment_files:
        current_dir = Path(".")
        attachment_files = (list(current_dir.glob("*.png")) + 
                          list(current_dir.glob("*.jpg")) + 
                          list(current_dir.glob("*.jpeg")))
    
    if not attachment_files:
        print("❌ No image attachment files found")
        print("💡 Please place a PNG, JPG, or JPEG file in the attachments/ directory or current directory")
        return
    
    # Use the first files found
    audio_file = audio_files[0]
    attachment_file = attachment_files[0]
    
    print(f"📁 Using audio file: {audio_file.name}")
    print(f"📎 Using attachment file: {attachment_file.name}")
    
    try:
        with open(audio_file, "rb") as af, open(attachment_file, "rb") as atf:
            files = {
                "audio_file": (audio_file.name, af, "audio/mpeg"),
                "attachment_file": (attachment_file.name, atf, "image/jpeg")
            }
            data = {
                "customer_name": "Test Customer Enhanced",
                "customer_email": "test.enhanced@example.com",
                "customer_phone": "+8801234567891",
                "attachment_description": f"Test attachment - {attachment_file.name}"
            }
            
            print("🤖 Processing with AI... (this may take 30-60 seconds)")
            response = requests.post(
                f"{FASTAPI_BASE_URL}/process/voice-with-attachment",
                files=files,
                data=data,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Enhanced ticket created successfully!")
                print(f"🎫 Ticket ID: #{result['ticket']['id']}")
                print(f"📝 Enhanced Title: {result['ticket']['title']}")
                print(f"📊 Category: {result['ticket']['category']}")
                print(f"🔥 Priority: {result['ticket']['priority']}")
                
                # Show enhanced analysis
                print("\n🤖 AI Analysis Results:")
                print(f"🎤 Bengali Text: {result['bengali_text'][:100]}...")
                print(f"🌍 English Translation: {result['english_translation'][:100]}...")
                
                attachment_analysis = result.get('attachment_analysis', {})
                if attachment_analysis:
                    print(f"📎 Attachment Type: {attachment_analysis.get('type', 'Unknown')}")
                    print(f"📄 Content: {attachment_analysis.get('content_description', 'No description')[:100]}...")
                
                correlation = result.get('voice_image_correlation', {})
                if correlation:
                    print(f"🔗 Correlation: {correlation.get('relationship', 'No analysis')[:100]}...")
                
                tech_assessment = result.get('technical_assessment', {})
                if tech_assessment:
                    print(f"🔧 Technical Issue: {tech_assessment.get('is_technical_issue', False)}")
                
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"❌ Error testing voice + attachment endpoint: {e}")

def list_recent_tickets():
    """List recent tickets to see our test results"""
    print("\n📋 Recent Tickets:")
    
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/tickets?limit=5", timeout=30)
        if response.status_code == 200:
            result = response.json()
            tickets = result.get("tickets", [])
            
            if tickets:
                for ticket in tickets:
                    ticket_type = ""
                    if ticket.get('audio_file_path') and ticket.get('attachment_file_path'):
                        ticket_type = "🎤📎"
                    elif ticket.get('audio_file_path'):
                        ticket_type = "🎤"
                    elif ticket.get('attachment_file_path'):
                        ticket_type = "📎"
                    else:
                        ticket_type = "📝"
                    
                    print(f"🎫 #{ticket['id']} {ticket_type} {ticket['title'][:50]}...")
                    print(f"   📊 {ticket['category']} | 🔥 {ticket['priority']} | 👤 {ticket['customer_name']}")
            else:
                print("No tickets found")
        else:
            print(f"❌ Error listing tickets: {response.status_code}")
    except Exception as e:
        print(f"❌ Error listing tickets: {e}")

def main():
    """Main test function"""
    print("🎫 Voice + Attachment Ticketing Feature Test (Refactored)")
    print("=" * 60)
    
    # Test API connection
    if not test_api_connection():
        print("\n💡 Make sure to start the FastAPI server with: python start_app.py")
        return
    
    # Test endpoints
    test_voice_only_endpoint()
    time.sleep(2)  # Brief pause
    test_voice_attachment_endpoint()
    time.sleep(2)  # Brief pause
    list_recent_tickets()
    
    print("\n✅ Testing completed!")
    print("\n💡 To use the feature:")
    print("1. Start the Streamlit app: streamlit run streamlit_app.py")
    print("2. Go to the 'Voice Complaint' tab")
    print("3. Click on the '🎤📎 Voice + Attachment' sub-tab")
    print("4. Upload both voice and attachment files")
    print("5. Fill in customer details and create ticket")
    print("\n🔧 Changes made:")
    print("- ✅ Removed Pillow dependency (Gemini handles raw bytes)")
    print("- ✅ Extended existing streamlit_app.py instead of separate file")
    print("- ✅ Follows same patterns as working voice complaint system")

if __name__ == "__main__":
    main() 