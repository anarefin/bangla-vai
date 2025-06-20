# Bengali Speech-to-Text with ElevenLabs Scribe API

A Python application that converts Bengali speech to text using ElevenLabs Scribe API (free tier). The application includes both a command-line interface and a web-based Streamlit interface.

## Features

- 🎤 Bengali speech-to-text transcription
- 🌐 Web interface using Streamlit
- 💻 Command-line interface
- 📁 Support for multiple audio formats (MP3, WAV, M4A, OGG, FLAC)
- 💾 Save transcriptions to text files
- 🆓 Uses ElevenLabs free tier

## Prerequisites

- Python 3.7 or higher
- ElevenLabs account with API key
- Audio files containing Bengali speech

## Step-by-Step Setup Instructions

### Step 1: Get ElevenLabs API Key

1. Visit [ElevenLabs](https://elevenlabs.io/) and create a free account
2. After signing up, go to your profile/settings
3. Find and copy your API key
4. The free tier includes speech-to-text capabilities

### Step 2: Clone or Download the Project

If you're starting fresh, make sure you have all the project files in your directory.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `requests` - For API calls to ElevenLabs
- `pydub` - For audio file handling
- `streamlit` - For the web interface
- `python-dotenv` - For environment variable management

### Step 4: Configure API Key

**Option A: Using .env file (Recommended)**
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit the `.env` file and add your API key:
   ```
   ELEVENLABS_API_KEY=your_actual_api_key_here
   ```

**Option B: Set environment variable directly**
```bash
export ELEVENLABS_API_KEY=your_actual_api_key_here
```

> **⚠️ Security Note**: Never commit your actual `.env` file to Git! It's already excluded in `.gitignore` to keep your API keys safe.

### Step 5: Prepare Bengali Audio Files

- Ensure your audio files contain clear Bengali speech
- Supported formats: MP3, WAV, M4A, OGG, FLAC
- Better audio quality = better transcription accuracy

## Usage Instructions

### Method 1: Command Line Interface

1. Run the main script:
   ```bash
   python bengali_stt.py
   ```

2. When prompted, enter the path to your Bengali audio file:
   ```
   Enter the path to your Bengali audio file: /path/to/your/bengali_audio.mp3
   ```

3. The program will:
   - Upload your audio file to ElevenLabs
   - Process the transcription
   - Display the Bengali text result
   - Optionally save the result to a text file

### Method 2: Web Interface (Streamlit)

1. Start the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```

2. Open your browser and go to the displayed URL (usually `http://localhost:8501`)

3. In the web interface:
   - Enter your ElevenLabs API key in the sidebar (if not set in .env)
   - Upload a Bengali audio file using the file uploader
   - Click "Transcribe Audio" button
   - View and download the transcription result

## File Structure

```
bangla-vai/
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── bengali_stt.py          # Main CLI application
├── streamlit_app.py        # Web interface
└── README.md               # This file
```

## Example Usage

### Command Line Example

```bash
$ python bengali_stt.py
=== Bengali Speech-to-Text with ElevenLabs Scribe API ===

✓ ElevenLabs Scribe API client initialized successfully

Enter the path to your Bengali audio file: my_bengali_audio.mp3
Uploading and transcribing 'my_bengali_audio.mp3'...
This may take a few moments...

==================================================
TRANSCRIPTION RESULT:
==================================================
আমি বাংলায় কথা বলছি। এটি একটি পরীক্ষা।
==================================================

Do you want to save the transcription to a file? (y/n): y
Enter output filename (default: bengali_transcription.txt): 
Transcription saved to 'bengali_transcription.txt'
```

## API Limits and Pricing

- **Free Tier**: ElevenLabs provides free credits for speech-to-text
- **Rate Limits**: Check ElevenLabs documentation for current limits
- **File Size**: Depends on your plan (free tier has size limitations)

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   ValueError: ELEVENLABS_API_KEY not found in environment variables
   ```
   **Solution**: Make sure your API key is properly set in the `.env` file or environment variable.

2. **File Not Found Error**
   ```
   Error: Audio file 'filename.mp3' not found
   ```
   **Solution**: Check the file path and ensure the audio file exists.

3. **API Request Failed**
   ```
   Error: API request failed with status code 401
   ```
   **Solution**: Verify your API key is correct and has sufficient credits.

4. **Unsupported Audio Format**
   **Solution**: Convert your audio to one of the supported formats (MP3, WAV, M4A, OGG, FLAC).

### Audio Quality Tips

- Use clear, high-quality audio recordings
- Minimize background noise
- Ensure the speaker speaks clearly in Bengali
- Avoid overlapping voices or multiple speakers

## Advanced Usage

### Custom Language Settings

You can modify the language parameter in the code:

```python
result = stt.transcribe_audio_file(audio_file_path, language="bengali")
```

### Batch Processing

To process multiple files, you can modify the main script to loop through a directory of audio files.

## Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Improving documentation
- Adding support for other languages

## License

This project is open source. Please check ElevenLabs' terms of service for API usage guidelines.

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your ElevenLabs API key and credits
3. Ensure your audio file is in a supported format
4. Check the ElevenLabs API documentation for any updates

---

**Happy transcribing! 🎤➡️📝** 