import streamlit as st
import os
from PIL import Image  # Used for image processing
from utils.gemini_api import analyze_text, analyze_image
from utils.translation_loader import load_translations, get_language_options
from utils.translation import translate_to_english, translate_from_english
from utils.gemini_audio import generate_speech, get_audio_download_link, get_audio_player_html, transcribe_audio_with_gemini


# Import required libraries
from datetime import datetime
api_key = st.secrets["GEMINI_API_KEY"]
# Streamlit setup
st.set_page_config(
    page_title="AgriAid",
    layout="wide",  # Changed back to wide for website appearance
    page_icon="🌱"
)

# Apply custom styling to match mobile app
st.markdown(
    """
    <style>
    /* Main app styling with agriculture-themed colors */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f8fff8;
        color: #2e5d2e;
    }

    .stApp {
        background-color: #f8fff8;
    }

    /* Ensure text is visible with proper agriculture-themed colors */
    .stMarkdown, p, span, label, div {
        color: #2e5d2e !important;
    }

    /* Styling for links */
    a {
        color: #4CAF50 !important;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    /* Website container with proper website styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 80px;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Add a subtle header background */
    header {
        background-color: #f0f7f0;
        border-bottom: 1px solid #e0e9e0;
        margin-bottom: 20px;
    }

    /* Main content area styling */
    .main .block-container {
        background-color: white;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e0e9e0;
    }

    /* Header styling */
    h1 {
        color: #333333;
        font-size: 28px;
        font-weight: 600;
        margin-bottom: 20px;
    }

    h2, h3 {
        color: #333333;
        font-weight: 600;
    }

    /* Card styling for diagnosis results - more website-like */
    .diagnosis-card {
        background-color: white;
        border-radius: 8px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }

    /* Section headers - more website-like */
    .section-header {
        display: flex;
        align-items: center;
        font-weight: 600;
        color: #333333;
        margin-bottom: 15px;
        padding: 12px 15px;
        background-color: #f0f7f0;
        border-radius: 6px;
        border-left: 4px solid #4CAF50;
    }

    /* Back button styling */
    .back-button {
        display: flex;
        align-items: center;
        color: #4CAF50;
        font-weight: 500;
        margin-bottom: 15px;
        text-decoration: none;
    }

    /* Primary button styling with agriculture theme */
    .stButton > button.primary {
        background-color: #4CAF50 !important;
        color: white !important;
        border-radius: 4px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        border: none !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        transition: background-color 0.3s !important;
    }

    .stButton > button.primary:hover {
        background-color: #3d9140 !important;
    }

    .stButton > button {
        border-radius: 4px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        border: 1px solid #4CAF50 !important;
        color: #4CAF50 !important;
        background-color: white !important;
        transition: all 0.3s !important;
    }

    .stButton > button:hover {
        background-color: #f0f7f0 !important;
    }

    /* Audio button styling */
    .audio-button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* Confidence indicator */
    .confidence-indicator {
        background-color: #E3F2FD;
        color: #2196F3;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 14px;
        display: inline-block;
    }

    /* Audio player styling */
    audio {
        width: 100%;
        border-radius: 8px;
        background-color: #f1f1f1;
        margin: 10px 0;
    }

    /* Read All Content button */
    .read-all-button {
        background-color: #4CAF50;
        color: white;
        padding: 12px 20px;
        text-align: center;
        text-decoration: none;
        display: block;
        width: 100%;
        border-radius: 8px;
        margin-top: 15px;
        font-weight: 500;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Website footer navigation */
    .bottom-nav {
        display: flex;
        justify-content: center;
        background-color: white;
        padding: 15px 0;
        margin-top: 30px;
        border-top: 1px solid #e0e0e0;
    }

    .nav-item {
        display: flex;
        align-items: center;
        color: #555555;
        text-decoration: none;
        font-size: 14px;
        margin: 0 20px;
        padding: 8px 15px;
        border-radius: 4px;
        transition: background-color 0.2s;
    }

    .nav-item:hover {
        background-color: #f0f7f0;
    }

    .nav-item.active {
        color: #4CAF50;
        font-weight: 500;
    }

    /* Form elements styling with agriculture theme */
    .stTextArea textarea {
        border-radius: 4px !important;
        border-color: #4CAF50 !important;
        background-color: white !important;
        color: #2e5d2e !important;
        padding: 12px !important;
        font-size: 16px !important;
    }

    .stTextArea textarea:focus {
        box-shadow: 0 0 0 1px #4CAF50 !important;
    }

    .stFileUploader > div {
        border-radius: 4px !important;
        border-color: #4CAF50 !important;
        background-color: white !important;
    }

    /* Selectbox styling */
    .stSelectbox > div > div > div {
        background-color: white !important;
        border-color: #4CAF50 !important;
        color: #2e5d2e !important;
    }

    /* Radio buttons */
    .stRadio > div {
        display: flex;
        gap: 15px;
        padding: 10px 0;
    }

    .stRadio label {
        font-weight: 500;
        color: #2e5d2e !important;
    }

    /* Checkbox styling */
    .stCheckbox > div > div > div {
        border-color: #4CAF50 !important;
    }

    /* Download button styling */
    .download-btn {
        display: inline-block;
        background-color: #4CAF50;
        color: white;
        padding: 10px 15px;
        text-align: center;
        text-decoration: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 500;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Add padding at the bottom to account for fixed navigation */
    .main-content {
        padding-bottom: 70px;
    }

    /* Custom container for diagnosis results */
    .diagnosis-result {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Styling for the audio solution section */
    .audio-solution {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        margin: 15px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Styling for the download options */
    .download-options {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        margin: 15px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Timestamp styling */
    .timestamp {
        color: #757575;
        font-size: 14px;
        margin-bottom: 15px;
    }

    /* Green text for remedies */
    .remedy-text {
        color: #4CAF50;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load translations
translations = load_translations()
language_options = get_language_options(translations)

# Initialize session state
if "current_lang" not in st.session_state:
    st.session_state.current_lang = None
if "translations" not in st.session_state:
    st.session_state.translations = translations
if "audio_output" not in st.session_state:
    st.session_state.audio_output = None
if "audio_generated" not in st.session_state:
    st.session_state.audio_generated = False

# Language selection page
if not st.session_state.current_lang:
    # Create a more visually appealing language selection page
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2e5d2e; margin-bottom: 10px;">🌱 Welcome to AgriAid</h1>
        <p style="font-size: 18px; color: #4CAF50;">Your agricultural disease diagnosis assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # Create a card-like container for language selection
    st.markdown("""
    <div style="background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #e0e9e0;">
        <h2 style="color: #2e5d2e; margin-bottom: 20px;">🌍 Select Your Language</h2>
    """, unsafe_allow_html=True)

    # Auto-generate language options
    lang = st.selectbox(
        "Choose your preferred language",
        options=list(language_options.keys()),
        format_func=lambda x: language_options[x],
        key="language_selectbox"
    )

    # Add some information about the app
    st.markdown("""
    <div style="margin-top: 20px; padding: 15px; background-color: #f0f7f0; border-radius: 6px; border-left: 4px solid #4CAF50;">
        <p style="margin: 0; color: #2e5d2e;">
            <strong>AgriAid</strong> helps you diagnose crop diseases and provides treatment recommendations.
            Simply upload an image, describe symptoms, or record audio to get started.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Close the card container
    st.markdown("</div>", unsafe_allow_html=True)

    # Center the continue button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Continue", type="primary", use_container_width=True):
            st.session_state.current_lang = lang
            st.rerun()

    # Add a footer
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; color: #666;">
        <p>Powered by AI for sustainable agriculture</p>
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# Main app after language selection
current_translation = st.session_state.translations[st.session_state.current_lang]
strings = current_translation['strings']
instructions = current_translation['instructions']

def get_diagnosis(input_data, input_mode):
    try:
        with st.spinner(strings["analyzing"]):
            if input_mode == "text":
                if not input_data.strip():
                    return None
                translated = translate_to_english(input_data)
                diagnosis = analyze_text(translated)
            elif input_mode == "image":
                diagnosis = analyze_image(input_data)
            elif input_mode == "audio":
                # Process audio using Gemini API
                try:
                    # Use the Gemini API to transcribe the audio
                    from utils.gemini_audio import transcribe_audio_with_gemini
                    import logging
                    import google.generativeai as genai

                    # Set up more detailed logging
                    logging.basicConfig(level=logging.INFO)
                    logger = logging.getLogger("crop_disease_app")

                    # Detect if this is likely a WAV file from Streamlit's recorder
                    mime_type = "audio/mpeg"  # Default
                    if input_data[:4] == b'RIFF' and b'WAVE' in input_data[:12]:
                        mime_type = "audio/wav"
                        logger.info("Detected WAV format from audio recorder")

                        # Save the audio to a temporary file for debugging
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            tmp_file.write(input_data)
                            tmp_path = tmp_file.name
                            logger.info(f"Saved audio to temporary file for debugging: {tmp_path}")

                    # Log audio details
                    logger.info(f"Audio data size: {len(input_data)} bytes")
                    logger.info(f"Audio mime_type: {mime_type}")

                    # Transcribe the audio directly using Gemini API
                    logger.info("Starting audio transcription...")
                    transcribed = transcribe_audio_with_gemini(input_data, mime_type)

                    if not transcribed or transcribed.strip() == "":
                        logger.warning("Transcription failed or returned empty text")

                        # Try one more time with a different approach
                        logger.info("Trying alternative transcription approach...")
                        from google.generativeai.types import generation_types

                        # Create a more specific model configuration
                        model = genai.GenerativeModel(
                            'gemini-1.5-flash-latest',
                            generation_config=generation_types.GenerationConfig(
                                temperature=0.1,
                                top_p=0.95,
                                top_k=40,
                                max_output_tokens=1024,
                            )
                        )

                        # Try with a different prompt
                        response = model.generate_content(
                            [
                                "This is an audio recording about plant diseases or agricultural problems. Please transcribe it word for word:",
                                {
                                    "mime_type": mime_type,
                                    "data": input_data
                                }
                            ]
                        )

                        transcribed = response.text
                        logger.info(f"Second attempt transcription result: {transcribed[:100]}...")

                        if not transcribed or transcribed.strip() == "":
                            logger.error("Both transcription attempts failed")
                            # Provide a default diagnosis if transcription fails
                            diagnosis = """🩺 Diagnosis: Since I couldn't transcribe your audio, here are common crop issues:
                            - Fungal diseases (powdery mildew, leaf spot)
                            - Pest infestations (aphids, whiteflies, spider mites)
                            - Nutrient deficiencies (nitrogen, phosphorus, potassium)

                            💊 Remedies:
                            1. Inspect plants carefully to identify specific symptoms
                            2. For fungal issues: Apply appropriate fungicide, improve air circulation
                            3. For pests: Use insecticidal soap or neem oil
                            4. For nutrient deficiencies: Apply balanced fertilizer
                            5. Remove severely affected plant parts

                            🌱 Prevention:
                            1. Maintain proper spacing between plants for airflow
                            2. Use disease-resistant varieties when possible
                            3. Practice crop rotation and regular soil testing"""
                        else:
                            logger.info(f"Second attempt successful: {transcribed[:100]}...")
                            # Process the transcribed text
                            translated = translate_to_english(transcribed)
                            diagnosis = analyze_text(translated)
                    else:
                        logger.info(f"Successfully transcribed audio: {transcribed[:100]}...")
                        # Process the transcribed text
                        translated = translate_to_english(transcribed)
                        diagnosis = analyze_text(translated)

                except Exception as e:
                    logger.error(f"Error processing audio: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())

                    # If any error occurs during transcription or analysis, provide a default diagnosis
                    diagnosis = f"""🩺 Diagnosis: Common crop issues:
                    - Fungal diseases (powdery mildew, leaf spot)
                    - Pest infestations (aphids, whiteflies, spider mites)
                    - Nutrient deficiencies (nitrogen, phosphorus, potassium)

                    💊 Remedies:
                    1. Inspect plants carefully to identify specific symptoms
                    2. For fungal issues: Apply appropriate fungicide, improve air circulation
                    3. For pests: Use insecticidal soap or neem oil
                    4. For nutrient deficiencies: Apply balanced fertilizer
                    5. Remove severely affected plant parts

                    🌱 Prevention:
                    1. Maintain proper spacing between plants for airflow
                    2. Use disease-resistant varieties when possible
                    3. Practice crop rotation and regular soil testing"""

            if not diagnosis or "error" in diagnosis.lower():
                return strings.get("analysis_error", "Could not analyze the input. Please try again with more detailed information.")

            translated_diagnosis = translate_from_english(diagnosis, st.session_state.current_lang)

            # Generate audio for the diagnosis
            with st.spinner(strings.get("generating_audio", "Generating audio solution...")):
                try:
                    # Try to generate speech with the detected language
                    st.session_state.audio_output = generate_speech(translated_diagnosis,
                                                                  lang=st.session_state.current_lang[:2] if st.session_state.current_lang else 'en')
                    st.session_state.audio_generated = True
                except Exception as e:
                    # If speech generation fails, try with English
                    try:
                        st.session_state.audio_output = generate_speech(translated_diagnosis, lang='en')
                        st.session_state.audio_generated = True
                    except Exception as e2:
                        # If that also fails, log the error but don't show it to the user
                        print(f"Error generating speech: {e2}")
                        st.session_state.audio_generated = False

            return translated_diagnosis

    except Exception as e:
        st.error(f"{strings['error']} {str(e)}")
        return None

# Main app layout
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
    <h1>{strings["title"]}</h1>
    <div style="color: #FF5252; font-size: 24px;"></div>
</div>
""", unsafe_allow_html=True)

# Add a container with main-content class for proper padding
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Tabs for input types
input_type = st.radio(
    strings["input_type"],
    ["Text", "Image", "Audio"],
    horizontal=True
)

if input_type == "Text":
    user_input = st.text_area(
        strings["describe_issue"],
        height=150,
        placeholder=strings["text_placeholder"]
    )

    if st.button(strings["diagnose"], type="primary"):
        if user_input.strip():
            # Reset audio generation flag
            st.session_state.audio_generated = False

            output = get_diagnosis(user_input, "text")   # Pass user_input directly
            if output:
                # Display diagnosis result in a card format like mobile app
                st.markdown("""
                <div class="diagnosis-card">
                    <h2>Diagnosis Result</h2>
                    <div class="timestamp">
                        """ + datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p") + """
                    </div>
                """, unsafe_allow_html=True)

                # Extract disease name from output (first line or best guess)
                import re
                disease_match = re.search(r'(.*?)(Disease|Infection|Deficiency|Pest)', output, re.IGNORECASE)
                disease_name = disease_match.group(0) if disease_match else "Plant Issue"

                # Extract confidence if present
                confidence_match = re.search(r'Confidence:\s*(\d+)%', output, re.IGNORECASE)
                confidence = confidence_match.group(1) if confidence_match else "85"

                # Display disease name and confidence
                st.markdown(f"""

                """, unsafe_allow_html=True)

                # Format the diagnosis text to ensure each point is on a new line
                import re

                # Replace diagnosis points with properly formatted HTML
                formatted_output = output

                # Format diagnosis points (1. Point, 2. Point) to be on separate lines
                diagnosis_section = re.search(r'(🩺 Diagnosis:.*?)(?=💊 Remedies:|$)', formatted_output, re.DOTALL)
                if diagnosis_section:
                    diagnosis_text = diagnosis_section.group(1)
                    # Find all numbered points in the diagnosis section
                    numbered_points = re.findall(r'(\d+\.\s+[^0-9]+?)(?=\d+\.|$)', diagnosis_text, re.DOTALL)
                    if numbered_points:
                        # Create a replacement with each point on a new line
                        replacement = "🩺 Diagnosis:<br>"
                        for point in numbered_points:
                            replacement += f"{point.strip()}<br>"
                        # Replace the diagnosis section
                        formatted_output = formatted_output.replace(diagnosis_text, replacement)

                # Display the formatted diagnosis text
                st.markdown(f"""
                <div>
                    {formatted_output}
                </div>
                </div>
                """, unsafe_allow_html=True)

                # Display audio solution if generated
                if st.session_state.get("audio_generated") and st.session_state.audio_output:
                    st.markdown("""
                    <div class="audio-solution">
                    """, unsafe_allow_html=True)

                    # Add audio player with controls
                    audio_player = get_audio_player_html(st.session_state.audio_output)
                    st.markdown(audio_player, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                    # Add download options for the audio
                    st.markdown("""
                    <div class="download-options">
                        <h3>Download Options</h3>
                        <p>Save the audio solution to your device:</p>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        filename = st.text_input(strings.get("filename_label", "Filename for download:"),
                                                "solution_audio.mp3", key="text_filename")
                    with col2:
                        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
                        download_link = get_audio_download_link(
                            st.session_state.audio_output,
                            filename=filename,
                            text=strings.get("download_audio", "Download Audio")
                        )
                        st.markdown(download_link, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                    # No need for "Read All Content" button
        else:
            st.warning(strings["warning"])

elif input_type == "Image":
    uploaded_image = st.file_uploader(
        strings["upload_image"],
        type=["jpg", "jpeg", "png"]
    )

    if uploaded_image:
        # Display the image in a card-like container
        st.markdown("""
        <div class="diagnosis-card">
        """, unsafe_allow_html=True)

        # Display the image
        st.image(uploaded_image, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button(strings["diagnose"], type="primary"):
            # Reset audio generation flag
            st.session_state.audio_generated = False

            output = get_diagnosis(uploaded_image.getvalue(), "image")
            if output:
                # Add back button like in mobile app


                # Display diagnosis result in a card format like mobile app
                st.markdown("""
                <div class="diagnosis-card">
                    <h2>Diagnosis Result</h2>
                    <div class="timestamp">
                        """ + datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p") + """
                    </div>
                """, unsafe_allow_html=True)

                # Display the image again
                st.image(uploaded_image, use_container_width=True)

                # Extract disease name from output (first line or best guess)
                import re
                disease_match = re.search(r'(.*?)(Disease|Infection|Deficiency|Pest)', output, re.IGNORECASE)
                disease_name = disease_match.group(0) if disease_match else "Plant Issue"

                # Extract confidence if present
                confidence_match = re.search(r'Confidence:\s*(\d+)%', output, re.IGNORECASE)
                confidence = confidence_match.group(1) if confidence_match else "85"

                # Display disease name and confidence
                st.markdown(f"""
                <div style="margin-bottom: 20px;">
                    <span>Confidence: </span>
                    <span class="confidence-indicator">{confidence}%</span>
                </div>
                """, unsafe_allow_html=True)

                # Format the diagnosis text to ensure each point is on a new line
                import re

                # Replace diagnosis points with properly formatted HTML
                formatted_output = output

                # Format diagnosis points (1. Point, 2. Point) to be on separate lines
                diagnosis_section = re.search(r'(🩺 Diagnosis:.*?)(?=💊 Remedies:|$)', formatted_output, re.DOTALL)
                if diagnosis_section:
                    diagnosis_text = diagnosis_section.group(1)
                    # Find all numbered points in the diagnosis section
                    numbered_points = re.findall(r'(\d+\.\s+[^0-9]+?)(?=\d+\.|$)', diagnosis_text, re.DOTALL)
                    if numbered_points:
                        # Create a replacement with each point on a new line
                        replacement = "🩺 Diagnosis:<br>"
                        for point in numbered_points:
                            replacement += f"{point.strip()}<br>"
                        # Replace the diagnosis section
                        formatted_output = formatted_output.replace(diagnosis_text, replacement)

                # Display the formatted diagnosis text
                st.markdown(f"""
                <div>
                    {formatted_output}
                </div>
                </div>
                """, unsafe_allow_html=True)

                # Display audio solution if generated
                if st.session_state.get("audio_generated") and st.session_state.audio_output:
                    st.markdown("""
                    <div class="audio-solution">
                    """, unsafe_allow_html=True)

                    # Add audio player with controls
                    audio_player = get_audio_player_html(st.session_state.audio_output)
                    st.markdown(audio_player, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                    # Add download options for the audio
                    st.markdown("""
                    <div class="download-options">
                        <h3>Download Options</h3>
                        <p>Save the audio solution to your device:</p>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        filename = st.text_input(strings.get("filename_label", "Filename for download:"),
                                                "solution_audio.mp3", key="image_filename")
                    with col2:
                        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
                        download_link = get_audio_download_link(
                            st.session_state.audio_output,
                            filename=filename,
                            text=strings.get("download_audio", "Download Audio")
                        )
                        st.markdown(download_link, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                    # No need for "Read All Content" button

elif input_type == "Audio":
    # Create a card-like container for audio input options
    st.markdown("""
    <div class="diagnosis-card">
        <h3>Audio Input Options</h3>
    </div>
    """, unsafe_allow_html=True)

    # Create two columns for audio input methods
    col1, col2 = st.columns(2)
    audio_data = None  # Initialize audio_data
    audio_mime_type = None  # Track the mime type

    with col1:
        # File uploader with styled container
        st.markdown("""
        <div class="section-header">
            <span style="margin-right: 10px;">📁</span> Upload Audio
        </div>
        """, unsafe_allow_html=True)

        audio_file = st.file_uploader(
            "",  # Empty label since we're using custom header
            type=["mp3", "wav"]
        )
        if audio_file:
            st.audio(audio_file)
            # Store the file in session state to avoid reading it multiple times
            if "uploaded_audio" not in st.session_state:
                st.session_state.uploaded_audio = audio_file.read()
                # Reset file pointer
                audio_file.seek(0)

            audio_data = st.session_state.uploaded_audio
            # Set mime type based on file extension
            if audio_file.name.lower().endswith('.mp3'):
                audio_mime_type = "audio/mpeg"
            else:
                audio_mime_type = "audio/wav"

    with col2:
        st.markdown("""
        <div class="section-header">
            <span style="margin-right: 10px;">🎙️</span> Record Audio
        </div>
        """, unsafe_allow_html=True)

        # Use a try-except block to handle any errors with the audio recorder
        try:
            audio_recorder = st.audio_input(
                label="",  # Empty label since we're using custom header
                key="audio_recorder"
            )

            if audio_recorder is not None:
                # Display the recorded audio
                st.audio(audio_recorder)

                # Store the recorded audio in session state
                if "recorded_audio" not in st.session_state or st.session_state.recorded_audio is None:
                    # Get the bytes from the recorder
                    try:
                        # Read the bytes from the UploadedFile
                        recorder_bytes = audio_recorder.getvalue()
                        st.session_state.recorded_audio = recorder_bytes
                        st.session_state.recorded_audio_processed = False
                    except Exception as e:
                        st.error(f"Error reading audio: {e}")
                        st.session_state.recorded_audio = None

                # If we have recorded audio in the session state, use it
                if st.session_state.recorded_audio is not None:
                    audio_data = st.session_state.recorded_audio
                    audio_mime_type = "audio/wav"  # Streamlit recorder always produces WAV
        except Exception as e:
            st.error(f"Error with audio recorder: {e}")
            import traceback
            st.error(traceback.format_exc())

    # Center the diagnose button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        diagnose_button = st.button(strings["diagnose"], type="primary", use_container_width=True)

    if diagnose_button:
        if audio_data:
            # Reset audio generation flag
            st.session_state.audio_generated = False

            # Show a spinner while processing
            with st.spinner("Processing audio..."):
                output = get_diagnosis(audio_data, "audio")

            if output:
                # Add back button like in mobile app
                # Display diagnosis result in a card format like mobile app
                st.markdown("""
                <div class="diagnosis-card">
                    <h2>Diagnosis Result</h2>
                    <div class="timestamp">
                        """ + datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p") + """
                    </div>
                """, unsafe_allow_html=True)

                # Extract disease name from output (first line or best guess)
                import re
                disease_match = re.search(r'(.*?)(Disease|Infection|Deficiency|Pest)', output, re.IGNORECASE)
                disease_name = disease_match.group(0) if disease_match else "Plant Issue"

                # Extract confidence if present
                confidence_match = re.search(r'Confidence:\s*(\d+)%', output, re.IGNORECASE)
                confidence = confidence_match.group(1) if confidence_match else "85"

                # Display disease name and confidence
                st.markdown(f"""
                <div style="margin-bottom: 15px;">
                    <h2 style="color: #2e5d2e; margin-bottom: 10px;">{disease_name}</h2>
                </div>
                <div style="margin-bottom: 20px;">
                    <span>Confidence: </span>
                    <span class="confidence-indicator">{confidence}%</span>
                </div>
                """, unsafe_allow_html=True)

                # Parse the output to extract diagnosis, remedies, and prevention
                import re

                # Extract diagnosis, remedies, and prevention sections
                diagnosis_match = re.search(r'🩺 Diagnosis:(.+?)(?=💊 Remedies:|$)', output, re.DOTALL)
                remedies_match = re.search(r'💊 Remedies:(.+?)(?=🌱 Prevention:|$)', output, re.DOTALL)
                prevention_match = re.search(r'🌱 Prevention:(.+?)(?=⚠️|$)', output, re.DOTALL)

                diagnosis_text = diagnosis_match.group(1).strip() if diagnosis_match else "No diagnosis information available."
                remedies_text = remedies_match.group(1).strip() if remedies_match else "No remedies information available."
                prevention_text = prevention_match.group(1).strip() if prevention_match else "No prevention information available."

                # Format the diagnosis text to ensure each point is on a new line
                import re

                # Replace diagnosis points with properly formatted HTML
                formatted_output = output

                # Format diagnosis points (1. Point, 2. Point) to be on separate lines
                diagnosis_section = re.search(r'(🩺 Diagnosis:.*?)(?=💊 Remedies:|$)', formatted_output, re.DOTALL)
                if diagnosis_section:
                    diagnosis_text = diagnosis_section.group(1)
                    # Find all numbered points in the diagnosis section
                    numbered_points = re.findall(r'(\d+\.\s+[^0-9]+?)(?=\d+\.|$)', diagnosis_text, re.DOTALL)
                    if numbered_points:
                        # Create a replacement with each point on a new line
                        replacement = "🩺 Diagnosis:<br>"
                        for point in numbered_points:
                            replacement += f"{point.strip()}<br>"
                        # Replace the diagnosis section
                        formatted_output = formatted_output.replace(diagnosis_text, replacement)

                # Display the formatted diagnosis text
                st.markdown(f"""
                <div>
                    {formatted_output}
                </div>
                </div>
                """, unsafe_allow_html=True)

                # Display audio solution if generated
                if st.session_state.get("audio_generated") and st.session_state.audio_output:
                    st.markdown("""
                    <div class="audio-solution">
                    """, unsafe_allow_html=True)

                    # Add audio player with controls
                    audio_player = get_audio_player_html(st.session_state.audio_output)
                    st.markdown(audio_player, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                    # Add download options for the audio
                    st.markdown("""
                    <div class="download-options">
                        <h3>Download Options</h3>
                        <p>Save the audio solution to your device:</p>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        filename = st.text_input(strings.get("filename_label", "Filename for download:"),
                                                "solution_audio.mp3", key="audio_filename")
                    with col2:
                        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
                        download_link = get_audio_download_link(
                            st.session_state.audio_output,
                            filename=filename,
                            text=strings.get("download_audio", "Download Audio")
                        )
                        st.markdown(download_link, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning(strings["audio_warning"])

# Close the main-content div
st.markdown('</div>', unsafe_allow_html=True)

# Add a simple footer
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 15px; border-top: 1px solid #e0e9e0;">
    <p style="color: #4CAF50; font-size: 14px;">AgriAid - Your agricultural disease diagnosis assistant</p>
</div>
""", unsafe_allow_html=True)

# Footer and sidebar
st.caption(strings["footer"])

with st.sidebar:
    # Back button
    if st.button(f"← {strings.get('back_button', 'Back to Language Selection')}"):
        st.session_state.current_lang = None
        st.rerun()

    # Instructions
    st.markdown(f"### {strings['how_to_use']}")
    for line in instructions:
        st.markdown(f"- {line}")
    st.markdown("---")
