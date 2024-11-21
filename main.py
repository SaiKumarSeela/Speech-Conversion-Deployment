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
