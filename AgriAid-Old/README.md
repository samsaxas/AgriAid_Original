# AgriAid – Multilingual AI Crop Disease Diagnosis

## Overview

AgriAid is an AI-powered web application that helps farmers identify possible crop diseases and receive treatment and prevention recommendations in their preferred language.

The application uses Google's Gemini AI to analyse crop symptoms through text descriptions, uploaded plant images, and audio input. Diagnosis results are presented in a structured format with disease information, model-reported confidence, treatment suggestions, and preventive measures.

AgriAid is designed to make agricultural guidance more accessible to farmers who prefer using regional languages.

## Key Features

### Multilingual Interface
- Supports 8 configured languages: English, Hindi, Bengali, Gujarati, Kannada, Punjabi, Tamil, and Telugu.
- Loads interface text from the corresponding JSON files in the `translations/` folder.
- Updates navigation, labels, buttons, and other interface text when the user changes the selected language.
- Returns diagnosis content in the selected language.

### Multiple Input Methods
- **Text:** Describe visible crop symptoms in your own words.
- **Image:** Upload a photograph of an affected plant for visual analysis.
- **Audio:** Provide a spoken description of the crop problem.

### Gemini-Powered Diagnosis
- Analyses crop symptoms and plant images using Google's Gemini API.
- Identifies a possible disease and provides a short explanation.
- Returns treatment and prevention recommendations.
- Uses retry and fallback handling for temporary model or API failures.

### Accessible Results
- Displays the diagnosis in structured sections.
- Shows the confidence value returned by the model.
- Supports audio playback of the diagnosis.
- Provides options to listen to, copy, and print the result.

### Responsive Interface
- Provides a simple interface for farmers.
- Supports desktop and mobile screen sizes.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| AI analysis | Google Gemini API |
| Language resources | JSON translation files |
| API server | Uvicorn |
| Containerisation | Docker |

## Application Workflow

1. Select a language from the language menu.
2. Choose text, image, or audio input.
3. Enter symptoms, upload a crop image, or provide an audio description.
4. Submit the information for Gemini-based analysis.
5. Review the possible disease, confidence value, treatment, and prevention guidance in the selected language.

## Results and Evaluation

The screenshots below show the application interface and example diagnosis outputs in different languages.

### Functional Results

- **Language configuration:** The interface provides 8 language options backed by translation JSON files.
- **Input coverage:** The application provides 3 input methods: text, image, and audio.
- **Diagnosis output:** Results are organised into disease identification, treatment, and prevention information.
- **Accessibility:** Diagnosis content can be played as audio, and the interface provides copy and print actions.
- **Example model confidence:** The sample diagnosis screens display a confidence value of 90%. This is the confidence reported for those individual outputs; it is **not** a measured model accuracy.

### Metrics and Their Interpretation

| Metric | Observed result | Interpretation |
|---|---:|---|
| Configured interface languages | 8 | Count of language options shown by the application |
| Supported input methods | 3 | Text, image, and audio |
| Example diagnosis confidence | 90% | Model-reported confidence shown in the sample screenshots |
| Independently measured diagnostic accuracy | Not yet measured | Requires a labelled test dataset and a defined evaluation procedure |
| Precision, recall, and F1-score | Not yet measured | Require ground-truth disease labels and prediction-level evaluation |
| Average response time | Not yet measured | Should be calculated across repeated requests and reported with the test conditions |

**Evaluation note:** A model-reported confidence score should not be interpreted as diagnostic accuracy. To report accuracy, precision, recall, or F1-score, evaluate predictions against a labelled test set. Response-time measurements should also specify the number of requests, input type, model, and network conditions.

## Screenshots

### 1. Diagnosis Results

The following screenshots show example diagnosis outputs and the information presented to the user.

![image](https://github.com/user-attachments/assets/59365fb2-6553-4c31-871c-c105d62789f7)

![image](https://github.com/user-attachments/assets/e41e077e-2057-4de7-bb7b-ca1b9eefe2e7)

![image](https://github.com/user-attachments/assets/5cebd2fb-ec6e-4c31-a777-d2ff6effd3f6)

![image](https://github.com/user-attachments/assets/2ede25f4-ad77-4b54-8d49-0739de36499f)

### 2. Application Interface

The following screenshots show the main application interface and its informational sections.

![app3](https://github.com/user-attachments/assets/567b25d3-df2a-481e-ba68-292420586d1b)

![app5](https://github.com/user-attachments/assets/065e6c49-ea28-4c4f-b17e-afeee54fa5c4)

## Project Structure

The repository includes the FastAPI backend, frontend assets, language resources, tests, and Docker configuration. The main components include:

- `backend/app/` – FastAPI application and backend modules.
- `frontend/` – HTML, CSS, and JavaScript interface.
- `translations/` – JSON files containing interface translations for supported languages.
- `tests/` – Application and API tests.
- `eval/` – Evaluation-related files.
- `Dockerfile` – Container build configuration.
- `.env.example` – Example environment variable configuration.

## Setup and Execution

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AgriAid
```

### 2. Configure Environment Variables

Create a `.env` file using `.env.example` as a reference and add your Gemini API key:

```env
GEMINI_API_KEY=your-gemini-api-key
```

Do not commit the `.env` file or expose your API key publicly.

### 3. Run with Docker

Build and start the application using the repository's Docker configuration:

```bash
docker compose up --build
```

Use the host address and port configured in the Docker Compose file to open the application.

## Limitations

- Diagnosis is AI-generated and should be treated as preliminary guidance, not a confirmed laboratory diagnosis.
- Output quality can be affected by image clarity, lighting, visible symptoms, and the completeness of the user's description.
- Model confidence is not a substitute for evaluation against verified disease labels.
- Gemini API availability, rate limits, and network conditions can affect response time and availability.
- Farmers should consult an agricultural expert when symptoms are severe or the diagnosis is uncertain.

## Future Improvements

- Build a labelled evaluation dataset and report accuracy, precision, recall, and F1-score.
- Measure response time across text, image, and audio requests.
- Expand crop and disease coverage.
- Validate translation quality with native speakers.
- Continue improving retry and fallback behaviour for model/API failures.

---

**AgriAid – Multilingual AI assistance for accessible crop disease diagnosis.**
