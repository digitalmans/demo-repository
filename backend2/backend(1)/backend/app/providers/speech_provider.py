"""
语音识别 Provider

DashScope SenseVoice / OpenAI Whisper
"""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from io import BytesIO

import httpx

from app.config import settings


class SpeechProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, audio_format: str) -> str:
        """返回转录文本"""


def _detect_format(filename: str) -> str:
    """从文件名推断音频格式，兜底 wav。"""
    mapping = {
        "wav": "wav", "wave": "wav",
        "mp3": "mp3", "mpeg": "mp3",
        "webm": "webm",
        "m4a": "m4a", "mp4": "m4a", "aac": "m4a",
        "ogg": "ogg", "oga": "ogg", "opus": "ogg",
        "flac": "flac",
        "pcm": "pcm",
    }
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return mapping.get(ext, "wav")


class DashScopeASRProvider(SpeechProvider):
    """阿里云 SenseVoice — 同步识别，base64 传音频"""

    ASR_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/asr"

    async def transcribe(self, audio_bytes: bytes, audio_format: str) -> str:
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY 未配置，无法使用 DashScope ASR")

        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        url = settings.dashscope_asr_api_url or self.ASR_URL

        headers = {
            "Authorization": f"Bearer {settings.dashscope_api_key}",
            "Content-Type": "application/json",
        }
        payload: dict = {
            "model": settings.dashscope_asr_model,
            "input": {
                "audio": audio_b64,
            },
        }
        if audio_format:
            payload["parameters"] = {"format": audio_format}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.is_error:
                try:
                    err = resp.json()
                    msg = err.get("message") or err
                except Exception:
                    msg = resp.text
                raise RuntimeError(f"DashScope ASR HTTP {resp.status_code}: {msg}")

            data = resp.json()
            if data.get("code"):
                raise RuntimeError(
                    f"DashScope ASR 失败: [{data.get('code')}] {data.get('message')}"
                )

            text = (data.get("output") or {}).get("text") or ""
            if not text.strip():
                raise RuntimeError("语音识别结果为空，请检查音频是否有有效语音内容")

            return text.strip()


class OpenAIWhisperProvider(SpeechProvider):
    """OpenAI Whisper API"""

    TRANSCRIBE_URL = "https://api.openai.com/v1/audio/transcriptions"

    async def transcribe(self, audio_bytes: bytes, audio_format: str) -> str:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY 未配置，无法使用 OpenAI Whisper")

        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        base_url = settings.openai_base_url.rstrip("/")
        url = f"{base_url}/audio/transcriptions"

        content_type = f"audio/{audio_format}" if audio_format else "audio/wav"
        files = {
            "file": (f"audio.{audio_format}", BytesIO(audio_bytes), content_type),
        }
        data = {
            "model": settings.openai_asr_model,
            "response_format": "text",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, data=data, files=files)
            if resp.is_error:
                try:
                    msg = resp.json()
                except Exception:
                    msg = resp.text
                raise RuntimeError(f"OpenAI Whisper HTTP {resp.status_code}: {msg}")

            text = resp.text.strip()
            if not text:
                raise RuntimeError("语音识别结果为空，请检查音频是否有有效语音内容")

            return text


def get_speech_provider() -> SpeechProvider:
    providers: dict[str, type[SpeechProvider]] = {
        "dashscope": DashScopeASRProvider,
        "openai": OpenAIWhisperProvider,
    }
    key = settings.asr_provider.lower()
    if key not in providers:
        raise ValueError(f"未知 ASR_PROVIDER: {key}，可选: {list(providers)}")
    return providers[key]()
