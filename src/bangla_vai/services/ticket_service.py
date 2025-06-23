import os
import json
import re
from typing import Dict, Any, List
from .ai_service import get_gemini_processor

# Hard-coded constants for POC
CATEGORIES = {
    'technical': 'Technical Issue',
    'billing': 'Billing Issue', 
    'general': 'General Inquiry',
    'complaint': 'Customer Complaint',
    'feature_request': 'Feature Request',
    'network': 'Network Problem',
    'device': 'Device Issue',
    'service': 'Service Problem'
}

SUBCATEGORIES = {
    'technical': ['Internet Connectivity', 'Device Configuration', 'Software Issue', 'Hardware Problem'],
    'billing': ['Payment Issue', 'Bill Dispute', 'Refund Request', 'Plan Change'],
    'general': ['Information Request', 'Account Help', 'Service Inquiry', 'Other'],
    'complaint': ['Service Quality', 'Customer Service', 'Billing Dispute', 'Technical Problem'],
    'feature_request': ['New Feature', 'Enhancement', 'Integration Request', 'Custom Solution'],
    'network': ['Slow Speed', 'Connection Drop', 'No Internet', 'Poor Signal'],
    'device': ['Setup Help', 'Troubleshooting', 'Replacement', 'Configuration'],
    'service': ['Outage', 'Maintenance', 'Installation', 'Upgrade']
}

PRIORITIES = {
    'low': 'Low Priority',
    'medium': 'Medium Priority', 
    'high': 'High Priority',
    'urgent': 'Urgent Priority',
    'critical': 'Critical Priority'
}

PRODUCTS = {
    'internet': 'Internet Service',
    'mobile': 'Mobile Service',
    'tv': 'Television Service',
    'phone': 'Phone Service',
    'router': 'Router/Modem',
    'app': 'Mobile App',
    'website': 'Website',
    'general': 'General Service'
}

class IntelligentTicketProcessor:
    """
    Intelligent ticket processor following the specified pattern:
    def process_bengali_voice_input(transcribed_text):
        extracted_data = {
            'category': extract_category(transcribed_text),
            'priority': detect_urgency_keywords(transcribed_text),
            'product': identify_product_mentions(transcribed_text),
            'description': clean_and_format_description(transcribed_text)
        }
        return extracted_data
    """
    
    def __init__(self):
        self.gemini_processor = get_gemini_processor()
    
    def process_bengali_voice_input(self, transcribed_text: str) -> Dict[str, Any]:
        """
        Main processing function following the specified pattern
        
        Args:
            transcribed_text (str): Bengali transcribed text from voice input
            
        Returns:
            Dict containing extracted ticket data
        """
        try:
            # First get AI analysis from Gemini
            ai_analysis = self.gemini_processor.process_bengali_complaint(transcribed_text)
            
            # Extract structured data following the pattern
            extracted_data = {
                'category': self.extract_category(transcribed_text, ai_analysis),
                'subcategory': self.extract_subcategory(transcribed_text, ai_analysis),
                'priority': self.detect_urgency_keywords(transcribed_text, ai_analysis),
                'product': self.identify_product_mentions(transcribed_text, ai_analysis),
                'description': self.clean_and_format_description(transcribed_text, ai_analysis),
                'title': self.generate_ticket_title(transcribed_text, ai_analysis),
                'ai_analysis': ai_analysis,  # Include full AI analysis
                'keywords': self.extract_keywords(transcribed_text),
                'sentiment': ai_analysis.get('sentiment', 'neutral'),
                'urgency_indicators': ai_analysis.get('urgency_indicators', [])
            }
            
            return extracted_data
            
        except Exception as e:
            print(f"Error in intelligent processing: {str(e)}")
            # Return fallback structure
            return self._get_fallback_data(transcribed_text)
    
    def extract_category(self, transcribed_text: str, ai_analysis: Dict[str, Any]) -> str:
        """
        Extract category from transcribed text using AI analysis and keyword matching
        
        For POC, we use hard-coded category mapping with AI assistance
        """
        # Get AI suggested category
        ai_category = ai_analysis.get('category', 'general').lower()
        
        # Validate against our hard-coded categories
        if ai_category in CATEGORIES:
            return ai_category
        
        # Fallback: keyword-based category detection
        text_lower = transcribed_text.lower()
        
        # Technical keywords
        technical_keywords = ['ইন্টারনেট', 'নেটওয়ার্ক', 'কানেকশন', 'স্পিড', 'রাউটার', 'মডেম', 'ওয়াইফাই']
        if any(keyword in text_lower for keyword in technical_keywords):
            return 'technical'
        
        # Billing keywords
        billing_keywords = ['বিল', 'পেমেন্ট', 'টাকা', 'চার্জ', 'রিচার্জ', 'রিফান্ড']
        if any(keyword in text_lower for keyword in billing_keywords):
            return 'billing'
        
        # Complaint keywords
        complaint_keywords = ['অভিযোগ', 'সমস্যা', 'খারাপ', 'বন্ধ', 'কাজ করছে না']
        if any(keyword in text_lower for keyword in complaint_keywords):
            return 'complaint'
        
        return 'general'  # Default fallback
    
    def extract_subcategory(self, transcribed_text: str, ai_analysis: Dict[str, Any]) -> str:
        """
        Extract subcategory based on main category and content analysis
        """
        category = self.extract_category(transcribed_text, ai_analysis)
        
        # Get available subcategories for the main category
        available_subcategories = SUBCATEGORIES.get(category, ['Other'])
        
        text_lower = transcribed_text.lower()
        
        # Map keywords to subcategories based on category
        if category == 'technical':
            if any(word in text_lower for word in ['ইন্টারনেট', 'কানেকশন', 'নেট']):
                return 'Internet Connectivity'
            elif any(word in text_lower for word in ['রাউটার', 'মডেম', 'ডিভাইস']):
                return 'Device Configuration'
            elif any(word in text_lower for word in ['সফটওয়্যার', 'অ্যাপ']):
                return 'Software Issue'
            else:
                return 'Hardware Problem'
        
        elif category == 'billing':
            if any(word in text_lower for word in ['পেমেন্ট', 'পে']):
                return 'Payment Issue'
            elif any(word in text_lower for word in ['রিফান্ড', 'ফেরত']):
                return 'Refund Request'
            elif any(word in text_lower for word in ['প্ল্যান', 'প্যাকেজ']):
                return 'Plan Change'
            else:
                return 'Bill Dispute'
        
        # Return first available subcategory as default
        return available_subcategories[0]
    
    def detect_urgency_keywords(self, transcribed_text: str, ai_analysis: Dict[str, Any]) -> str:
        """
        Detect urgency level from keywords and AI analysis
        
        For POC, we use hard-coded priority mapping
        """
        # Get AI suggested priority
        ai_priority = ai_analysis.get('priority', 'medium').lower()
        
        # Validate against our hard-coded priorities
        if ai_priority in PRIORITIES:
            suggested_priority = ai_priority
        else:
            suggested_priority = 'medium'
        
        # Override with keyword-based urgency detection
        text_lower = transcribed_text.lower()
        urgency_indicators = ai_analysis.get('urgency_indicators', [])
        
        # Critical/Urgent keywords
        critical_keywords = ['জরুরি', 'দ্রুত', 'তাড়াতাড়ি', 'এখনি', 'অবিলম্বে', 'খুব সমস্যা']
        if any(keyword in text_lower for keyword in critical_keywords) or len(urgency_indicators) > 2:
            return 'urgent'
        
        # High priority keywords
        high_keywords = ['সমস্যা', 'বন্ধ', 'কাজ করছে না', 'খারাপ']
        if any(keyword in text_lower for keyword in high_keywords):
            return 'high'
        
        # Low priority keywords
        low_keywords = ['জানতে চাই', 'তথ্য', 'জিজ্ঞাসা', 'জানার জন্য']
        if any(keyword in text_lower for keyword in low_keywords):
            return 'low'
        
        return suggested_priority
    
    def identify_product_mentions(self, transcribed_text: str, ai_analysis: Dict[str, Any]) -> str:
        """
        Identify product/service mentions in the text
        
        For POC, we use hard-coded product mapping
        """
        text_lower = transcribed_text.lower()
        
        # Internet service keywords
        internet_keywords = ['ইন্টারনেট', 'নেট', 'ব্রডব্যান্ড', 'ওয়াইফাই', 'wifi']
        if any(keyword in text_lower for keyword in internet_keywords):
            return 'internet'
        
        # Mobile service keywords  
        mobile_keywords = ['মোবাইল', 'ফোন', 'সিম', 'কল', 'এসএমএস']
        if any(keyword in text_lower for keyword in mobile_keywords):
            return 'mobile'
        
        # TV service keywords
        tv_keywords = ['টিভি', 'টেলিভিশন', 'চ্যানেল']
        if any(keyword in text_lower for keyword in tv_keywords):
            return 'tv'
        
        # Router/Device keywords
        router_keywords = ['রাউটার', 'মডেম', 'ডিভাইস']
        if any(keyword in text_lower for keyword in router_keywords):
            return 'router'
        
        # App keywords
        app_keywords = ['অ্যাপ', 'অ্যাপ্লিকেশন', 'মোবাইল অ্যাপ']
        if any(keyword in text_lower for keyword in app_keywords):
            return 'app'
        
        # Website keywords
        website_keywords = ['ওয়েবসাইট', 'সাইট', 'ওয়েব']
        if any(keyword in text_lower for keyword in website_keywords):
            return 'website'
        
        return 'general'  # Default fallback
    
    def clean_and_format_description(self, transcribed_text: str, ai_analysis: Dict[str, Any]) -> str:
        """
        Clean and format the description for better readability
        """
        # Get enhanced description from AI
        english_translation = ai_analysis.get('english_translation', '')
        key_points = ai_analysis.get('key_points', [])
        
        # Create a structured description
        formatted_description = f"""
**Original Complaint (Bengali):**
{transcribed_text.strip()}

**English Translation:**
{english_translation}

**Key Issues Identified:**
{self._format_key_points(key_points)}

**Customer Sentiment:** {ai_analysis.get('sentiment', 'neutral').title()}
"""
        
        return formatted_description.strip()
    
    def generate_ticket_title(self, transcribed_text: str, ai_analysis: Dict[str, Any]) -> str:
        """
        Generate a concise and descriptive ticket title
        """
        ai_title = ai_analysis.get('title', '')
        
        if ai_title and len(ai_title.strip()) > 5:
            return ai_title[:100]  # Limit to 100 characters
        
        # Fallback title generation
        category = self.extract_category(transcribed_text, ai_analysis)
        product = self.identify_product_mentions(transcribed_text, ai_analysis)
        
        category_label = CATEGORIES.get(category, 'General Issue')
        product_label = PRODUCTS.get(product, 'Service')
        
        return f"{category_label} - {product_label}"
    
    def extract_keywords(self, transcribed_text: str) -> List[str]:
        """
        Extract important keywords from the Bengali text
        """
        # Common Bengali stopwords to exclude
        stopwords = ['এর', 'এবং', 'বা', 'যে', 'যা', 'এক', 'একটি', 'দিয়ে', 'থেকে', 'এই', 'সেই']
        
        # Simple keyword extraction (in real implementation, you might use more sophisticated NLP)
        words = re.findall(r'\b[\u0980-\u09FF]+\b', transcribed_text)
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        # Return unique keywords, limited to 10
        return list(set(keywords))[:10]
    
    def _format_key_points(self, key_points: List[str]) -> str:
        """Format key points as a bulleted list"""
        if not key_points:
            return "No specific issues identified."
        
        return '\n'.join([f"• {point}" for point in key_points])
    
    def _get_fallback_data(self, transcribed_text: str) -> Dict[str, Any]:
        """Return fallback data structure when processing fails"""
        return {
            'category': 'general',
            'subcategory': 'Other',
            'priority': 'medium',
            'product': 'general',
            'description': f"**Original Complaint (Bengali):**\n{transcribed_text}\n\n**Note:** Automatic processing failed, manual review required.",
            'title': 'Voice Complaint - Manual Review Required',
            'ai_analysis': {},
            'keywords': [],
            'sentiment': 'neutral',
            'urgency_indicators': []
        }

# Global instance for reuse
intelligent_processor = None

def get_intelligent_processor():
    """Get or create intelligent processor instance"""
    global intelligent_processor
    if intelligent_processor is None:
        intelligent_processor = IntelligentTicketProcessor()
    return intelligent_processor

# For testing
if __name__ == "__main__":
    processor = IntelligentTicketProcessor()
    
    # Test Bengali text
    test_text = "আমার ইন্টারনেট কানেকশন খুবই ধীর হচ্ছে। কয়েকদিন ধরে এই সমস্যা হচ্ছে। দয়া করে দ্রুত সমাধান করুন।"
    
    result = processor.process_bengali_voice_input(test_text)
    
    print("Intelligent Processing Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False)) 