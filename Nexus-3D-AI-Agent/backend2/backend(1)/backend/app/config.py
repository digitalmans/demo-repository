from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    image_provider: str = "dashscope"
    dashscope_api_key: str = ""
    dashscope_model: str = "wan2.7-image"
    dashscope_api_url: str = ""
    dashscope_size: str = ""
    dashscope_watermark: bool = False
    dashscope_thinking_mode: bool = True

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "dall-e-3"
    custom_api_url: str = ""
    custom_api_key: str = ""

    asr_provider: str = "dashscope"
    dashscope_asr_model: str = "sensevoice-v1"
    dashscope_asr_api_url: str = ""
    openai_asr_model: str = "whisper-1"
    asr_max_file_size_mb: int = 10

    host: str = "0.0.0.0"
    port: int = 8000
    output_dir: Path = Path("./outputs")

    default_width: int = 1024
    default_height: int = 1024


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
