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
    """DeepSeek Chat Completions API 客户端"""

    def __init__(self, api_key=None, base_url=None, model=None, timeout=None):
        self.api_key = (api_key or os.environ.get("DEEPSEEK_API_KEY", "")).strip()
        self.base_url = (base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = (model or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")).strip()
        self.timeout = int(timeout or os.environ.get("DEEPSEEK_TIMEOUT", "30"))

    def is_configured(self):
        """是否已经配置 API Key"""
        return bool(self.api_key)

    def ask(self, question, preset_key=DEFAULT_PRESET, local_result=None):
        """
        调用 DeepSeek 回答问题。
        :param question: 用户问题
        :param preset_key: 回答预设
        :param local_result: 本地知识库检索结果，可为空
        :return: 回答信息字典
        """
        if not self.is_configured():
            raise DeepSeekAPIError("未配置 DEEPSEEK_API_KEY，无法调用 DeepSeek API")

        preset = DEEPSEEK_PRESETS.get(preset_key) or DEEPSEEK_PRESETS[DEFAULT_PRESET]
        messages = [
            {"role": "system", "content": preset["system_prompt"]},
            {"role": "user", "content": self._build_user_prompt(question, local_result)},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": preset["temperature"],
            "max_tokens": preset["max_tokens"],
            "stream": False,
        }

        response = self._post_chat_completions(payload)
        choices = response.get("choices") or []
        if not choices:
            raise DeepSeekAPIError("DeepSeek API 未返回回答")

        message = choices[0].get("message") or {}
        answer = (message.get("content") or "").strip()
        if not answer:
            raise DeepSeekAPIError("DeepSeek API 返回了空回答")

        return {
            "answer": answer,
            "model": self.model,
            "preset": preset_key if preset_key in DEEPSEEK_PRESETS else DEFAULT_PRESET,
            "preset_label": preset["label"],
        }

    def _post_chat_completions(self, payload):
        """发送 chat/completions 请求"""
        req = Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            import ssl
            context = ssl._create_unverified_context()
            with urlopen(req, timeout=self.timeout, context=context) as resp:
                body = resp.read().decode("utf-8")
        except HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            raise DeepSeekAPIError(self._extract_error_message(body) or f"DeepSeek API HTTP {err.code}")
        except URLError as err:
            raise DeepSeekAPIError(f"DeepSeek API 网络连接失败: {err.reason}")
        except TimeoutError:
            raise DeepSeekAPIError("DeepSeek API 请求超时")

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise DeepSeekAPIError("DeepSeek API 返回内容不是有效 JSON")

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
