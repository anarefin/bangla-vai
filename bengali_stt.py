import os
import requests
import json
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from gtts import gTTS
import tempfile

# Load environment variables
load_dotenv()

class BengaliSTT:
    def __init__(self):
        """Initialize the Bengali Speech-to-Text client with ElevenLabs Scribe API"""
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
    
    def transcribe_audio_file(self, audio_file_path: str, language: str = "bengali") -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file to Bengali text using ElevenLabs Scribe API
        
        Args:
            audio_file_path (str): Path to the audio file
            language (str): Language for transcription (default: bengali)
            
        Returns:
            Dict containing transcription result or None if failed
        """
        try:
            # Check if file exists
            if not os.path.exists(audio_file_path):
                print(f"Error: Audio file '{audio_file_path}' not found")
                return None
            
            # Prepare the file for upload
            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'file': (os.path.basename(audio_file_path), audio_file, 'audio/mpeg')
                }
                
                data = {
                    'model_id': 'scribe_v1',
                    'language_code': 'ben' if language == 'bengali' else language
                }
                
                print(f"Uploading and transcribing '{audio_file_path}'...")
                print("This may take a few moments...")
                
                # Make the API request
                response = requests.post(
                    f"{self.base_url}/speech-to-text",
                    headers=self.headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    print(f"Error: API request failed with status code {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            return None
    
    def save_transcription(self, transcription_result: Dict[str, Any], output_file: str = "transcription.txt"):
        """
        Save transcription result to a text file
        
        Args:
            transcription_result (dict): Result from transcribe_audio_file
            output_file (str): Output file name
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if 'text' in transcription_result:
                    f.write(transcription_result['text'])
                elif 'transcription' in transcription_result:
                    f.write(transcription_result['transcription'])
                else:
                    # Write the entire result if structure is different
                    f.write(str(transcription_result))
            
            print(f"Transcription saved to '{output_file}'")
            
        except Exception as e:
            print(f"Error saving transcription: {str(e)}")


class BengaliTTS:
    def __init__(self):
        """Initialize the Bengali Text-to-Speech client"""
        pass
    
    def text_to_speech(self, text: str, output_path: str = None, slow: bool = False) -> str:
        """
        Convert Bengali text to speech and save as audio file
        
        Args:
            text (str): Bengali text to convert to speech
            output_path (str): Path to save the audio file (optional)
            slow (bool): Whether to speak slowly
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            # Create TTS object for Bengali
            tts = gTTS(text=text, lang='bn', slow=slow)
            
            # If no output path specified, create a temporary file
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                output_path = temp_file.name
                temp_file.close()
            
            # Save the audio file
            tts.save(output_path)
            
            print(f"Speech saved to '{output_path}'")
            return output_path
            
        except Exception as e:
            print(f"Error during text-to-speech conversion: {str(e)}")
            return None
    
    def save_text_to_file(self, text: str, output_file: str = "bengali_text.txt"):
        """
        Save Bengali text to a text file
        
        Args:
            text (str): Bengali text to save
            output_file (str): Output file name
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"Text saved to '{output_file}'")
            
        except Exception as e:
            print(f"Error saving text: {str(e)}")


def main():
    """Main function to demonstrate Bengali speech-to-text"""
    print("=== Bengali Speech-to-Text with ElevenLabs Scribe API ===\n")
    
    try:
        # Initialize the STT client
        stt = BengaliSTT()
        print("✓ ElevenLabs Scribe API client initialized successfully\n")
        
        # Get audio file path from user
        audio_file_path = input("Enter the path to your Bengali audio file: ").strip()
        
        if not audio_file_path:
            print("No file path provided. Exiting...")
            return
        
        # Transcribe the audio
        result = stt.transcribe_audio_file(audio_file_path)
        
        if result:
            print("\n" + "="*50)
            print("TRANSCRIPTION RESULT:")
            print("="*50)
            
            # Display the transcription
            if 'text' in result:
                print(result['text'])
                transcript_text = result['text']
            elif 'transcription' in result:
                print(result['transcription'])
                transcript_text = result['transcription']
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
                transcript_text = str(result)
            
            print("="*50)
            
            # Ask if user wants to save the result
            save_choice = input("\nDo you want to save the transcription to a file? (y/n): ").strip().lower()
            if save_choice in ['y', 'yes']:
                output_filename = input("Enter output filename (default: bengali_transcription.txt): ").strip()
                if not output_filename:
                    output_filename = "bengali_transcription.txt"
                
                stt.save_transcription(result, output_filename)
        else:
            print("❌ Transcription failed. Please check your audio file and API key.")
            
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please make sure to:")
        print("1. Copy .env.example to .env")
        print("2. Add your ElevenLabs API key to the .env file")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 