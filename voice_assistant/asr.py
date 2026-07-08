#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Try to load environment variables from the workspace root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def asr(audio_file, auto_detect_language=True):
    """
    Transcribe audio file to text using Moark's whisper-large-v3 model
    :param audio_file: Path to the audio file
    :param auto_detect_language: Handled by Moark API automatically
    :return: Transcribed text
    """
    print(f"[ASR] Transcribing file: {audio_file} via Moark whisper-large-v3...")
    
    # Reload environment variables to pick up changes in .env dynamically
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    api_key = os.environ.get("MOARK_API_KEY") or os.environ.get("GITEE_AI_API_KEY")
    
    if not api_key or api_key == "YOUR_MOARK_API_KEY":
        raise ValueError("MOARK_API_KEY is not configured! Please configure it in your .env file.")

    # Initialize OpenAI client with Moark endpoint
    client = OpenAI(
        base_url="https://api.moark.com/v1",
        api_key=api_key
    )

    try:
        with open(audio_file, "rb") as f:
            response = client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3",
                temperature=0.0  # Use 0.0 for maximum transcription consistency and accuracy
            )
            
            # Response contains the transcribed text
            text = response.text.strip() if hasattr(response, 'text') else str(response)
            print(f"[ASR] Transcription result: {text}")
            return text
            
    except Exception as e:
        print(f"[ASR] Error during transcription: {e}")
        raise e


if __name__ == '__main__':
    print('ASR module initialized with Moark whisper-large-v3 model.')
