import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def generate_2d_digital_human_video(audio_path, face_path, output_path):
    """
    通过 Wav2Lip 合成 2D 数字人视频。
    如果 Wav2Lip 权重文件不存在或推理环境不具备，则自动优雅降级，使用 ffmpeg 生成静态人像+语音的音视频同步视频。
    """
    # 检查 Wav2Lip 目录下的 checkpoint 路径
    checkpoint_name = "wav2lip_288x288.pth"  # 或者 wav2lip_gan.pth
    checkpoint_dir = os.path.join(os.path.dirname(__file__), 'wav2lip_288x288', 'checkpoints')
    checkpoint_path = os.path.join(checkpoint_dir, checkpoint_name)
    
    # 尝试查找任意存在的 pth 权重
    has_checkpoint = os.path.isfile(checkpoint_path)
    if not has_checkpoint and os.path.isdir(checkpoint_dir):
        for f in os.listdir(checkpoint_dir):
            if f.endswith('.pth'):
                checkpoint_path = os.path.join(checkpoint_dir, f)
                has_checkpoint = True
                break

    # 尝试检测 GPU 与运行环境
    try:
        import torch
        has_cuda = torch.cuda.is_available()
    except ImportError:
        has_cuda = False

    # 如果有权重，尝试运行 Wav2Lip 推理
    if has_checkpoint:
        logger.info(f"Detect Wav2Lip checkpoint: {checkpoint_path}. Running inference...")
        try:
            # 准备参数执行 inference.py
            inference_script = os.path.join(os.path.dirname(__file__), 'wav2lip_288x288', 'inference.py')
            cmd = [
                os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe'),
                inference_script,
                '--checkpoint_path', checkpoint_path,
                '--face', face_path,
                '--audio', audio_path,
                '--outfile', output_path,
                '--resize_factor', '1'
            ]
            # 执行推理
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Wav2Lip inference finished successfully.")
            return True, "mp4", output_path
        except Exception as e:
            logger.warning(f"Wav2Lip inference failed: {e}. Falling back to static video.")

    # 优雅降级：使用 ffmpeg 快速组合静态人脸图像与音频
    logger.info("Using ffmpeg fallback to generate 2D Digital Human video...")
    try:
        # 如果 output_path 已经存在，先删除
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
                
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', face_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest', output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        logger.info(f"FFmpeg video generated at: {output_path}")
        return True, "mp4", output_path
    except Exception as e:
        logger.error(f"FFmpeg static video generation failed: {e}. Falling back to copying audio file.")
        try:
            # 如果 FFmpeg 丢失或失败，将音频文件直接复制为输出，后缀为相同后缀
            import shutil
            ext = os.path.splitext(audio_path)[1] or ".mp3"
            fallback_output_path = os.path.splitext(output_path)[0] + ext
            if os.path.exists(fallback_output_path):
                os.remove(fallback_output_path)
            shutil.copy2(audio_path, fallback_output_path)
            logger.info(f"Copied raw audio as fallback video source: {fallback_output_path}")
            return True, ext.replace(".", ""), fallback_output_path
        except Exception as copy_err:
            logger.error(f"Audio copy fallback failed: {copy_err}")
            return False, "failed", ""
