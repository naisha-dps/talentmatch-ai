# =============================================================
# utils/voice_utils.py
# TalentMatch AI - Voice Processing Core Engine (Free Architecture Tier)
# =============================================================
import os
import re
import asyncio
import edge_tts
from groq import Groq

def analyze_candidate_audio(audio_bytes: bytes, api_key: str) -> dict:
    """
    Transcribes candidate audio bytes using the free Groq Whisper-large-v3 model
    and extracts basic delivery/fluency metrics.
    """
    if not api_key:
        raise ValueError("Groq API key validation failed: Secret key missing.")

    client = Groq(api_key=api_key)
    temp_file = "temp_candidate_speech.wav"
    
    try:
        # Write audio stream buffer safely to local directory
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)
            
        # Stream the audio binary data straight to the Groq Whisper infrastructure
        with open(temp_file, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(temp_file), file.read()),
                model="whisper-large-v3",
                response_format="json"
            )
        
        text = transcription.text
        
        # Calculate dynamic vocal pacing telemetry markers (stalling phrases)
        fillers = len(re.findall(r'\b(uh|um|like|ah|eh)\b', text.lower()))
        score = max(50, 100 - (fillers * 5))
        
        return {
            "transcript": text,
            "filler_count": fillers,
            "confidence_score": score
        }
        
    finally:
        # Guarantee physical file cache deletion to keep workspace clean
        if os.path.exists(temp_file):
            os.remove(temp_file)


def generate_agent_speech(text_payload: str) -> bytes:
    """
    Synthesizes conversational text-to-speech using Microsoft's open edge-tts cloud 
    pipeline natively for free. Returns raw audio bytes stream.
    """
    temp_response_file = "temp_agent_response.mp3"
    
    try:
        # Invoke asynchronous Edge TTS communicator using a natural corporate male profile voice
        communicate = edge_tts.Communicate(text_payload, "en-US-BrianNeural")
        asyncio.run(communicate.save(temp_response_file))
        
        # Ingest the newly synthesized byte file payload into runtime memory
        with open(temp_response_file, "rb") as f:
            audio_data = f.read()
            
        return audio_data
        
    finally:
        # Unlink media asset file tracking logs instantly
        if os.path.exists(temp_response_file):
            os.remove(temp_response_file)