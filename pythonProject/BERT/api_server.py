#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
代码4.9 封装API及项目部署代码
使用aiohttp部署智能客服API服务
"""

import asyncio
import time
from aiohttp import web
from .intelligent_service import getBestAnswer
from .text_utils import clean_text


async def handle(request):
    """
    处理GET请求
    :param request: HTTP请求对象
    :return: JSON响应
    """
    # 获取查询参数
    varDict = request.query
    question = varDict.get('question', '')
    
    # 清理问题文本
    question = clean_text(question)
    
    # 比较余弦相似度查找相似问题
    sys_reply, QA_que, QA_ans = getBestAnswer(question)
    
    # 构造返回JSON
    reply_json = {
        '系统回复': sys_reply,
        '相似问题': QA_que,
        '推荐答案': QA_ans
    }
    
    # 打印当前时间
    print('Current time is:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    print(f'Question: {question}')
    print(f'Reply: {sys_reply[:50]}...')
    
    return web.json_response(reply_json)


async def init_app():
    """
    初始化应用
    :return: web应用实例
    """
    app = web.Application()
    app.router.add_get('/', handle)
    return app


if __name__ == '__main__':
    print("="*50)
    print("智能客服API服务启动中...")
    print("="*50)
    print("访问地址: http://127.0.0.1:9010")
    print("使用方式: http://127.0.0.1:9010/?question=您的问题")
    print("按 Ctrl+C 停止服务器")
    print("="*50)
    
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, port=9010)
