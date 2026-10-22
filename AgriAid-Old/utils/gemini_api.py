import os
import tempfile
import time  # Import the time module
from dotenv import load_dotenv
from pydub import AudioSegment
from PIL import Image
import io
import google.generativeai as genai
from streamlit.runtime.uploaded_file_manager import UploadedFile
import speech_recognition as sr
import logging  # Import the logging module

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)  # Log detailed information for debugging


# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Check if API key is set
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# Configure Gemini
genai.configure(api_key=api_key)

def analyze_text(input_text):
    """Analyze text-based crop issues"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        prompt = f"""As an agricultural expert, analyze this crop issue described in the following text:
        {input_text}

        Provide response in this format with short, concise content (no extra words):
        🩺 Diagnosis: [list 2-3 most likely causes very concisely, use numbered list format (1., 2., etc.)]
        💊 Remedies: [3-5 actionable treatment steps, be extremely specific and brief, use numbered list format (1., 2., etc.)]
        🌱 Prevention: [2-3 long-term solutions, be extremely specific and brief, use numbered list format (1., 2., etc.)]

        IMPORTANT: Keep each point short and to the point. Avoid unnecessary words or explanations. Each point should be 1-2 sentences maximum."""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error during text analysis: {e}")
        return f"Error during text analysis: {str(e)}"


def analyze_image(image_input):
    """Analyze image-based crop diseases"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        if isinstance(image_input, bytes):
            image = Image.open(io.BytesIO(image_input))
        else:
            image = image_input
        response = model.generate_content([
            """Analyze this crop disease image and provide a very concise report including:
            🩺 Diagnosis: [Likely disease name (scientific and common name if available), followed by numbered list (1., 2., etc.) of symptoms and causes - keep extremely brief]
            📊 Confidence: [Estimated confidence percentage (e.g., 85%)]
            💊 Remedies: [2-3 immediate and specific treatment steps in numbered list format (1., 2., etc.) - keep extremely brief with no extra words]
            🌱 Prevention: [2-3 specific prevention methods in numbered list format (1., 2., etc.) - keep extremely brief with no extra words]
            ⚠️ Contagion: [Briefly state the contagion risk level (e.g., Low, Medium, High)]

            IMPORTANT: Keep each point short and to the point. Avoid unnecessary words or explanations. Each point should be 1-2 sentences maximum.""",
            image
        ])
        return response.text
    except Exception as e:
        logging.error(f"Image analysis error: {e}")
        return f"Image analysis error: {str(e)}"



def convert_audio_to_wav(audio_path):
    """Convert audio file to WAV format."""
    try:
        logging.debug(f"Converting audio file: {audio_path}")
        audio = AudioSegment.from_file(audio_path)
        wav_path = os.path.splitext(audio_path)[0] + ".wav"
        audio.export(wav_path, format="wav")
        logging.debug(f"Successfully converted to: {wav_path}")
        return wav_path
    except Exception as e:
        logging.error(f"Error converting audio: {e}")
        raise Exception(f"Error converting audio: {e}")  # Re-raise the exception



def transcribe_audio(audio_file_path):
    """Transcribe audio using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            logging.debug(f"Transcription: {text}")
            return text
    except sr.UnknownValueError:
        logging.warning("Could not understand audio")
        return "Could not understand audio"
    except sr.RequestError as e:
        logging.error(f"Error with Google Speech Recognition service: {e}")
        raise Exception(f"Error with Google Speech Recognition service: {e}")
    except Exception as e:
        logging.error(f"Error transcribing audio: {e}")
        raise Exception(f"Error transcribing audio: {e}")



def analyze_audio(audio_file: UploadedFile):
    """Process audio descriptions of crop issues from an UploadedFile (.mp3 supported)."""
    temp_file_path = None  # Keep track of the temporary file path
    wav_path = None
    try:
        # Save the uploaded audio file to a temporary location
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file_path = temp_file.name  # Store the path
        try:
            temp_file.write(audio_file.read())
            audio_path = temp_file_path
        except Exception as e:
            logging.error(f"Error writing to temporary file: {e}")
            temp_file.close()  # Ensure file is closed
            os.unlink(temp_file_path)  # delete
            raise Exception(f"Error writing to temporary file: {e}")
        finally:
            temp_file.close()  # Ensure the temporary file is always closed

        logging.debug(f"Saved uploaded audio to: {audio_path}")

        # Convert to WAV if it's not already WAV
        wav_path = audio_path  # Initialize wav_path
        if audio_file.type != "audio/wav":
            try:
                wav_path = convert_audio_to_wav(audio_path)
            except Exception as e:
                os.unlink(audio_path)
                raise  # Re-raise
        logging.debug(f"WAV file path: {wav_path}")

        transcribed_text = transcribe_audio(wav_path)

        # Delay before deleting files
        time.sleep(0.1)  # Add a short delay (adjust as needed)

        # Clean up
        if os.path.exists(wav_path):
            os.unlink(wav_path)
        if temp_file_path and os.path.exists(temp_file_path):  # Check if temp_file_path is set
            os.unlink(temp_file_path)

        if transcribed_text.lower() == "could not understand audio":
            return "Could not understand the audio. Please try again with a clearer recording."
        elif not transcribed_text.strip():
            return "No discernible speech detected in the audio."
        else:
            result = analyze_text(transcribed_text)
            return result
    except ImportError:
        error_message = "Error: The 'speech_recognition' library is required for audio transcription. Please install it using: pip install SpeechRecognition"
        logging.error(error_message)
        return error_message
    except Exception as e:
        error_message = f"Error during audio analysis: {str(e)}"
        logging.error(error_message)
        return error_message

if __name__ == '__main__':
    # Example usage for text analysis
    text_query = "The tomato plant leaves are turning yellow and have brown spots."
    text_result = analyze_text(text_query)
    print("\n--- Text Analysis Result ---")
    print(text_result)

    # Example usage for image analysis (replace 'test_image.jpg' with your image file)
    try:
        with open("test_image.jpg", "rb") as f:
            image_data = f.read()
            image_result = analyze_image(image_data)
            print("\n--- Image Analysis Result ---")
            print(image_result)
    except FileNotFoundError:
        print("\n--- Image Analysis ---")
        print("Error: test_image.jpg not found. Please place a test image in the same directory to test image analysis.")
    except Exception as e:
        print(f"\n--- Image Analysis Error ---")
        print(e)

    # Example usage for audio analysis (you'll need an audio file for proper testing)
    # Create a dummy audio file for testing if one doesn't exist
    dummy_audio_content = b"RIFF\x14\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x80>\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00"
    dummy_audio_file = "dummy_audio.wav"
    if not os.path.exists(dummy_audio_file):
        with open(dummy_audio_file, "wb") as f:
            f.write(dummy_audio_content)

    try:
        with open(dummy_audio_file, "rb") as f:
            class MockUploadedFile:
                def __init__(self, file_path, content_type):
                    self.name = os.path.basename(file_path)
                    self.type = content_type
                    self._file = open(file_path, 'rb')

                def read(self):
                    return self._file.read()

                def close(self):
                    self._file.close()

            mock_uploaded_file = MockUploadedFile(dummy_audio_file, "audio/wav")
            audio_result = analyze_audio(mock_uploaded_file)
            print("\n--- Audio Analysis Result ---")
            print(audio_result)
            mock_uploaded_file.close()
            os.remove(dummy_audio_file) # Clean up dummy file
    except ImportError:
        print("\n--- Audio Analysis ---")
        print("Error: speech_recognition or pydub not installed. Install with: pip install SpeechRecognition pydub")
    except Exception as e:
        print(f"\n--- Audio Analysis Error ---")
        print(e)