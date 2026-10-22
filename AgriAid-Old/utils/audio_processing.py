import whisper
from pydub import AudioSegment
import os

# Load the Whisper model globally to avoid reloading for each transcription
try:
    model = whisper.load_model("base")
    print("Whisper model loaded successfully.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    model = None

def convert_audio(file_path):
    """Convert audio file to WAV format."""
    output_path = "temp.wav"
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        # Check if file is empty
        if os.path.getsize(file_path) == 0:
            print(f"File is empty: {file_path}")
            return None

        try:
            # Try to load the file with pydub
            audio = AudioSegment.from_file(file_path)
            audio.export(output_path, format="wav")

            # Verify the output file was created and is not empty
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            else:
                print("Output file is empty or not created")
                return None

        except Exception as e:
            print(f"First conversion attempt failed: {e}")

            # Fallback: Try with explicit format detection
            try:
                # Try to determine format from file extension
                file_ext = os.path.splitext(file_path)[1].lower().replace('.', '')
                if file_ext in ['mp3', 'wav', 'ogg', 'flac', 'm4a']:
                    audio = AudioSegment.from_file(file_path, format=file_ext)
                    audio.export(output_path, format="wav")
                    return output_path
                else:
                    # Try common formats
                    for fmt in ['mp3', 'wav', 'ogg']:
                        try:
                            audio = AudioSegment.from_file(file_path, format=fmt)
                            audio.export(output_path, format="wav")
                            return output_path
                        except:
                            continue
            except Exception as inner_e:
                print(f"Fallback conversion failed: {inner_e}")

        return None
    except Exception as e:
        print(f"Audio conversion error: {e}")
        # If output file was created but is invalid, clean it up
        if os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except:
                pass
        return None

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper model."""
    if model is None:
        print("Whisper model not loaded, cannot transcribe.")
        return ""

    try:
        # Check if file exists
        if not os.path.exists(audio_path):
            print(f"Transcription file not found: {audio_path}")
            return ""

        # Check if file is empty
        if os.path.getsize(audio_path) == 0:
            print(f"Transcription file is empty: {audio_path}")
            return ""

        result = model.transcribe(audio_path)
        transcription = result["text"]

        # Check if transcription is empty or too short
        if not transcription or len(transcription.strip()) < 3:
            print("Transcription is empty or too short")
            return ""

        return transcription
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""

if __name__ == '__main__':
    # Example usage for testing
    test_file = "audio.mp3"  # Replace with your test audio file
    if os.path.exists(test_file):
        converted_path = convert_audio(test_file)
        if converted_path:
            transcription = transcribe_audio(converted_path)
            print(f"Transcription of {test_file}: {transcription}")
            os.remove(converted_path) # Clean up temporary file
        else:
            print(f"Audio conversion failed for {test_file}")
    else:
        print(f"Test file '{test_file}' not found. Please create a test audio file.")