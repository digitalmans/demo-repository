#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import json
import base64
import time
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode

timer = time.perf_counter

# 从应用中获取的信息
API_KEY = 'K4v9NQfETSR2hqkRQS0LlUrN'
SECRET_KEY = 'J7WwinltQaEzPWRuZkF9HmK7yEHZ5Iac'

# 有此 scope 表示有 asr 能力,没有请在网页里勾选,版本过低的应用可能没有
SCOPE = 'audio_voice_assistant_get'

class DemoError(Exception):
    pass

""" TOKEN start """
TOKEN_URL = 'http://openapi.baidu.com/oauth/2.0/token'

def fetch_token():
    """
    获取 token
    :return:
    """
    # 设置获取 token 的参数
    params = {'grant_type': 'client_credentials',
              'client_id': API_KEY,
              'client_secret': SECRET_KEY}
    # 通过 post 方式传递参数
    post_data = urlencode(params)
    post_data = post_data.encode('utf-8')
    req = Request(TOKEN_URL, post_data)
    try:
        f = urlopen(req)
        result_str = f.read()
    except URLError as err:
        print('token http response http code : ' + str(err.code))
        result_str = err.read()
        result_str = result_str.decode()
    # 获取token 结果
    result = json.loads(result_str)
    # 校验 token 结果是否正确
    if ('access_token' in result.keys() and 'scope' in result.keys()):
        print(SCOPE)
        if SCOPE and (SCOPE not in result['scope'].split(' ')):  # SCOPE = False 忽略
            raise DemoError('scope is not correct')
        print('SUCCESS WITH TOKEN: %s EXPIRES IN SECONDS: %s' % (result['access_token'], result['expires_in']))
        return result['access_token']
    else:
        raise DemoError('MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response')
""" TOKEN end """


def asr(audio_file):
    """
    将语音数据转换为文本
    :param audio_file: 音频文件路径
    :return: 识别结果
    """
    # 以下为参数设置
    # 文件格式
    FORMAT = audio_file[-3:]  # 文件后缀 pcm/wav/amr 格式 极速版仅支持pcm
    # 采样率
    RATE = 16000  # 固定值
    # 1537 表示识别普通话,使用输入法模型。根据文档填写PID,选择语言及识别模型
    DEV_PID = 1537
    # asr 服务地址信息
    ASR_URL = 'http://vop.baidu.com/server_api'
    
    # 获取 token
    token = fetch_token()
    
    # 获取要识别的音频文件
    speech_data = []
    with open(audio_file, 'rb') as speech_file:
        speech_data = speech_file.read()
    # 若文件内容为空,则抛出异常
    length = len(speech_data)
    if length == 0:
        raise DemoError('file %s length read 0 bytes' % audio_file)
    
    # 使用 base64 加密编码
    speech = base64.b64encode(speech_data)
    speech = str(speech, 'utf-8')
    
    # 设置参数
    params = {'dev_pid': DEV_PID,
              'format': FORMAT,
              'rate': RATE,
              'token': token,
              'cuid': '123456PYTHON',
              'channel': 1,
              'speech': speech,
              'len': length}
    
    # 设置请求格式
    post_data = json.dumps(params, sort_keys=False)
    req = Request(ASR_URL, post_data.encode('utf-8'))
    req.add_header('Content-Type', 'application/json')
    
    # 发送请求并获取结果
    try:
        begin = timer()
        f = urlopen(req)
        result_json = f.read()
        # 计算服务响应时间
        print("Request time cost %f" % (timer() - begin))
    except URLError as err:
        print('asr http response http code : ' + str(err.code))
        result_json = err.read()
    
    # 获取语音识别结果
    result_str = result_json.decode('utf-8')
    result = json.loads(result_str)
    
    if result['err_no'] == 0:
        return result['result'][0]
    else:
        raise DemoError('ASR error: %s' % result.get('err_msg', 'Unknown error'))


if __name__ == '__main__':
    print('语音识别模块已加载')
    print('请设置 API_KEY 和 SECRET_KEY，然后调用 asr(audio_file) 函数进行语音识别')
    print('\n示例用法:')
    print('  audio_file = "your_audio_file.pcm"')
    print('  result = asr(audio_file)')
    print('  print("识别结果:", result)')
