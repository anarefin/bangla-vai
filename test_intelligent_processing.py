#!/usr/bin/env python3
"""
Test script for the Intelligent Ticket Processing System
Demonstrates the pattern-based processing with hard-coded values for POC

Usage: python test_intelligent_processing.py
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from intelligent_ticket_processor import get_intelligent_processor, CATEGORIES, PRIORITIES, PRODUCTS, SUBCATEGORIES
except ImportError as e:
    print(f"Error importing intelligent_ticket_processor: {e}")
    print("Make sure you have all required dependencies installed and GOOGLE_API_KEY configured")
    sys.exit(1)

def test_bengali_examples():
    """Test the intelligent processing with various Bengali examples"""
    
    # Test examples covering different scenarios
    test_cases = [
        {
            "name": "Internet Connectivity Issue (Technical)",
            "bengali_text": "আমার ইন্টারনেট কানেকশন খুবই ধীর হচ্ছে। কয়েকদিন ধরে এই সমস্যা হচ্ছে। দয়া করে দ্রুত সমাধান করুন।",
            "expected_category": "technical",
            "expected_priority": "high"
        },
        {
            "name": "Billing Issue",
            "bengali_text": "আমার গত মাসের বিল ভুল এসেছে। আমি যে প্যাকেজ নিয়েছি সেটার চেয়ে বেশি টাকা কাটা হয়েছে। এটা ঠিক করুন।",
            "expected_category": "billing",
            "expected_priority": "medium"
        },
        {
            "name": "Urgent Router Problem",
            "bengali_text": "আমার রাউটার কাজ করছে না। একদম বন্ধ হয়ে গেছে। অফিসের কাজ আছে, জরুরি সমাধান দরকার।",
            "expected_category": "technical",
            "expected_priority": "urgent"
        },
        {
            "name": "Mobile Service Complaint",
            "bengali_text": "মোবাইলে কল করতে পারছি না। নেটওয়ার্ক সিগন্যাল খুবই খারাপ। এটা ঠিক করুন।",
            "expected_category": "complaint",
            "expected_priority": "high"
        },
        {
            "name": "General Information Request",
            "bengali_text": "আমি নতুন একটা প্যাকেজের তথ্য জানতে চাই। কি কি প্যাকেজ আছে এবং দাম কত?",
            "expected_category": "general",
            "expected_priority": "low"
        }
    ]
    
    processor = get_intelligent_processor()
    
    print("="*80)
    print("INTELLIGENT TICKET PROCESSING SYSTEM - TEST RESULTS")
    print("="*80)
    print(f"Available Categories: {list(CATEGORIES.keys())}")
    print(f"Available Priorities: {list(PRIORITIES.keys())}")
    print(f"Available Products: {list(PRODUCTS.keys())}")
    print("="*80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[TEST CASE {i}] {test_case['name']}")
        print("-" * 60)
        print(f"Input: {test_case['bengali_text']}")
        print()
        
        try:
            # Process the Bengali text
            result = processor.process_bengali_voice_input(test_case['bengali_text'])
            
            # Display extracted data
            print("📊 EXTRACTED DATA:")
            print(f"   Category: {result['category']} ({'✅' if result['category'] == test_case['expected_category'] else '❌'})")
            print(f"   Subcategory: {result['subcategory']}")
            print(f"   Priority: {result['priority']} ({'✅' if result['priority'] == test_case['expected_priority'] else '❌'})")
            print(f"   Product: {result['product']}")
            print(f"   Title: {result['title']}")
            print(f"   Keywords: {result['keywords']}")
            print(f"   Sentiment: {result['sentiment']}")
            print(f"   Urgency Indicators: {result['urgency_indicators']}")
            
            print("\n🤖 AI ANALYSIS:")
            ai_analysis = result['ai_analysis']
            print(f"   English Translation: {ai_analysis.get('english_translation', 'N/A')}")
            print(f"   AI Category: {ai_analysis.get('category', 'N/A')}")
            print(f"   AI Priority: {ai_analysis.get('priority', 'N/A')}")
            print(f"   Key Points: {ai_analysis.get('key_points', [])}")
            
            print("\n📝 FORMATTED DESCRIPTION:")
            description_lines = result['description'].split('\n')[:3]  # Show first 3 lines
            for line in description_lines:
                if line.strip():
                    print(f"   {line}")
            print("   ...")
            
        except Exception as e:
            print(f"❌ Error processing: {str(e)}")
        
        print("-" * 60)
    
    print("\n" + "="*80)
    print("PROCESSING PATTERN DEMONSTRATION")
    print("="*80)
    print("Following the specified pattern:")
    print("extracted_data = {")
    print("    'category': extract_category(transcribed_text),")
    print("    'priority': detect_urgency_keywords(transcribed_text),")
    print("    'product': identify_product_mentions(transcribed_text),")
    print("    'description': clean_and_format_description(transcribed_text)")
    print("}")
    print("="*80)

def demonstrate_hard_coded_values():
    """Demonstrate the hard-coded values used for POC"""
    print("\n" + "="*80)
    print("HARD-CODED VALUES FOR POC")
    print("="*80)
    
    print("\n📂 CATEGORIES:")
    for key, value in CATEGORIES.items():
        print(f"   {key} → {value}")
    
    print("\n📊 PRIORITIES:")
    for key, value in PRIORITIES.items():
        print(f"   {key} → {value}")
    
    print("\n🔧 PRODUCTS:")
    for key, value in PRODUCTS.items():
        print(f"   {key} → {value}")
    
    print("\n📋 SUBCATEGORIES:")
    for category, subcats in SUBCATEGORIES.items():
        print(f"   {category}:")
        for subcat in subcats:
            print(f"     - {subcat}")
    
    print("="*80)

if __name__ == "__main__":
    try:
        print("Starting Intelligent Ticket Processing System Test...")
        
        # Check if required environment variables are set
        if not os.getenv("GOOGLE_API_KEY"):
            print("⚠️  Warning: GOOGLE_API_KEY not found in environment variables")
            print("   Some AI features may not work properly")
        
        # Run tests
        test_bengali_examples()
        demonstrate_hard_coded_values()
        
        print("\n✅ Test completed successfully!")
        print("\nTo use this in your application:")
        print("1. Import: from intelligent_ticket_processor import get_intelligent_processor")
        print("2. Create: processor = get_intelligent_processor()")
        print("3. Process: result = processor.process_bengali_voice_input(bengali_text)")
        
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc() 