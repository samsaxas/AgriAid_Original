import io
import base64
from gtts import gTTS

def generate_speech(text, lang='en'):
    """Generates speech audio bytes from text using gTTS."""
    try:
        # Validate input
        if not text or not isinstance(text, str):
            print("Invalid text input for speech generation")
            # Return a default audio message
            default_text = "Sorry, I couldn't generate audio for this diagnosis. Please read the text solution."
            tts = gTTS(text=default_text, lang='en')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            return audio_bytes.getvalue()

        # Clean up the text to remove any problematic characters
        cleaned_text = text.replace('\n', ' ').replace('\r', ' ')

        # Validate language code
        valid_langs = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'hi', 'ar']
        if lang not in valid_langs:
            print(f"Unsupported language code: {lang}, falling back to English")
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
        print(f"Error generating audio: {e}")

        # Try again with a simpler message in English as fallback
        try:
            fallback_text = "I've provided a text diagnosis. Please read it for details about your crop issue."
            tts = gTTS(text=fallback_text, lang='en')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            return audio_bytes.getvalue()
        except Exception as e2:
            print(f"Fallback audio generation also failed: {e2}")
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
        href = f'<a href="data:audio/mpeg;base64,{b64}" download="{filename}" class="download-btn">{text}</a>'
        return href
    except Exception as e:
        print(f"Error creating download link: {e}")
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
        print(f"Error creating audio player: {e}")
        return """
        <div style="background-color: #ffeeee; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
            <p style="color: red; text-align: center;">Error creating audio player</p>
        </div>
        """
