import google.generativeai as genai
import os
import json
import re
from typing import Dict, Any, Optional, Tuple
from langchain.schema import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class GeminiTicketProcessor:
    def __init__(self):
        """Initialize Gemini AI client for Bengali text processing"""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize the model (using latest Gemini 2.5 models)
        # Try multiple model names for compatibility - prioritize 2.5 over 1.5
        self.model_names = [
            'models/gemini-2.5-flash',           # Latest stable 2.5 Flash
            'models/gemini-2.5-pro',             # Latest stable 2.5 Pro
            'models/gemini-2.5-flash-preview-05-20', # Preview version
            'models/gemini-2.0-flash',           # Fallback to 2.0
            'models/gemini-1.5-flash',           # Fallback to 1.5 if needed
            'models/gemini-1.5-pro',             # Last resort 1.5
        ]
        self.model = None
        self.model_name = None
        
        for model_name in self.model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                self.model_name = model_name
                print(f"✅ Successfully initialized Gemini model: {model_name}")
                break
            except Exception as e:
                print(f"❌ Failed to initialize model {model_name}: {str(e)}")
                continue
        
        if not self.model:
            raise ValueError("❌ No valid Gemini model could be initialized. Check your API key and quota.")
        
        # Initialize LangChain model
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.3
        )
    
    def process_bengali_complaint(self, bengali_text: str) -> Dict[str, Any]:
        """
        Process Bengali complaint text and extract structured information
        
        Args:
            bengali_text (str): Bengali complaint text
            
        Returns:
            Dict containing structured ticket information
        """
        try:
            # First, translate and understand the Bengali text
            translation_prompt = f"""
            You are an expert Bengali language translator and customer service analyst.
            
            Please analyze the following Bengali complaint/issue description and provide:
            1. English translation
            2. Issue category (technical, billing, general, complaint, feature_request)
            3. Priority level (low, medium, high, urgent)
            4. Brief title/summary
            5. Key details extracted
            
            Bengali Text: {bengali_text}
            
            Please respond in the following JSON format:
            {{
                "english_translation": "Complete English translation",
                "title": "Brief descriptive title",
                "category": "one of: technical, billing, general, complaint, feature_request",
                "priority": "one of: low, medium, high, urgent",
                "key_points": ["list", "of", "key", "issues"],
                "sentiment": "positive/negative/neutral",
                "urgency_indicators": ["any", "urgent", "words", "found"]
            }}
            """
            
            response = self.model.generate_content(translation_prompt)
            
            # Parse the response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback parsing
                    result = self._parse_fallback_response(response.text, bengali_text)
                
                # Validate and clean the result
                result = self._validate_and_clean_result(result)
                
                return result
                
            except json.JSONDecodeError:
                # Fallback parsing if JSON fails
                return self._parse_fallback_response(response.text, bengali_text)
                
        except Exception as e:
            print(f"Error processing Bengali text with Gemini: {str(e)}")
            # Return a basic fallback result
            return {
                "english_translation": f"Error translating: {bengali_text}",
                "title": "Voice Complaint",
                "category": "general",
                "priority": "medium",
                "key_points": ["Processing error occurred"],
                "sentiment": "neutral",
                "urgency_indicators": []
            }
    
    def _parse_fallback_response(self, response_text: str, original_bengali: str) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails"""
        return {
            "english_translation": response_text[:500] if response_text else original_bengali,
            "title": "Voice-based Ticket",
            "category": "general",
            "priority": "medium",
            "key_points": ["Voice complaint submitted"],
            "sentiment": "neutral",
            "urgency_indicators": []
        }
    
    def _validate_and_clean_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the AI response"""
        # Valid categories and priorities
        valid_categories = {"technical", "billing", "general", "complaint", "feature_request"}
        valid_priorities = {"low", "medium", "high", "urgent"}
        
        # Ensure all required fields exist with defaults
        cleaned_result = {
            "english_translation": result.get("english_translation", "Translation not available"),
            "title": result.get("title", "Voice Complaint")[:200],  # Limit title length
            "category": self._map_category_to_enum(result.get("category", "general")),
            "priority": self._map_priority_to_enum(result.get("priority", "medium")),
            "key_points": result.get("key_points", []),
            "sentiment": result.get("sentiment", "neutral"),
            "urgency_indicators": result.get("urgency_indicators", [])
        }
        
        # Additional validation (redundant but safe)
        if cleaned_result["category"] not in valid_categories:
            cleaned_result["category"] = "general"
        
        if cleaned_result["priority"] not in valid_priorities:
            cleaned_result["priority"] = "medium"
        
        # Ensure key_points is a list
        if not isinstance(cleaned_result["key_points"], list):
            cleaned_result["key_points"] = [str(cleaned_result["key_points"])]
        
        return cleaned_result
    
    def enhance_ticket_description(self, english_translation: str, key_points: list) -> str:
        """Create an enhanced description for the ticket"""
        try:
            enhancement_prompt = f"""
            Based on the following customer complaint translation and key points, create a clear, 
            professional ticket description that a customer service representative can easily understand and act upon.
            
            Translation: {english_translation}
            Key Points: {', '.join(key_points)}
            
            Please provide a well-structured ticket description that includes:
            1. Clear problem statement
            2. Any specific details mentioned
            3. Suggested next steps or areas to investigate
            
            Keep it concise but comprehensive.
            """
            
            response = self.model.generate_content(enhancement_prompt)
            return response.text
            
        except Exception as e:
            print(f"Error enhancing description: {str(e)}")
            # Return the basic translation as fallback
            return english_translation
    
    def suggest_resolution_steps(self, ticket_info: Dict[str, Any]) -> list:
        """Suggest potential resolution steps based on ticket information"""
        try:
            resolution_prompt = f"""
            Based on this customer complaint, suggest 3-5 specific resolution steps for customer service:
            
            Category: {ticket_info.get('category')}
            Priority: {ticket_info.get('priority')}
            Description: {ticket_info.get('english_translation')}
            Key Issues: {', '.join(ticket_info.get('key_points', []))}
            
            Provide a numbered list of actionable steps.
            """
            
            response = self.model.generate_content(resolution_prompt)
            
            # Extract numbered steps from response
            steps = []
            lines = response.text.split('\n')
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+\.', line):
                    steps.append(line)
            
            return steps[:5]  # Limit to 5 steps
            
        except Exception as e:
            print(f"Error generating resolution steps: {str(e)}")
            return ["Review complaint details", "Contact customer for clarification", "Escalate if necessary"]
    
    def list_available_models(self):
        """List all available Gemini models for debugging"""
        try:
            models = genai.list_models()
            available_models = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name)
            return available_models
        except Exception as e:
            print(f"Error listing models: {str(e)}")
            return []

    def analyze_attachment_with_voice(self, attachment_bytes: bytes, attachment_filename: str, voice_text: str, voice_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an attachment (image/screenshot) in context of the voice complaint
        
        Args:
            attachment_bytes (bytes): Raw bytes of the attachment file
            attachment_filename (str): Name of the attachment file
            voice_text (str): Bengali voice text
            voice_analysis (dict): Previous voice analysis result
            
        Returns:
            Dict containing combined analysis
        """
        try:
            # Create a comprehensive prompt that combines voice and visual context
            combined_prompt = f"""
            You are analyzing a customer support ticket that includes both voice complaint and visual evidence.
            
            **Voice Complaint (Bengali):** {voice_text}
            
            **Previous Voice Analysis:**
            - English Translation: {voice_analysis.get('english_translation', 'N/A')}
            - Category: {voice_analysis.get('category', 'N/A')}
            - Priority: {voice_analysis.get('priority', 'N/A')}
            - Key Issues: {', '.join(voice_analysis.get('key_points', []))}
            
            **Visual Evidence:** Please analyze the attached image/screenshot/document.
            **Attachment Filename:** {attachment_filename}
            
            Please provide a comprehensive analysis that combines both the voice complaint and visual evidence:
            
            1. **Attachment Analysis:**
               - What type of file is this? (screenshot, photo, document, etc.)
               - What specific details can you see?
               - What technical elements are visible?
               - Any error messages, UI elements, or important visual information?
            
            2. **Voice-Attachment Correlation:**
               - How does the attachment relate to the voice complaint?
               - Does the visual evidence support or contradict the voice complaint?
               - What additional context does the attachment provide?
            
            3. **Enhanced Ticket Information:**
               - Updated title that reflects both voice and visual context
               - Enhanced description combining voice and visual information
               - More accurate category and priority based on combined evidence
               - Specific action items based on visual evidence
            
            4. **Technical Assessment:**
               - If this is a technical issue, what can you determine from the attachment?
               - Any error codes, system states, or technical problems visible?
               - Suggested troubleshooting steps based on visual evidence
            
            Please respond in JSON format:
            {{
                "attachment_analysis": {{
                    "type": "screenshot/photo/document/other",
                    "content_description": "Detailed description of what's shown",
                    "technical_details": {{"any": "technical information found"}},
                    "extracted_text": "Any text visible in the image",
                    "key_visual_elements": ["list", "of", "important", "elements"]
                }},
                "voice_image_correlation": {{
                    "relationship": "How attachment relates to voice complaint",
                    "consistency": "Does attachment support the voice complaint?",
                    "additional_context": "What new information does attachment provide?"
                }},
                "enhanced_ticket": {{
                    "title": "Enhanced title based on voice + attachment",
                    "description": "Comprehensive description combining both sources",
                    "category": "Updated category if needed",
                    "priority": "Updated priority if needed",
                    "specific_issues": ["detailed", "list", "of", "issues"],
                    "recommended_actions": ["specific", "steps", "to", "resolve"]
                }},
                "technical_assessment": {{
                    "is_technical_issue": true/false,
                    "error_codes": ["any", "error", "codes", "found"],
                    "system_state": "Description of system state if applicable",
                    "troubleshooting_steps": ["step", "by", "step", "suggestions"]
                }}
            }}
            """
            
            # Use Gemini Vision to analyze the attachment with voice context
            # Create the image part from raw bytes
            import google.generativeai as genai
            
            # Determine mime type from filename
            mime_type = "image/jpeg"  # Default
            if attachment_filename.lower().endswith(('.png',)):
                mime_type = "image/png"
            elif attachment_filename.lower().endswith(('.gif',)):
                mime_type = "image/gif"
            elif attachment_filename.lower().endswith(('.webp',)):
                mime_type = "image/webp"
            elif attachment_filename.lower().endswith(('.pdf',)):
                mime_type = "application/pdf"
            elif attachment_filename.lower().endswith(('.doc', '.docx')):
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            # Create the attachment part for Gemini
            attachment_part = {
                "mime_type": mime_type,
                "data": attachment_bytes
            }
            
            # Send prompt and attachment to Gemini
            response = self.model.generate_content([combined_prompt, attachment_part])
            
            # Parse the response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    # Map categories and priorities in enhanced_ticket to valid enum values
                    if 'enhanced_ticket' in result and isinstance(result['enhanced_ticket'], dict):
                        enhanced_ticket = result['enhanced_ticket']
                        if 'category' in enhanced_ticket:
                            enhanced_ticket['category'] = self._map_category_to_enum(enhanced_ticket['category'])
                        if 'priority' in enhanced_ticket:
                            enhanced_ticket['priority'] = self._map_priority_to_enum(enhanced_ticket['priority'])
                else:
                    # Fallback parsing
                    result = self._parse_fallback_attachment_response(response.text, voice_text, voice_analysis)
                
                return result
                
            except json.JSONDecodeError:
                # Fallback parsing if JSON fails
                return self._parse_fallback_attachment_response(response.text, voice_text, voice_analysis)
                
        except Exception as e:
            print(f"Error analyzing attachment with voice: {str(e)}")
            # Return a basic fallback result
            return {
                "attachment_analysis": {
                    "type": "unknown",
                    "content_description": "Error analyzing attachment",
                    "technical_details": {},
                    "extracted_text": "",
                    "key_visual_elements": []
                },
                "voice_image_correlation": {
                    "relationship": "Unable to determine",
                    "consistency": "Cannot verify",
                    "additional_context": "Analysis failed"
                },
                "enhanced_ticket": {
                    "title": voice_analysis.get('title', 'Voice + Attachment Complaint'),
                    "description": voice_analysis.get('english_translation', 'Voice complaint with attachment'),
                    "category": self._map_category_to_enum(voice_analysis.get('category', 'general')),
                    "priority": self._map_priority_to_enum(voice_analysis.get('priority', 'medium')),
                    "specific_issues": ["Voice complaint with attachment - analysis failed"],
                    "recommended_actions": ["Manual review required"]
                },
                "technical_assessment": {
                    "is_technical_issue": False,
                    "error_codes": [],
                    "system_state": "Unknown",
                    "troubleshooting_steps": ["Manual review required"]
                }
            }

    def analyze_attachment_only(self, attachment_bytes: bytes, attachment_filename: str, customer_context: str = "") -> Dict[str, Any]:
        """
        Analyze an attachment without voice context
        
        Args:
            attachment_bytes (bytes): Raw bytes of the attachment file
            attachment_filename (str): Name of the attachment file
            customer_context (str): Optional context about the customer issue
            
        Returns:
            Dict containing attachment analysis
        """
        try:
            attachment_prompt = f"""
            Analyze this attachment that was submitted as part of a customer support ticket.
            
            **Attachment Filename:** {attachment_filename}
            **Customer Context:** {customer_context}
            
            Please provide a detailed analysis of this attachment:
            
            1. What type of content is this? (screenshot, photo, document, etc.)
            2. What specific details can you see?
            3. Are there any error messages, technical information, or important visual elements?
            4. What might be the customer's issue based on this attachment?
            5. What actions would you recommend?
            
            Please respond in JSON format:
            {{
                "attachment_type": "screenshot/photo/document/other",
                "content_description": "Detailed description",
                "extracted_text": "Any text visible",
                "technical_details": {{"any": "technical info"}},
                "inferred_issue": "What issue does this attachment suggest?",
                "suggested_category": "technical/billing/general/complaint/feature_request",
                "suggested_priority": "low/medium/high/urgent",
                "recommended_actions": ["specific", "action", "steps"]
            }}
            """
            
            # Determine mime type from filename
            mime_type = "image/jpeg"  # Default
            if attachment_filename.lower().endswith(('.png',)):
                mime_type = "image/png"
            elif attachment_filename.lower().endswith(('.gif',)):
                mime_type = "image/gif"
            elif attachment_filename.lower().endswith(('.webp',)):
                mime_type = "image/webp"
            elif attachment_filename.lower().endswith(('.pdf',)):
                mime_type = "application/pdf"
            elif attachment_filename.lower().endswith(('.doc', '.docx')):
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            # Create the attachment part for Gemini
            attachment_part = {
                "mime_type": mime_type,
                "data": attachment_bytes
            }
            
            response = self.model.generate_content([attachment_prompt, attachment_part])
            
            # Parse the response
            try:
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    # Map categories and priorities to valid enum values
                    if 'suggested_category' in result:
                        result['suggested_category'] = self._map_category_to_enum(result['suggested_category'])
                    if 'suggested_priority' in result:
                        result['suggested_priority'] = self._map_priority_to_enum(result['suggested_priority'])
                else:
                    result = self._parse_basic_attachment_fallback(response.text)
                
                return result
                
            except json.JSONDecodeError:
                return self._parse_basic_attachment_fallback(response.text)
                
        except Exception as e:
            print(f"Error analyzing attachment: {str(e)}")
            return {
                "attachment_type": "unknown",
                "content_description": "Error analyzing attachment",
                "extracted_text": "",
                "technical_details": {},
                "inferred_issue": "Unknown issue",
                "suggested_category": self._map_category_to_enum("general"),
                "suggested_priority": self._map_priority_to_enum("medium"),
                "recommended_actions": ["Manual review required"]
            }
    
    def _parse_basic_attachment_fallback(self, response_text: str) -> Dict[str, Any]:
        """Basic fallback for attachment-only analysis"""
        return {
            "attachment_type": "unknown",
            "content_description": response_text[:200] if response_text else "No description available",
            "extracted_text": "",
            "technical_details": {},
            "inferred_issue": "Issue requires manual review",
            "suggested_category": self._map_category_to_enum("general"),
            "suggested_priority": self._map_priority_to_enum("medium"),
            "recommended_actions": ["Manual review of attachment required"]
        }
    
    def _parse_fallback_attachment_response(self, response_text: str, voice_text: str, voice_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails for voice + attachment analysis"""
        return {
            "attachment_analysis": {
                "type": "unknown",
                "content_description": response_text[:200] if response_text else "No description available",
                "technical_details": {},
                "extracted_text": "",
                "key_visual_elements": []
            },
            "voice_image_correlation": {
                "relationship": "Analysis incomplete",
                "consistency": "Cannot determine",
                "additional_context": "Fallback analysis used"
            },
            "enhanced_ticket": {
                "title": voice_analysis.get('title', 'Voice + Attachment Complaint'),
                "description": f"Voice complaint: {voice_analysis.get('english_translation', voice_text)}. Attachment analysis: {response_text[:300]}",
                "category": self._map_category_to_enum(voice_analysis.get('category', 'general')),
                "priority": self._map_priority_to_enum(voice_analysis.get('priority', 'medium')),
                "specific_issues": ["Voice complaint with attachment"],
                "recommended_actions": ["Review attachment manually"]
            },
            "technical_assessment": {
                "is_technical_issue": False,
                "error_codes": [],
                "system_state": "Unknown",
                "troubleshooting_steps": ["Manual review required"]
            }
        }

    def _map_category_to_enum(self, ai_category: str) -> str:
        """
        Map AI-generated category to valid TicketCategoryEnum value
        
        Args:
            ai_category (str): Category generated by AI
            
        Returns:
            str: Valid category enum value
        """
        if not ai_category or not isinstance(ai_category, str):
            return "general"
            
        ai_category_lower = ai_category.lower()
        
        # Technical categories
        if any(keyword in ai_category_lower for keyword in [
            'technical', 'tech', 'system', 'software', 'hardware', 'network',
            'authentication', 'login', 'password', 'error', 'bug', 'crash',
            'connection', 'database', 'server', 'api', 'integration', 'security'
        ]):
            return "technical"
        
        # Billing categories  
        elif any(keyword in ai_category_lower for keyword in [
            'billing', 'payment', 'invoice', 'charge', 'refund', 'price',
            'cost', 'subscription', 'plan', 'finance', 'money', 'credit'
        ]):
            return "billing"
        
        # Complaint categories
        elif any(keyword in ai_category_lower for keyword in [
            'complaint', 'dissatisfied', 'unhappy', 'frustrated', 'angry',
            'service', 'support', 'quality', 'experience', 'issue', 'problem'
        ]):
            return "complaint"
        
        # Feature request categories
        elif any(keyword in ai_category_lower for keyword in [
            'feature', 'request', 'enhancement', 'improvement', 'suggestion',
            'new', 'add', 'functionality', 'capability', 'wishlist'
        ]):
            return "feature_request"
        
        # Default to general
        else:
            return "general"

    def _map_priority_to_enum(self, ai_priority: str) -> str:
        """
        Map AI-generated priority to valid TicketPriorityEnum value
        
        Args:
            ai_priority (str): Priority generated by AI
            
        Returns:
            str: Valid priority enum value
        """
        if not ai_priority or not isinstance(ai_priority, str):
            return "medium"
            
        ai_priority_lower = ai_priority.lower()
        
        if any(keyword in ai_priority_lower for keyword in ['urgent', 'critical', 'emergency', 'immediate']):
            return "urgent"
        elif any(keyword in ai_priority_lower for keyword in ['high', 'important', 'serious']):
            return "high"
        elif any(keyword in ai_priority_lower for keyword in ['low', 'minor', 'trivial']):
            return "low"
        else:
            return "medium"

# Global instance for reuse
gemini_processor = None

def get_gemini_processor():
    """Get or create Gemini processor instance"""
    global gemini_processor
    if gemini_processor is None:
        gemini_processor = GeminiTicketProcessor()
    return gemini_processor

if __name__ == "__main__":
    # Test the processor
    processor = GeminiTicketProcessor()
    
    test_bengali = "আমার ইন্টারনেট কানেকশন খুবই ধীর হচ্ছে। কয়েকদিন ধরে এই সমস্যা হচ্ছে। দয়া করে দ্রুত সমাধান করুন।"
    result = processor.process_bengali_complaint(test_bengali)
    
    print("Processing Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False)) 