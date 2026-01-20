#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import json
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.parse import quote_plus

# 从应用中获取的信息
API_KEY = 'K4v9NQfETSR2hqkRQS0LlUrN'
SECRET_KEY = 'J7WwinltQaEzPWRuZkF9HmK7yEHZ5Iac'

# 有此 scope 表示有tts能力;若没有,请在网页里勾选
SCOPE = 'audio_tts_post'

class DemoError(Exception):
    pass

""" TOKEN start """
TOKEN_URL = 'http://openapi.baidu.com/oauth/2.0/token'

def fetch_token():
    """
    获取 token
    :return:
    """
    print("fetch token begin")
    # 设置 token 参数信息
    params = {'grant_type': 'client_credentials',
              'client_id': API_KEY,
              'client_secret': SECRET_KEY}
    # 发送请求获取 token 信息
    post_data = urlencode(params)
    post_data = post_data.encode('utf-8')
    req = Request(TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read()
    except URLError as err:
        print('token http response http code : ' + str(err.code))
        result_str = err.read()
        result_str = result_str.decode()
    print(result_str)
    result = json.loads(result_str)
    print(result)
    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if SCOPE not in result['scope'].split(' '):
            raise DemoError('scope is not correct')
        print('SUCCESS WITH TOKEN: %s ; EXPIRES IN SECONDS: %s' % (result['access_token'], result['expires_in']))
        return result['access_token']
    else:
        raise DemoError('MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response')
""" TOKEN end """

# 参数设置
# 发音人选择,基础音库:0为度小美,1为度小字,3为度逍遥,4为度丫丫,
# 精品音库:5为度小娇,103为度米朵,106为度博文,110为度小童,111为度小萌,默认为度小类
PER = 0
# 语速,取值范围为0~15,默认为5中语速
SPD = 5
# 音调,取值范围为0~15,默认为5中语调
PIT = 5
# 音量,取值范围为0~9,默认为5中音量
VOL = 5
# 下载的文件格式,3: mp3(default) 4: pcm-16k 5: pcm-8k 6. wav
AUE = 3
FORMATS = {3: "mp3", 4: "pcm", 5: "pcm", 6: "wav"}
FORMAT = FORMATS[AUE]

CUID = "123456PYTHON"

# TTS 服务地址信息
TTS_URL = 'http://tsn.baidu.com/text2audio'

def tts(text, language='zh', speaker=None):
    """
    将文本转换为语音
    :param text: 要转换的文本内容
    :param language: 语言选择，'zh' 表示中文，'en' 表示英文，默认为 'zh'
    :param speaker: 发音人选择，0为度小美，1为度小字，3为度逍遥，4为度丫丫，默认为None（使用PER）
    :return: 保存的文件名
    """
    # 验证语言参数
    if language not in ['zh', 'en']:
        print(f"[TTS] 警告: 无效的语言参数 '{language}'，使用默认值 'zh'")
        language = 'zh'  # 默认使用中文
    
    # 根据语言和传入的speaker参数选择合适的发音人
    # 中文：0为度小美（女声），1为度小字（男声），3为度逍遥（男声），4为度丫丫（女声）
    # 英文：需要使用支持英文的发音人，通常使用0（度小美）或1（度小字）也可以
    if speaker is not None and speaker in [0, 1, 3, 4]:
        # 如果指定了有效的发音人，使用指定的发音人
        per = speaker
        print(f"[TTS] 使用指定的发音人: {per}")
    elif language == 'en':
        # 英文建议使用度小美（0）或度小字（1），这些发音人支持中英文混合
        per = 0  # 使用度小美，支持英文发音
        print(f"[TTS] 使用英文模式，发音人: {per}")
    else:
        # 中文使用默认发音人
        per = PER  # 默认发音人
        print(f"[TTS] 使用中文模式，发音人: {per}, 语言参数: {language}")
    
    # 获取 token
    token = fetch_token()
    
    # 此处 text 需要两次 urlencode
    tex = quote_plus(text)
    # lan ctp 固定参数
    # 注意：百度TTS API的lan参数：'zh'表示中文，'en'表示英文
    params = {'tok': token,
              'tex': tex,
              'per': per,  # 根据语言调整发音人
              'spd': SPD,
              'pit': PIT,
              'vol': VOL,
              'aue': AUE,
              'cuid': CUID,
              'lan': language,  # 使用传入的语言参数：'zh'或'en'
              'ctp': 1}
    # 对参数进行编码
    data = urlencode(params)
    
    print('test on Web Browser' + TTS_URL + '?' + data)
    
    # 获取请求返回结果
    req = Request(TTS_URL, data.encode('utf-8'))
    has_error = False
    try:
        f = urlopen(req)
        result_str = f.read()
        # 获取返回结果的headers 信息
        headers = {name.lower(): value for name, value in f.headers.items()}
        # 判定返回结果是否正确
        has_error = ('content-type' not in headers.keys() or headers['content-type'].find('audio/') < 0)
    except URLError as err:
        print('asr http response http code : ' + str(err.code))
        result_str = err.read()
        has_error = True
    
    # 保存返回结果为音频格式
    save_file = "error.txt" if has_error else 'result.' + FORMAT
    with open(save_file, 'wb') as of:
        of.write(result_str)
    
    if has_error:
        result_str = str(result_str, 'utf-8')
        print("tts api error:" + result_str)
    print("result saved as: " + save_file)
    return save_file


if __name__ == '__main__':
    # 待转换的文本信息
    text = "您好,有什么可以帮助您的吗?"
    tts(text)
