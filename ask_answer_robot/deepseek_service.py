#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
DeepSeek API 接入模块
使用 OpenAI 兼容的 chat/completions 接口为问答机器人提供大模型回答。
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEEPSEEK_PRESETS = {
    "deepseek_only": {
        "label": "DeepSeek问答",
        "temperature": 0.3,
        "max_tokens": 1200,
        "system_prompt": (
            "你是一个智能问答助手。"
            "请直接、客观、准确地回答用户的问题。"
            "回答应清晰、自然，适合网页展示和语音播报。"
        ),
    },
    "deepseek_combined": {
        "label": "DeepSeek结合本地知识库问答",
        "temperature": 0.3,
        "max_tokens": 1200,
        "system_prompt": (
            "你是一个结合本地知识库（作为你的 skills 技能库）的智能问答助手。"
            "请认真阅读和学习本地知识库的检索结果，并优先参考它们来生成回答。"
            "如果本地检索结果相似度较低、内容不足或不相关，请明确说明，然后基于你的通用知识给出解答。"
            "回答应清晰、自然，适合网页展示和语音播报。"
        ),
    }
}

DEFAULT_PRESET = "deepseek_combined"


class DeepSeekAPIError(Exception):
    """DeepSeek API 调用错误"""


class DeepSeekService:
    """DeepSeek & Moark Chat Completions API 客户端"""

    def __init__(self, api_key=None, base_url=None, model=None, timeout=None):
        self.api_key = (api_key or os.environ.get("DEEPSEEK_API_KEY", "")).strip()
        self.base_url = (base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = (model or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")).strip()
        self.timeout = int(timeout or os.environ.get("DEEPSEEK_TIMEOUT", "30"))

    def is_configured(self):
        """是否已经配置 API Key"""
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
        return bool(self.api_key or os.environ.get("MOARK_API_KEY") or os.environ.get("GITEE_AI_API_KEY"))

    def ask(self, question, preset_key=DEFAULT_PRESET, local_result=None):
        """
        调用 LLM 回答问题。
        :param question: 用户问题
        :param preset_key: 模型名称或预设
        :param local_result: 本地知识库检索结果，可为空
        :return: 回答信息字典
        """
        if not self.is_configured():
            raise DeepSeekAPIError("未配置 API Key，无法调用 API")

        # 判断是否是模力方舟（Moark）模型
        is_moark_model = preset_key in ["Qwen3-32B", "gpt-oss-120b", "GLM-4.6", "DeepSeek-V3"]
        
        # 动态加载 Token 保证最新配置生效
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
        
        api_key = self.api_key
        base_url = self.base_url
        model_name = self.model
        
        if is_moark_model:
            api_key = os.environ.get("MOARK_API_KEY") or os.environ.get("GITEE_AI_API_KEY") or api_key
            base_url = "https://api.moark.com/v1"
            model_name = preset_key
            preset_label = f"模力方舟 {preset_key}"
        else:
            preset = DEEPSEEK_PRESETS.get(preset_key) or DEEPSEEK_PRESETS[DEFAULT_PRESET]
            preset_label = preset["label"]

        system_prompt = (
            "你是一个结合本地知识库（作为你的 skills 技能库）的智能问答助手。"
            "请认真阅读和学习本地知识库的检索结果，并优先参考它们来生成回答。"
            "如果本地检索结果相似度较低、内容不足或不相关，请明确说明，然后基于你的通用知识给出解答。"
            "回答应清晰、自然，适合网页展示和语音播报。"
        ) if local_result else (
            "你是一个智能问答助手。"
            "请直接、客观、准确地回答用户的问题。"
            "回答应清晰、自然，适合网页展示和语音播报。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._build_user_prompt(question, local_result)},
        ]
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1200,
            "stream": False,
        }

        # 针对部分千问等模型设置 top_p 和 frequency_penalty，增加 top_k
        if model_name in ["Qwen3-32B", "gpt-oss-120b", "GLM-4.6"]:
            payload["top_p"] = 0.7
            payload["frequency_penalty"] = 1
            payload["extra_body"] = {"top_k": 50}

        extra_headers = {}
        if model_name == "Qwen3-32B":
            extra_headers["X-Failover-Enabled"] = "true"

        response = self._post_chat_completions(payload, api_key=api_key, base_url=base_url, extra_headers=extra_headers)
        choices = response.get("choices") or []
        if not choices:
            raise DeepSeekAPIError("API 未返回回答")

        message = choices[0].get("message") or {}
        answer = (message.get("content") or "").strip()
        if not answer and message.get("reasoning_content"):
            answer = message.get("reasoning_content").strip()
        if not answer:
            raise DeepSeekAPIError("API 返回了空回答")

        return {
            "answer": answer,
            "model": model_name,
            "preset": preset_key,
            "preset_label": preset_label,
        }

    def _post_chat_completions(self, payload, api_key=None, base_url=None, extra_headers=None):
        """发送 chat/completions 请求"""
        api_key = api_key or self.api_key
        base_url = (base_url or self.base_url).rstrip("/")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        if extra_headers:
            headers.update(extra_headers)

        req = Request(
            base_url + "/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            import ssl
            context = ssl._create_unverified_context()
            with urlopen(req, timeout=self.timeout, context=context) as resp:
                body = resp.read().decode("utf-8")
        except HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            raise DeepSeekAPIError(self._extract_error_message(body) or f"API HTTP {err.code}")
        except URLError as err:
            raise DeepSeekAPIError(f"API 网络连接失败: {err.reason}")
        except TimeoutError:
            raise DeepSeekAPIError("API 请求超时")

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise DeepSeekAPIError("API 返回内容不是有效 JSON")

    def _build_user_prompt(self, question, local_result=None):
        """构造带本地检索上下文的用户消息"""
        parts = [f"用户问题：{question}"]

        if local_result:
            similarity = local_result.get("similarity")
            matched_question = local_result.get("question") or "无"
            local_answer = local_result.get("answer") or "无"
            parts.append(
                "本地知识库检索结果：\n"
                f"- 匹配问题：{matched_question}\n"
                f"- 相似度：{similarity if similarity is not None else '未知'}\n"
                f"- 本地答案：{local_answer}"
            )

            alternatives = local_result.get("alternatives") or []
            if alternatives:
                alt_lines = []
                for index, alt in enumerate(alternatives[:3], 1):
                    if len(alt) >= 3:
                        alt_lines.append(f"{index}. 问题：{alt[0]}；答案：{alt[1]}；相似度：{alt[2]}")
                if alt_lines:
                    parts.append("其他候选结果：\n" + "\n".join(alt_lines))
        else:
            parts.append("本地知识库没有可用检索结果。")

        parts.append("请根据以上信息回答用户问题。")
        return "\n\n".join(parts)

    @staticmethod
    def _extract_error_message(body):
        """从错误响应中提取可读错误"""
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return body[:300].strip()

        error = data.get("error")
        if isinstance(error, dict):
            return error.get("message") or error.get("code")
        if isinstance(error, str):
            return error
        return None
