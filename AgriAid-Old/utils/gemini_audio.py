import io
import base64
import os
import tempfile
import google.generativeai as genai
from gtts import gTTS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyC5ADCw6rPvd2mBOegP62OEZ0pjlNYV0VA"  # Using the same key from app2.py
genai.configure(api_key=GEMINI_API_KEY)

def preprocess_audio_for_transcription(audio_bytes, mime_type="audio/mpeg"):
    """Preprocesses audio bytes for transcription, especially for Streamlit's recorder."""
    try:
        # Detect if this is likely a WAV file from Streamlit's recorder
        is_wav = False
        if audio_bytes[:4] == b'RIFF' and b'WAVE' in audio_bytes[:12]:
            mime_type = "audio/wav"
            is_wav = True
            logger.info("Detected WAV format audio")

            # Save the audio to a temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
                logger.info(f"Saved audio to temporary file: {tmp_path}")

                # For Streamlit's recorder output, we need to convert it to a format
                # that Gemini can better understand
                try:
                    # Try to use pydub to normalize the audio
                    from pydub import AudioSegment

                    # Load the audio file
                    audio = AudioSegment.from_wav(tmp_path)

                    # Normalize the audio (adjust volume to a standard level)
                    normalized_audio = audio.normalize()

                    # Export to a new temporary file
                    processed_path = tmp_path + "_processed.wav"
                    normalized_audio.export(processed_path, format="wav")

                    # Read the processed file
                    with open(processed_path, 'rb') as f:
                        processed_audio_bytes = f.read()

                    # Clean up
                    if os.path.exists(processed_path):
                        os.unlink(processed_path)

                    logger.info(f"Successfully preprocessed audio, new size: {len(processed_audio_bytes)} bytes")
                    return processed_audio_bytes, mime_type

                except Exception as e:
                    logger.warning(f"Audio preprocessing failed: {e}, using original audio")
                finally:
                    # Clean up the temporary file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

        # If not WAV or preprocessing failed, return the original bytes
        return audio_bytes, mime_type

    except Exception as e:
        logger.error(f"Error during audio preprocessing: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return audio_bytes, mime_type


def transcribe_audio_with_gemini(audio_bytes, mime_type="audio/mpeg"):
    """Transcribes audio bytes to text using the Gemini API."""
    try:
        # Preprocess the audio for better transcription
        processed_audio, mime_type = preprocess_audio_for_transcription(audio_bytes, mime_type)

        logger.info(f"Transcribing audio with mime_type: {mime_type}, audio size: {len(processed_audio)} bytes")

        # Use a more specific prompt for better transcription
        prompt = """
        Transcribe the following audio recording accurately.
        This is a recording about crop diseases or agricultural problems.
        The speaker is describing plant symptoms, diseases, or pest issues.
        Focus on agricultural terminology and plant health descriptions.
        Provide a complete and accurate transcription of all spoken content.
        """

        # Use a more capable model for transcription
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # Set generation config for better transcription
        generation_config = {
            "temperature": 0.2,  # Lower temperature for more accurate transcription
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }

        # Make the API call
        response = model.generate_content(
            [
                prompt,
                {
                    "mime_type": mime_type,
                    "data": processed_audio
                }
            ],
            generation_config=generation_config
        )

        # Log the response for debugging
        transcribed_text = response.text
        logger.info(f"Transcription result: {transcribed_text[:100]}...")

        # If the transcription is too short, it might be an error
        if len(transcribed_text.strip()) < 10:
            logger.warning(f"Transcription result too short: '{transcribed_text}'")

            # Try one more time with a different approach
            logger.info("Trying alternative transcription approach...")
            response = model.generate_content(
                [
                    "This is an audio recording about plant diseases or agricultural problems. Please transcribe it word for word:",
                    {
                        "mime_type": mime_type,
                        "data": processed_audio
                    }
                ],
                generation_config=generation_config
            )
            transcribed_text = response.text
            logger.info(f"Second attempt transcription result: {transcribed_text[:100]}...")

        return transcribed_text
    except Exception as e:
        logger.error(f"Error during audio transcription: {e}")
        # Print more detailed error information
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_audio_input(audio_data):
    """Process audio input using Gemini API for transcription."""
    try:
        # Ensure input_data is bytes
        if not isinstance(audio_data, bytes):
            raise TypeError(f"Expected bytes for audio, got {type(audio_data)}")

        # Save audio data to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        logger.info(f"Saved audio to temporary file: {tmp_path}")

        # Transcribe the audio using Gemini API
        transcribed_text = transcribe_audio_with_gemini(audio_data)

        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

        if not transcribed_text or transcribed_text.strip() == "":
            logger.warning("Transcription failed or returned empty text")
            return None

        return transcribed_text

    except Exception as e:
        logger.error(f"Error processing audio input: {e}")
        return None

def clean_text_for_speech(text):
    """Clean text to make it more suitable for text-to-speech conversion."""
    import re

    # Replace common emojis with their meanings or remove them
    emoji_replacements = {
        '🌱': 'plant',
        '🌾': 'crop',
        '🩺': 'diagnosis',
        '💊': 'remedy',
        '🔍': 'inspect',
        '🌿': 'herb',
        '🍃': 'leaf',
        '🌞': 'sun',
        '💧': 'water',
        '🔊': 'audio',
        '📊': 'chart',
        '📝': 'note',
        '⚠️': 'warning',
        '✅': 'done',
        '❌': 'not',
        '➡️': 'next',
        '⬅️': 'previous',
        '⭐': 'star',
        '🔴': 'red',
        '🟢': 'green',
        '🟡': 'yellow',
    }

    # First replace emojis with spaces or their meanings
    for emoji, replacement in emoji_replacements.items():
        if emoji in text:
            # For diagnosis/remedy headers, replace with the word and a colon
            if emoji in ['🩺', '💊', '🌱']:
                text = text.replace(emoji, f"{replacement}: ")
            else:
                # For other emojis, just remove them
                text = text.replace(emoji, " ")

    # Remove any remaining emojis not in our dictionary
    text = re.sub(r'[^\w\s.,;:!?()-]', ' ', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    # Replace special characters that might be read out loud
    text = text.replace('*', ' ')
    text = text.replace('#', ' ')
    text = text.replace('_', ' ')
    text = text.replace('-', ' ')
    text = text.replace('/', ' or ')
    text = text.replace('&', ' and ')
    text = text.replace('%', ' percent ')
    text = text.replace('(', ' ')
    text = text.replace(')', ' ')
    text = text.replace('\n', '. ')  # Replace newlines with periods for better pausing

    # Replace common abbreviations
    text = text.replace('e.g.', 'for example')
    text = text.replace('i.e.', 'that is')
    text = text.replace('etc.', 'etcetera')

    # Clean up any artifacts from the replacements
    text = re.sub(r'\s+', ' ', text)  # Remove multiple spaces again
    text = re.sub(r'\.+', '.', text)  # Replace multiple periods with a single one
    text = re.sub(r'\s+\.', '.', text)  # Remove spaces before periods
    text = re.sub(r'\.\s+', '. ', text)  # Ensure single space after periods

    # Trim whitespace
    text = text.strip()

    logger.info(f"Cleaned text for speech: {text[:100]}...")
    return text

def generate_speech(text, lang='en'):
    """Generates speech audio bytes from text using gTTS."""
    try:
        # Validate input
        if not text or not isinstance(text, str):
            logger.warning("Invalid text input for speech generation")
            # Return a default audio message
            default_text = "Sorry, I couldn't generate audio for this diagnosis. Please read the text solution."
            tts = gTTS(text=default_text, lang='en')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            return audio_bytes.getvalue()

        # Clean up the text to make it more suitable for speech
        cleaned_text = clean_text_for_speech(text)

        # Validate language code
        valid_langs = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'hi', 'ar']
        if lang not in valid_langs:
            logger.warning(f"Unsupported language code: {lang}, falling back to English")
            lang = 'en'

        # Generate speech
        tts = gTTS(text=cleaned_text, lang=lang)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_value = audio_bytes.getvalue()

        # Verify we got valid audio data
        if not audio_value or len(audio_value) < 100:  # Arbitrary small size check
            raise ValueError("Generated audio is too small, likely invalid")

        return audio_value
    except Exception as e:
        logger.error(f"Error generating audio: {e}")

        # Try again with a simpler message in English as fallback
        try:
            fallback_text = "I've provided a text diagnosis. Please read it for details about your crop issue."
            tts = gTTS(text=fallback_text, lang='en')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            return audio_bytes.getvalue()
        except Exception as e2:
            logger.error(f"Fallback audio generation also failed: {e2}")
            return None

def get_audio_download_link(audio_bytes, filename="solution_audio.mp3", text="Download Audio Solution"):
    """Generates a download link for the audio file."""
    try:
        if not audio_bytes:
            return "<p style='color: red;'>Audio not available for download</p>"

        # Ensure filename has the correct extension
        if not filename.lower().endswith('.mp3'):
            filename += '.mp3'

        # Encode the audio bytes
        b64 = base64.b64encode(audio_bytes).decode()

        # Create a button-style download link with improved visibility
        href = f'''
        <a href="data:audio/mpeg;base64,{b64}"
           download="{filename}"
           style="background-color: #4CAF50;
                  color: white;
                  padding: 10px 15px;
                  text-align: center;
                  text-decoration: none;
                  display: inline-block;
                  font-size: 16px;
                  margin: 4px 2px;
                  cursor: pointer;
                  border-radius: 4px;
                  border: none;
                  font-weight: 500;
                  box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <span style="display: flex; align-items: center; justify-content: center;">
                <span style="margin-right: 8px;">⬇️</span> {text}
            </span>
        </a>
        '''
        return href
    except Exception as e:
        logger.error(f"Error creating download link: {e}")
        return "<p style='color: red;'>Error creating download link</p>"

def get_audio_player_html(audio_bytes):
    """Generates HTML for an audio player with the provided audio bytes."""
    try:
        if not audio_bytes:
            return """
            <div style="background-color: #ffeeee; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                <p style="color: red; text-align: center;">Audio playback not available</p>
            </div>
            """

        # Encode the audio bytes
        audio_bytes_b64 = base64.b64encode(audio_bytes).decode()

        # Create the audio player HTML
        audio_player = f"""
        <div style="background-color: #e0eee0; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
            <audio controls style="width: 100%;" controlsList="nodownload">
                <source src="data:audio/mpeg;base64,{audio_bytes_b64}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            <div style="font-size: 0.8em; color: #38761d; margin-top: 5px; text-align: center;">
                Use the player controls to play, pause, and adjust volume
            </div>
        </div>
        """
        return audio_player
    except Exception as e:
        logger.error(f"Error creating audio player: {e}")
        return """
        <div style="background-color: #ffeeee; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
            <p style="color: red; text-align: center;">Error creating audio player</p>
        </div>
        """
