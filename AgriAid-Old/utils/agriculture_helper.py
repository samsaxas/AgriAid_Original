import numpy as np
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from huggingface_hub import login
from utils.audio_processing import convert_audio, transcribe_audio
from utils.translation import translate_to_english

# Load environment variables
load_dotenv()

class AgricultureHelper:
    def __init__(self):
        # Initialize embedding model for intent detection
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.agri_phrases = [
            "plant", "crop", "leaf", "disease", "pest", "soil", 
            "watering", "fertilizer", "tomato", "wheat", "rice",
            "yellow", "brown", "spots", "wilting", "fungus", "insects"
        ]
        self.agri_embeddings = self.embedder.encode(self.agri_phrases)
        
        # Initialize text generator with agricultural focus
        self.text_gen = pipeline(
            "text-generation",
            model="gpt2",
            tokenizer="gpt2"
        )

    def is_agricultural(self, text, threshold=0.45):
        """Check if input relates to agriculture using semantic similarity"""
        text_embed = self.embedder.encode([text])[0]
        similarities = np.dot(self.agri_embeddings, text_embed)
        return max(similarities) > threshold

    def generate_response(self, text):
        """Generate professional agricultural response"""
        prompt = f"""As an agricultural expert, provide detailed advice for:
        "{text}"

        Respond with:
        1. Likely causes (2-3 possibilities)
        2. Immediate remedies (bullet points)
        3. Prevention methods
        4. When to consult an expert

        Guidelines:
        - Be scientifically accurate
        - Use simple language
        - Include both organic and chemical solutions
        - Mention if symptom is serious"""
        
        response = self.text_gen(
            prompt,
            max_length=200,
            num_return_sequences=1,
            temperature=0.6,
            do_sample=True
        )
        return response[0]['generated_text']

# Initialize helper
agri_helper = AgricultureHelper()

# Initialize Hugging Face connection
hf_api_key = os.getenv("HF_API_KEY")
if not hf_api_key:
    raise ValueError("HF_API_KEY not found in environment variables.")
login(token=hf_api_key)

def analyze_text(input_text):
    """Enhanced text analysis with agricultural focus"""
    try:
        if not agri_helper.is_agricultural(input_text):
            return "Please ask a plant or crop-related question for agricultural advice."
        
        return agri_helper.generate_response(input_text)
    except Exception as e:
        return f"Analysis error: {str(e)}"

def analyze_image(image_input):
    """Placeholder for future image analysis implementation"""
    try:
        return "Image analysis for plant diseases is coming soon. Currently please describe the symptoms in text."
    except Exception as e:
        return f"Error during image analysis: {str(e)}"

def analyze_audio(audio_path):
    """Full audio processing pipeline"""
    try:
        # Convert and transcribe audio
        wav_path = convert_audio(audio_path)
        transcribed_text = transcribe_audio(wav_path)
        
        # Translate if needed
        english_text = translate_to_english(transcribed_text)
        
        # Analyze with agricultural focus
        return analyze_text(english_text)
    except Exception as e:
        return f"Error during audio analysis: {str(e)}"