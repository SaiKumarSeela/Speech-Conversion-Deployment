# Speech Processing Application

This application provides real-time **Speech-to-Text** transcription and **Text-to-Speech** synthesis. Leveraging FastAPI for backend processing, it allows users to convert text input to audio and transcribe speech to text using WebSocket for live updates.

## Features

- **Text-to-Speech (TTS)**: Converts user-input text into spoken audio using meta's .
- **Speech-to-Text (STT)**: Records live audio and transcribes it to text in real time.
- **Voice Command Stop**: Allows stopping the recording by saying "stop listening."
- **WebSocket Communication**: Enables live transcription with immediate text display.

## Models
- **Text-to-Speech Model**: Uses VITS (Variational Inference Text-to-Speech) model, specifically Facebook’s MMS-TTS (Multilingual Speech Synthesis) model available on Hugging Face, to generate natural-sounding audio from text input. This model is accessed through the Hugging Face API, requiring an authentication token.

- **Speech-to-Text Model**: The Google Web Speech API is used for real-time speech recognition, allowing accurate and responsive transcription of spoken language.

## Project Demo
[![SpeechProcessinAppUIwithOS](https://github.com/user-attachments/assets/5c333fd2-e376-4cd9-a090-4d3e63dc7514)](https://github.com/user-attachments/assets/5fd62bfd-5fdb-4475-8acb-de0a18a14def)

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: FastAPI (Python), WebSocket
- **Models**: VITS Text-to-Speech model (via Hugging Face)
- **Dependencies**: `transformers`, `torch`, `speech_recognition`, `scipy`

## Installation

1. **Clone the Repository**
    ```bash
    git clone https://github.com/SaiKumarSeela/Speech-Processing-with-Open-Source
    cd Speech-Processing-with-Open-Source
    ```

2. **Install Requirements**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set Up Environment Variables**
   - Get a Hugging Face API token and set it as an environment variable `HF_TOKEN`.

4. **Run the Application**
    ```bash
    uvicorn app:app --host 0.0.0.0 --port 8000
    ```
## Usage

1. **Text-to-Speech Conversion**
   - Navigate to the **Text-to-Speech** section in the UI.
   - Enter the desired text in the provided input box.
   - Click on **Convert to Speech** to generate and play the audio.
  
2. **Speech-to-Text Transcription**
   - Click **Start Recording** to begin capturing audio.
   - Speak clearly into the microphone; transcription will display in real-time.
   - Say "stop listening" or click **Stop Recording** to end the recording.

## API Endpoints
- **GET /**: Loads the main HTML page.
- **POST /text-to-speech**: Accepts text input, generates audio, and returns it as a base64-encoded string.
- **WebSocket /transcribe**: Establishes a WebSocket connection for live transcription.
- **POST /stop-recording**: Sets a global flag to halt recording.


