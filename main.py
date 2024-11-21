from fastapi import FastAPI, HTTPException, WebSocket,Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import base64
import io
import numpy as np
import torch
from transformers import VitsTokenizer, VitsModel
import os
import scipy.io.wavfile as wavfile
import speech_recognition as sr
from logger import logging
from datetime import datetime
import time
import asyncio
import json
from s3_syncer import S3Sync

app = FastAPI()


AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
TRAINING_BUCKET_NAME = "focus-tts-stt"  # focus-transcribe

# Initialize S3 Syncer
s3_sync = S3Sync(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load model and tokenizer
access_token = os.getenv('HF_TOKEN')
tokenizer = VitsTokenizer.from_pretrained("facebook/mms-tts-eng", token=access_token)
model = VitsModel.from_pretrained("facebook/mms-tts-eng", token=access_token)

save_dir = f"transcriptions/artifacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
text_stats = {"start_time": None, "total_duration": 0, "processing_time": 0, "total_words": 0}
call_stats = {
    "start_time": None,
    "total_duration": 0,
    "processing_time": 0,
    "total_words": 0,
    "speakers_words": {}
}
complete_transcription = ""
speakers_transcription = []

def save_transcription_to_file(speaker_transcription , output_dir, filename="transcriptions.txt"):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), "a") as file:
        for transcript in speaker_transcription:
            file.write(f"{transcript}\n")
    file.close()
def save_tts_stats_to_json(tts_stats, output_dir,filename="tts_stats.json"):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), "w") as file:
        json.dump(tts_stats, file, indent=4)
    file.close()

def save_stats_to_json(stats, output_dir,filename="stats.json"):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), "w") as file:
        json.dump(stats, file, indent=4)
    file.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logging.info("Serving root HTML page")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/text-to-speech")
async def text_to_speech(data: dict):
    global call_stats
    try:
        text = data.get("text")
        stats = data.get("stats")
        speaker_transcript = data.get("speakers_transcription")
        call_stats = stats
        print("Stats:",stats)
        print("Type:", type(stats))
        print("Transcript:",speaker_transcript)
        print("Type:", type(speaker_transcript))
        logging.info(f"Speech to text Stats:{stats}")
        logging.info(f"Speech to text Transcript:{speaker_transcript}")

        text_stats["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text_stats["total_words"] = len(text.split()) if text else 0
        process_start = time.time()
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        waveform = outputs.waveform.squeeze()
        text_stats["total_duration"] = waveform.size(0) / model.config.sampling_rate
        waveform_np = (waveform.numpy() * 32767).astype(np.int16)
        buffer = io.BytesIO()
        wavfile.write(buffer, rate=model.config.sampling_rate, data=waveform_np)
        buffer.seek(0)

        audio_base64 = base64.b64encode(buffer.read()).decode()
        text_stats["processing_time"] = time.time() - process_start

        logging.info(f"Text to speech stats: {text_stats}")
        logging.info("Store transcriptions Locally")
        save_tts_stats_to_json(text_stats, save_dir)
        save_transcription_to_file(speaker_transcription=speaker_transcript, output_dir=save_dir)
        save_stats_to_json(stats=stats, output_dir=save_dir)
        
        s3_sync.sync_folder_to_s3(folder=save_dir, aws_bucket_name=TRAINING_BUCKET_NAME)
        logging.info("Store transcriptions into s3")
        logging.info("Store the speech to text stats and text to speech stats into s3")

        return JSONResponse({"audio": audio_base64, "stats":text_stats})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.websocket("/transcribe")
# async def live_transcribe(websocket: WebSocket):
#     global save_dir
#     global speakers_transcription

#     await websocket.accept()
#     logging.info("Initialize the recognizer")
#     recognizer = sr.Recognizer()

#     call_stats["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     process_start = time.time()

#     # Track which speaker is speaking (start with speaker 1)
#     current_speaker = 1

#     # Use the microphone as the audio source
#     with sr.Microphone() as source:
#         logging.info("Adjusting for ambient noise... Please wait.")
#         #recognizer.adjust_for_ambient_noise(source)
        
#         logging.info("You can start speaking now...")
#         message = await websocket.receive_text()
#         data = json.loads(message)
#         if data['type'] == 'start':
#             current_speaker = data['speakerId']
#             logging.info(f"Started recording for Speaker {current_speaker}")

#         while True:
#             try:
#                 # Capture audio from the microphone
#                 #audio = recognizer.listen(source , timeout=5, phrase_time_limit=10)
#                 audio = recognizer.listen(source)                     
#                 # Recognize speech using Google Web Speech API
#                 text = recognizer.recognize_google(audio)
                
#                 # Check if the user wants to stop via voice command
#                 if "stop listening" in text.lower():
#                     call_stats["total_duration"] = time.time() - process_start
#                     await websocket.send_text(json.dumps({
#                         "type": "stats",
#                         "data": call_stats
#                     }))
#                     logging.info("Stopping transcription by voice command.")
#                     break
#                 await websocket.send_text(text)
#                 process_end = time.time()
#                 logging.info(f"Transcription: {text}")

#                 call_stats["processing_time"] += (process_end - process_start)
#                 word_count = len(text.split())
#                 call_stats["total_words"] += word_count

#                 if current_speaker not in call_stats["speakers_words"]:
#                     call_stats["speakers_words"][current_speaker] = 0
#                 call_stats["speakers_words"][current_speaker] += word_count

#                 # Update stats and send them
#                 jsondata = json.dumps({
#                     'type': 'stats',
#                     'data': call_stats
#                 })
#                 await websocket.send_text(jsondata)

#                 speakers_transcription.append(f"Speaker{current_speaker}: {text}")
#                 await asyncio.sleep(0.1)

#             except sr.UnknownValueError:
#                 await websocket.send_text("")
#             except sr.RequestError as e:
#                 await websocket.send_text(json.dumps({
#                     "type": "error",
#                     "data": f"Could not request results; {e}"
#                 }))
#         save_stats_to_json(call_stats,save_dir)
#         save_transcription_to_file(speakers_transcription, save_dir)
#         s3_sync.sync_folder_to_s3(folder = save_dir, aws_bucket_name=TRAINING_BUCKET_NAME)
        # logging.info("Store transcriptions into s3")
        # logging.info("Store the speech to text stats into s3")

@app.get("/get-stats")
async def get_stats():
    global call_stats
    return {"stats": f"{call_stats}"}

@app.post("/reset-stats")
async def reset_stats():
    global call_stats
    call_stats = {
        "duration": 0,
        "processingTime": 0,
        "totalWords": 0,
        "speakerWords": {}
    };
    return {"status": "Stats reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
