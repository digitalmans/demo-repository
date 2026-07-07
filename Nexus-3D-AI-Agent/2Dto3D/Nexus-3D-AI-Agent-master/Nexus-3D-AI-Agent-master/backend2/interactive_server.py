import asyncio
import websockets
import json
import logging
import base64
import urllib.parse
import urllib.request
import os
import uuid

# 自动加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass  # python-dotenv 未安装时跳过，手动设置环境变量也可

from openai import AsyncOpenAI
import threading
import http.server
import socketserver
import dashscope

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def start_http_server():
    try:
        with socketserver.TCPServer(("127.0.0.1", 8080), CORSRequestHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"HTTP Server failed to start: {e}")

from agent_tools import Generate3DModelTool
from image_generator import ImageGeneratorTool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("InteractiveServer")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

SYSTEM_PROMPT = """
你是一个运行在 Unity 游戏引擎中的“AI 沙盒创世系统”控制大脑。
你可以与用户聊天，控制数字人动作，或者根据用户需求自动生成 3D 数字人和游戏场景背景。

当前场景的状态（包括各个角色的坐标 `avatars`，以及场景中物理对象的位置 `objects`）将在每次用户发送消息时附加。你需要根据用户输入和当前场景状态，判断意图，并返回严格的 JSON 格式。
你可以返回单个 JSON 对象，或者一个包含多个 JSON 对象的 **JSON 数组 (Array)**，如果你需要同时控制多个角色的行动（并发指令）。

【非常重要的 3D 坐标系说明】
在这个 3D Web 环境中，坐标系遵循以下严格规则（基于用户的屏幕视角）：
- **X 轴 (左右)**：正数（+X）向右，负数（-X）向左。
- **Y 轴 (上下)**：代表高度。0 是地面，正数（+Y）向上（天空）。**除非用户要求“飞上去”、“跳起来”、“向上走”，否则绝对不要改变目标的 Y 坐标！如果用户只是说“走几步”，Y 必须保持不变。**
- **Z 轴 (前后)**：正数（+Z）代表**向前**（即朝着屏幕外、朝着用户的方向）。负数（-Z）代表**向后**（往屏幕里面退）。
当用户说“向前走一步”，意味着 Z 轴增加（例如 `z + 1`），X 和 Y 保持不变！当用户说“向左走”，意味着 X 轴减小。请务必根据当前坐标进行加减！

支持的 action：

1. 生成数字人 (generate_avatar)
当用户要求“生成一个武士”、“在这个场景里放一个机器人”等，使用此 action。
{
    "action": "generate_avatar",
    "prompt": "对这个数字人的详细英文英文描述，用于提示词",
    "reply": "好的，正在为您生成数字人..."
}

2. 生成场景 (generate_scene)
当用户要求“生成一个赛博朋克街道场景”等，使用此 action。
{
    "action": "generate_scene",
    "prompt": "对这个场景的高清全景英文描述，用于提示词",
    "reply": "正在生成场景背景..."
}

3. 移动数字人 (move_to)
当你需要数字人走到场景中的特定位置，**或者去踢开/撞开/推开某个场景物体** 时使用。
利用传入的场景状态 `objects` 找到目标物体的 position [x, y, z]，然后输出 destination。因为引擎有物理碰撞，只要数字人走到物体的位置，自然就会踢到/推到它！不需要写 dynamic_code！
{
    "action": "move_to",
    "target": "Avatar 1",
    "destination": [x, y, z],
    "reply": "我这就走过去踢那个箱子。"
}

4. 聊天与控制数字人动作 (chat)
当用户要求某个具体的数字人做动作或聊天时使用。如果没说几号，默认 target 为 "Avatar 1"。
Trigger 支持: "Idle", "Walk", "Wave", "Talk", "Dance", "Jump", "Sing"
{
    "action": "chat",
    "target": "Avatar 1",
    "trigger": "Wave",
    "reply": "你好！我是1号数字人。"
}

5. 动态代码生成 (dynamic_code)
当用户要求数字人执行复杂的动态行为（非简单移动），如飞行、变大等，使用此 action。
注意：代码每秒执行60次！若要执行一次性动作（如转身），请写：`group.rotation.y = THREE.MathUtils.lerp(group.rotation.y, Math.PI, 0.1);`。切勿使用 `+=` 等累加操作，否则会疯狂转圈！对于复合动作（如向左走再转身），只写一个 dynamic_code 合并逻辑，或者只选择最重要的一个动作返回，严禁返回多个动作对象。
{
    "action": "dynamic_code",
    "target": "Avatar 1",
    "trigger": "Idle",
    "code": "group.position.y = 2 + Math.sin(state.clock.elapsedTime * 2);",
    "reply": "正在飞行！"
}

请务必只返回合法的 JSON（或 JSON 数组），不要有任何其他多余的解释。如果用户让你们各自向两边走，你可以返回 [{"action":"move_to", "target":"Avatar 1", "destination":[-5,0,0], "reply":"我去左边"}, {"action":"move_to", "target":"Avatar 2", "destination":[5,0,0], "reply":"我去右边"}]
"""

connected_clients = set()

try:
    image_gen_tool = ImageGeneratorTool()
    model_gen_tool = Generate3DModelTool()
except Exception as e:
    logger.error(f"工具初始化失败: {e}")

async def process_user_input(user_text):
    logger.info(f"发送给大模型: {user_text}")
    try:
        response = await client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.3
        )
        result_text = response.choices[0].message.content.strip()
        # Clean markdown formatting if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        result_json = json.loads(result_text)
        logger.info(f"大模型解析意图: {result_json}")
        return result_json
    except Exception as e:
        logger.error(f"大模型调用失败: {e}")
        return {"action": "chat", "target": "Avatar 1", "trigger": "Idle", "reply": "抱歉，我的大脑暂时断线了。"}

def run_dashscope_tts(text):
    dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-7ca125ec0a414e7a810b40f199c1071d")
    result = dashscope.SpeechSynthesizer.call(
        model='sambert-zhijia-v1',
        text=text,
        sample_rate=16000,
        format='wav'
    )
    if result.get_audio_data() is not None:
        return base64.b64encode(result.get_audio_data()).decode('utf-8')
    return None

async def generate_audio_base64(text):
    try:
        url = f"http://127.0.0.1:9880/?text={urllib.parse.quote(text)}&text_language=zh"
        loop = asyncio.get_event_loop()
        def fetch_audio():
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.read()
        logger.info(f"正在请求 GPT-SoVITS 语音合成...")
        audio_bytes = await loop.run_in_executor(None, fetch_audio)
        return base64.b64encode(audio_bytes).decode('utf-8')
    except Exception as e:
        logger.warning(f"GPT-SoVITS 语音合成失败: {e}，尝试 DashScope TTS")
        try:
            loop = asyncio.get_event_loop()
            b64_audio = await loop.run_in_executor(None, run_dashscope_tts, text)
            return b64_audio
        except Exception as e2:
            logger.error(f"DashScope TTS 失败: {e2}")
            return None

async def background_generate_scene(prompt: str):
    logger.info(f"后台开始生成场景: {prompt}")
    try:
        loop = asyncio.get_event_loop()
        output_filename = f"scene_{uuid.uuid4().hex[:6]}.jpg"
        abs_path = os.path.abspath(output_filename)
        await loop.run_in_executor(None, image_gen_tool.generate, prompt, abs_path)
        url = f"http://127.0.0.1:8080/{output_filename}"
        msg = json.dumps({"action": "load_scene", "path": url})
        websockets.broadcast(connected_clients, msg)
    except Exception as e:
        logger.error(f"生成场景失败: {e}")

async def background_generate_avatar(prompt: str):
    logger.info(f"后台开始生成数字人: {prompt}")
    try:
        loop = asyncio.get_event_loop()
        img_filename = f"avatar_2d_{uuid.uuid4().hex[:6]}.jpg"
        glb_filename = f"avatar_3d_{uuid.uuid4().hex[:6]}.glb"
        abs_img = os.path.abspath(img_filename)
        abs_glb = os.path.abspath(glb_filename)
        await loop.run_in_executor(None, image_gen_tool.generate, prompt, abs_img)
        await loop.run_in_executor(None, model_gen_tool.generate, None, abs_img, abs_glb)
        url = f"http://127.0.0.1:8080/{glb_filename}"
        msg = json.dumps({"action": "load_avatar", "path": url})
        websockets.broadcast(connected_clients, msg)
    except Exception as e:
        logger.error(f"生成数字人失败: {e}")

async def handle_client(websocket): 
    logger.info(f"新的客户端连接建立")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            logger.info(f"收到客户端消息: {message}")
            user_text = message
            try:
                msg_json = json.loads(message)
                if "mode" in msg_json and msg_json["mode"] == "answer":
                    text_content = msg_json.get("text", "")
                    target_avatar = msg_json.get("target", "Avatar 1")
                    logger.info(f"纯回答模式: {text_content}")
                    
                    response = await client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": "你是一个3D虚拟助手。请针对用户的提问进行简短、口语化、有趣的回答（不超过50个字）。"},
                            {"role": "user", "content": text_content}
                        ],
                        temperature=0.7
                    )
                    reply_text = response.choices[0].message.content.strip()
                    audio_b64 = await generate_audio_base64(reply_text)
                    ans_act = {
                        "action": "chat",
                        "target": target_avatar,
                        "trigger": "Talk",
                        "reply": reply_text,
                        "audio_base64": audio_b64 or None
                    }
                    await websocket.send(json.dumps([ans_act]))
                    continue
                
                if "text" in msg_json:
                    text_content = msg_json["text"]
                    if "sceneState" in msg_json:
                        user_text = f"【当前场景状态】: {json.dumps(msg_json['sceneState'], ensure_ascii=False)}\n【用户指令】: {text_content}"
                    else:
                        user_text = text_content
            except json.JSONDecodeError:
                pass 
            
            llm_response = await process_user_input(user_text)
            
            actions = llm_response if isinstance(llm_response, list) else [llm_response]
            
            for act in actions:
                action = act.get("action", "chat")
                reply_text = act.get("reply", "")
                if reply_text:
                    audio_b64 = await generate_audio_base64(reply_text)
                    if audio_b64:
                        act["audio_base64"] = audio_b64
                
                if action == "generate_scene":
                    asyncio.create_task(background_generate_scene(act.get("prompt", "a beautiful background")))
                elif action == "generate_avatar":
                    asyncio.create_task(background_generate_avatar(act.get("prompt", "a humanoid character")))
            
            response_str = json.dumps(llm_response, ensure_ascii=False)
            websockets.broadcast(connected_clients, response_str)
            logger.info(f"已广播给客户端")

    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"客户端断开连接: {e}")
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
    finally:
        connected_clients.remove(websocket)

async def main():
    logger.info("Starting HTTP server on port 8080 for serving assets...")
    threading.Thread(target=start_http_server, daemon=True).start()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8765))
    
    server = await websockets.serve(handle_client, host, port)
    logger.info(f"✨ WebSocket 服务正在运行于 ws://{host}:{port} ...")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
