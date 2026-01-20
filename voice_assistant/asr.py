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


def asr(audio_file, auto_detect_language=True):
    """
    将语音数据转换为文本，支持自动识别普通话和英文
    :param audio_file: 音频文件路径
    :param auto_detect_language: 是否自动检测语言（默认True，会尝试中文和英文）
    :return: 识别结果（如果auto_detect_language=True，返回最佳结果）
    """
    # 以下为参数设置
    # 文件格式
    FORMAT = audio_file[-3:]  # 文件后缀 pcm/wav/amr 格式 极速版仅支持pcm
    # 采样率
    RATE = 16000  # 固定值
    # asr 服务地址信息
    ASR_URL = 'http://vop.baidu.com/server_api'
    
    # 语言识别模型PID映射
    # 1537: 普通话（输入法模型）
    # 1737: 英语
    # 80001: 普通话（搜索模型）
    LANGUAGE_PIDS = {
        'zh': 1537,  # 普通话
        'en': 1737   # 英语
    }
    
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
    
    if auto_detect_language:
        # 自动检测语言：尝试中文和英文，选择最佳结果
        results = {}
        for lang, dev_pid in LANGUAGE_PIDS.items():
            try:
                # 设置参数
                params = {'dev_pid': dev_pid,
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
                begin = timer()
                f = urlopen(req)
                result_json = f.read()
                print(f"{lang} Request time cost {timer() - begin}")
                
                # 获取语音识别结果
                result_str = result_json.decode('utf-8')
                result = json.loads(result_str)
                
                if result['err_no'] == 0:
                    # 保存识别结果和置信度
                    results[lang] = {
                        'text': result['result'][0],
                        'confidence': result.get('result', [{}])[0] if isinstance(result.get('result', []), list) else None
                    }
                    print(f"{lang} 识别成功: {results[lang]['text']}")
                else:
                    print(f"{lang} 识别失败: {result.get('err_msg', 'Unknown error')}")
            except Exception as e:
                print(f"{lang} 识别异常: {str(e)}")
                continue
        
        # 选择最佳结果（优先中文，如果中文失败则使用英文）
        if 'zh' in results:
            return results['zh']['text']
        elif 'en' in results:
            return results['en']['text']
        else:
            raise DemoError('自动识别失败：中文和英文识别都未成功')
    else:
        # 默认使用中文识别
        DEV_PID = LANGUAGE_PIDS['zh']
        
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
