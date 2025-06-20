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
            "category": result.get("category", "general").lower(),
            "priority": result.get("priority", "medium").lower(),
            "key_points": result.get("key_points", []),
            "sentiment": result.get("sentiment", "neutral"),
            "urgency_indicators": result.get("urgency_indicators", [])
        }
        
        # Validate category
        if cleaned_result["category"] not in valid_categories:
            cleaned_result["category"] = "general"
        
        # Validate priority
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