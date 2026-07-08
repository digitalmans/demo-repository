#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
百度翻译API模块
"""

import hashlib
import random
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

# 百度翻译API配置
APP_ID = 'rxh'
SECRET_KEY = 'S3t4_d5jr6qubn12rnu5ubijg'
TRANSLATE_URL = 'http://api.fanyi.baidu.com/api/trans/vip/translate'


class TranslationError(Exception):
    """翻译错误异常"""
    pass


def translate(text, from_lang='auto', to_lang='zh'):
    """
    翻译文本
    :param text: 要翻译的文本
    :param from_lang: 源语言，'auto'表示自动检测，'zh'表示中文，'en'表示英文
    :param to_lang: 目标语言，'zh'表示中文，'en'表示英文
    :return: 翻译结果
    """
    if not text or not text.strip():
        raise TranslationError('文本内容不能为空')
    
    # 语言代码映射
    lang_map = {
        'zh': 'zh',
        'en': 'en',
        'jp': 'jp',
        'auto': 'auto'
    }
    
    from_lang = lang_map.get(from_lang, 'auto')
    to_lang = lang_map.get(to_lang, 'zh')
    
    if from_lang == to_lang:
        # 如果源语言和目标语言相同，直接返回原文
        return text
    
    salt = str(random.randint(32768, 65536))
    # 计算签名：appid+q+salt+密钥 的MD5值
    sign_str = APP_ID + text + salt + SECRET_KEY
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    params = {
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'appid': APP_ID,
        'salt': salt,
        'sign': sign
    }
    
    try:
        # 发送请求
        data = urlencode(params).encode('utf-8')
        req = Request(TRANSLATE_URL, data)
        response = urlopen(req, timeout=10)
        result = response.read().decode('utf-8')
        result_dict = json.loads(result)
        
        # 检查是否有错误
        if 'error_code' in result_dict:
            error_code = result_dict.get('error_code')
            error_msg = result_dict.get('error_msg', '未知错误')
            raise TranslationError(f'翻译失败: {error_code} - {error_msg}')
        
        # 获取翻译结果
        if 'trans_result' in result_dict:
            trans_result = result_dict['trans_result']
            if isinstance(trans_result, list) and len(trans_result) > 0:
                translated_text = trans_result[0].get('dst', '')
                return translated_text
            else:
                raise TranslationError('翻译结果格式错误')
        else:
            raise TranslationError('翻译API返回格式错误')
    
    except URLError as e:
        raise TranslationError(f'网络错误: {str(e)}')
    except json.JSONDecodeError as e:
        raise TranslationError(f'解析响应失败: {str(e)}')
    except Exception as e:
        raise TranslationError(f'翻译失败: {str(e)}')


def translate_to_chinese(text):
    """
    翻译为中文
    :param text: 要翻译的文本
    :return: 中文翻译结果
    """
    return translate(text, from_lang='auto', to_lang='zh')


def translate_to_english(text):
    """
    翻译为英文
    :param text: 要翻译的文本
    :return: 英文翻译结果
    """
    return translate(text, from_lang='auto', to_lang='en')


def translate_to_japanese(text):
    """
    翻译为日语
    :param text: 要翻译的文本
    :return: 日语翻译结果
    """
    return translate(text, from_lang='auto', to_lang='jp')


if __name__ == '__main__':
    # 测试翻译功能
    test_text = "你好，世界"
    print(f"原文: {test_text}")
    print(f"翻译为英文: {translate_to_english(test_text)}")
    
    test_text_en = "Hello, world"
    print(f"\n原文: {test_text_en}")
    print(f"翻译为中文: {translate_to_chinese(test_text_en)}")
