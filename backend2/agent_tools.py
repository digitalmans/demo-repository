import os
import time
import requests
import subprocess
import shutil
import logging
import mimetypes
import contextlib
from requests_toolbelt import MultipartEncoder
from dotenv import load_dotenv

# Try to load environment variables from the workspace root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("3DAgent")

class Generate3DModelTool:
    def __init__(self, api_key: str = None):
        # Reload environment variables to load from .env dynamically
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
        self.api_key = api_key or os.environ.get("MOARK_API_KEY") or os.environ.get("GITEE_AI_API_KEY")
        if not self.api_key:
            logger.warning("No MOARK_API_KEY found! Please configure it in your .env file.")
        
        self.base_url = "https://api.moark.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def generate(self, prompt: str = None, image_path: str = None, output_path: str = "temp.glb") -> str:
        """
        Generate 3D model using Moark's Hunyuan3D-2 model.
        Supports both image-to-3d and text-to-3d tasks.
        """
        if not self.api_key:
            raise ValueError("MOARK_API_KEY is missing. Please configure it in .env.")

        # Default payload parameters matching the Hunyuan3D-2 spec
        payload = {
            "model": "Hunyuan3D-2",
            "type": "glb",
            "seed": 1234,
            "num_inference_steps": 5,
            "octree_resolution": 128,
            "guidance_scale": 5
        }

        fields = [
            ("type", payload["type"]),
            ("model", payload["model"]),
            ("seed", str(payload["seed"])),
            ("num_inference_steps", str(payload["num_inference_steps"])),
            ("octree_resolution", str(payload["octree_resolution"])),
            ("guidance_scale", str(payload["guidance_scale"])),
        ]

        if image_path:
            logger.info(f"Task: Image to 3D. Image: '{image_path}'")
            api_url = f"{self.base_url}/async/image-to-3d"
            
            with contextlib.ExitStack() as stack:
                name = os.path.basename(image_path)
                if image_path.startswith(("http://", "https://")):
                    response = requests.get(image_path, timeout=10)
                    response.raise_for_status()
                    fields.append(("image", (name, response.content, response.headers.get("Content-Type", "application/octet-stream"))))
                else:
                    mime_type, _ = mimetypes.guess_type(image_path)
                    fields.append(("image", (name, stack.enter_context(open(image_path, "rb")), mime_type or "application/octet-stream")))
                
                encoder = MultipartEncoder(fields)
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": encoder.content_type
                }
                
                logger.info(f"Submitting image-to-3d task to: {api_url}")
                response = requests.post(api_url, headers=headers, data=encoder)
                response.raise_for_status()
                result = response.json()
        elif prompt:
            logger.info(f"Task: Text to 3D. Prompt: '{prompt}'")
            api_url = f"{self.base_url}/async/text-to-3d"
            
            fields.append(("prompt", prompt))
            encoder = MultipartEncoder(fields)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": encoder.content_type
            }
            
            logger.info(f"Submitting text-to-3d task to: {api_url}")
            response = requests.post(api_url, headers=headers, data=encoder)
            response.raise_for_status()
            result = response.json()
        else:
            raise ValueError("Must provide either prompt or image_path")

        if result.get("error"):
            raise ValueError(f"Task creation failed: {result.get('error')} - {result.get('message')}")
            
        task_id = result.get("task_id")
        if not task_id:
            raise ValueError(f"Task ID not found in the response: {result}")
        logger.info(f"Task created successfully. Task ID: {task_id}")

        # 2. Poll task status
        status_url = f"{self.base_url}/task/{task_id}"
        model_url = None
        attempts = 0
        max_attempts = 180  # Max 30 minutes with 10s intervals
        
        while attempts < max_attempts:
            attempts += 1
            logger.info(f"Checking task status [{attempts}/{max_attempts}]...")
            res = requests.get(status_url, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=10)
            res.raise_for_status()
            task_res = res.json()
            
            if task_res.get("error"):
                raise ValueError(f"Task error: {task_res['error']} - {task_res.get('message')}")
                
            status = task_res.get("status", "unknown")
            logger.info(f"Task status: {status}")
            
            if status == "success":
                if "output" in task_res and "file_url" in task_res["output"]:
                    model_url = task_res["output"]["file_url"]
                    break
                else:
                    raise Exception("Task succeeded but no output file_url was found.")
            elif status in ["failed", "cancelled"]:
                raise Exception(f"Task execution failed or cancelled with state: {status}")
            
            time.sleep(10)
            
        if not model_url:
            raise Exception("Timeout exceeded waiting for 3D model generation.")

        # 3. Download the generated model
        logger.info(f"Downloading generated 3D model from: {model_url}")
        model_res = requests.get(model_url, timeout=30)
        model_res.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(model_res.content)
            
        logger.info(f"Model downloaded and saved to: {output_path}")
        return os.path.abspath(output_path)


class ConvertToFbxTool:
    def __init__(self, blender_path: str = "blender"):
        # 如果 blender 不在系统 PATH 中，需要传入 blender 绝对路径
        self.blender_path = blender_path
        self.script_path = os.path.abspath("convert_to_fbx.py")

    def convert(self, input_model: str, output_fbx: str) -> str:
        """
        使用 Blender headless 模式将模型转为 FBX
        """
        logger.info(f"Task: Format Conversion. {input_model} -> FBX")
        input_abs = os.path.abspath(input_model)
        output_abs = os.path.abspath(output_fbx)

        if not os.path.exists(input_abs):
            raise FileNotFoundError(f"Input model file not found: {input_abs}")

        cmd = [
            self.blender_path,
            "-b",  # headless mode
            "-P", self.script_path,
            "--",  # 分隔符，传递给 python 脚本的参数
            input_abs,
            output_abs
        ]

        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Blender conversion failed:\n{result.stderr}")
            raise Exception("Blender conversion failed.")
        
        if not os.path.exists(output_abs):
            raise FileNotFoundError("Output FBX was not created by Blender.")

        logger.info(f"Conversion successful. Saved to {output_abs}")
        return output_abs


class UnityImportTool:
    def __init__(self, unity_project_path: str):
        self.unity_models_dir = os.path.join(unity_project_path, "Assets", "Models", "AutoGenerated")
        os.makedirs(self.unity_models_dir, exist_ok=True)

    def import_to_unity(self, source_fbx: str) -> str:
        """
        将生成的 FBX 移动到 Unity 的特定目录下，触发 Unity 自动导入
        """
        logger.info(f"Task: Unity Import")
        if not os.path.exists(source_fbx):
            raise FileNotFoundError(f"Source FBX not found: {source_fbx}")

        filename = os.path.basename(source_fbx)
        dest_path = os.path.join(self.unity_models_dir, filename)

        # 移动文件（为了安全也可以用 copy）
        shutil.copy2(source_fbx, dest_path)
        logger.info(f"Model copied to Unity project: {dest_path}")
        logger.info("Switch back to Unity Editor to trigger AssetPostprocessor.")
        
        return dest_path
