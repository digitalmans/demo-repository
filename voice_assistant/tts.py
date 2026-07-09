#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import requests
from dotenv import load_dotenv

# Try to load environment variables from the workspace root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Moark / Gitee AI API key configuration
API_KEY = os.environ.get("MOARK_API_KEY") or os.environ.get("GITEE_AI_API_KEY") or "QQFL0VLH1MMPVEOASHZAOTMJOCTXC2XHD4MWBO1Q"
BASE_URL = "https://api.moark.com/v1"

# Voice mapping based on existing speaker parameters:
# 0 -> alloy (default female), 1 -> echo, 3 -> onyx (male), 4 -> nova
SPEAKER_MAPPING = {
    0: "alloy",
    1: "echo",
    3: "onyx",
    4: "nova"
}

def tts(text, language='zh', speaker=None):
    """
    Convert text to speech using Moark's fish-speech-1.2-sft model
    :param text: Text content to convert
    :param language: 'zh' or 'en'
    :param speaker: Speaker index (0, 1, 3, 4)
    :return: Saved audio filename (result.mp3) or "error.txt" on failure
    """
    # Reload environment variables to pick up changes in .env dynamically
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    api_key = os.environ.get("MOARK_API_KEY") or os.environ.get("GITEE_AI_API_KEY") or "YOUR_MOARK_API_KEY"
    
    print(f"[TTS] Invoking Moark fish-speech-1.2-sft...")
    
    if not api_key or api_key == "YOUR_MOARK_API_KEY":
        print("[TTS] Warning: MOARK_API_KEY is not configured! Please set MOARK_API_KEY in your environment variables or root .env file.")
        with open("error.txt", "w", encoding="utf-8") as f:
            f.write("API_KEY not configured. Please set MOARK_API_KEY environment variable in your .env file.")
        return "error.txt"

    # Map the speaker index to supported preset voices
    voice = SPEAKER_MAPPING.get(speaker, "alloy")
    print(f"[TTS] Request parameters - Text length: {len(text)}, Language: {language}, Voice: {voice}")

    # Prepare API Request headers and payload
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "fish-speech-1.2-sft",
        "input": text,
        "voice": voice,
        "response_data_format": "blob"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/audio/speech",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            save_file = "result.mp3"
            with open(save_file, "wb") as f:
                f.write(response.content)
            print(f"[TTS] Successfully saved generated speech to: {save_file}")
            return save_file
        else:
            print(f"[TTS] HTTP Error {response.status_code}: {response.text}")
            with open("error.txt", "w", encoding="utf-8") as f:
                f.write(f"HTTP Error {response.status_code}: {response.text}")
            return "error.txt"

    except Exception as e:
        print(f"[TTS] Exception occurred: {e}")
        with open("error.txt", "w", encoding="utf-8") as f:
            f.write(str(e))
        return "error.txt"


if __name__ == '__main__':
    # Test block
    test_text = "您好，这是一段由模力方舟 fish-speech-1.2-sft 生成的测试语音。"
    tts(test_text)
