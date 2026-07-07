import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.prompts import OffTopicError, StylePreset as PromptStyle
from app.prompts import build_prompt
from app.providers import get_image_provider, get_speech_provider
from app.providers.speech_provider import _detect_format
from app.schemas import GenerateRequest, GenerateResponse, HealthResponse, StylePreset

app = FastAPI(
    title="潮玩文生图 API",
    description="自然语言 / 语音 → 人形卡通潮玩公仔 2D 设计图（强制 humanoid designer toy 锚点，适配后续数字人 + 3D 打印）",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(settings.output_dir)), name="outputs")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", provider=settings.image_provider, topic="chaowan")


@app.post("/api/v1/generate", response_model=GenerateResponse)
async def generate_image(body: GenerateRequest):
    width = body.width or settings.default_width
    height = body.height or settings.default_height

    try:
        prompt_data = build_prompt(
            user_prompt=body.prompt,
            style=PromptStyle(body.style.value),
            extra_suffix=body.extra_suffix,
        )
    except OffTopicError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        provider = get_image_provider()
        image_url, local_path = await provider.generate(
            prompt=str(prompt_data["prompt"]),
            negative_prompt=str(prompt_data["negative_prompt"]),
            width=width,
            height=height,
            output_dir=settings.output_dir,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"生图失败: {exc}") from exc

    return GenerateResponse(
        task_id=uuid.uuid4().hex,
        image_url=f"/outputs/{local_path.name}",
        local_path=str(local_path.resolve()),
        prompt=str(prompt_data["prompt"]),
        negative_prompt=str(prompt_data["negative_prompt"]),
        style=str(prompt_data["style"]),
        provider=settings.image_provider,
        topic=str(prompt_data["topic"]),
        normalized_subject=str(prompt_data["normalized_subject"]),
        enforced_rules=list(prompt_data["enforced_rules"]),
    )


@app.post("/api/v1/generate-from-voice", response_model=GenerateResponse)
async def generate_from_voice(
    audio: UploadFile = File(...),
    style: StylePreset = Form(default=StylePreset.chaoplay),
    width: int | None = Form(default=None),
    height: int | None = Form(default=None),
    extra_suffix: str = Form(default=""),
):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="请上传一个音频文件")

    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="上传的音频文件为空")

    max_bytes = settings.asr_max_file_size_mb * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"音频文件过大（最大 {settings.asr_max_file_size_mb} MB）",
        )

    audio_format = _detect_format(audio.filename)

    try:
        speech_provider = get_speech_provider()
        transcribed_text = await speech_provider.transcribe(audio_bytes, audio_format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"语音识别失败: {exc}") from exc

    if len(transcribed_text) < 2:
        raise HTTPException(
            status_code=422,
            detail=f"识别到的文本过短（'{transcribed_text}'），请提供更详细的语音描述",
        )

    w = width or settings.default_width
    h = height or settings.default_height

    try:
        prompt_data = build_prompt(
            user_prompt=transcribed_text,
            style=PromptStyle(style.value),
            extra_suffix=extra_suffix,
        )
    except OffTopicError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        provider = get_image_provider()
        image_url, local_path = await provider.generate(
            prompt=str(prompt_data["prompt"]),
            negative_prompt=str(prompt_data["negative_prompt"]),
            width=w,
            height=h,
            output_dir=settings.output_dir,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"生图失败: {exc}") from exc

    return GenerateResponse(
        task_id=uuid.uuid4().hex,
        image_url=f"/outputs/{local_path.name}",
        local_path=str(local_path.resolve()),
        prompt=str(prompt_data["prompt"]),
        negative_prompt=str(prompt_data["negative_prompt"]),
        style=str(prompt_data["style"]),
        provider=settings.image_provider,
        topic=str(prompt_data["topic"]),
        normalized_subject=str(prompt_data["normalized_subject"]),
        enforced_rules=list(prompt_data["enforced_rules"]),
    )


@app.get("/api/v1/prompt/preview")
async def preview_prompt(
    prompt: str,
    style: StylePreset = StylePreset.chaoplay,
    extra_suffix: str = "",
):
    """预览切题后的 prompt，不调生图 API。比赛演示可先调这个接口。"""
    try:
        return build_prompt(prompt, PromptStyle(style.value), extra_suffix)
    except OffTopicError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
