#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
代码4.4 实现去除文本中的标点符号
文本清理工具函数
"""

import re


def replace_punctuation(curr_string):
    """
    清理无效标点符号
    :param curr_string: 当前待处理字符串
    :return: 清理后的字符串
    """
    # 通过正则表达式清理中文标点符号
    punctuation = "！？。，、；：""''（）【】《》〈〉「」『』〔〕…—～·"
    re_punctuation = "[{}]+".format(re.escape(punctuation))
    curr_string = re.sub(re_punctuation, "", curr_string)
    
    # 通过正则表达式清理英文标点符号
    punctuation2 = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    re_punctuation2 = "[{}]+".format(re.escape(punctuation2))
    curr_string = re.sub(re_punctuation2, "", curr_string)
    
    return curr_string


def clean_text(word):
    """
    问题文本清理
    只保留中文字符
    :param word: 输入文本
    :return: 清理后的文本
    """
    res = ""
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':  # 中文字符范围
            res += ch
    return res


def clean_ans(str_ans):
    """
    清理答案信息中的不合法字符
    代码4.8 答案信息清理
    :param str_ans: 答案字符串
    :return: 清理后的答案
    """
    # 清理空格及换行字符
    str_ans = str_ans.replace('\n', '').replace(' ', '')
    return str_ans


if __name__ == '__main__':
    # 测试
    test_str = "你好！这是一个测试，包含标点符号。"
    cleaned = replace_punctuation(test_str)
    print(f"原文本: {test_str}")
    print(f"清理后: {cleaned}")
    
    test_ans = "您好！\n这是一个答案。\n包含换行和空格。"
    cleaned_ans = clean_ans(test_ans)
    print(f"\n原答案: {test_ans}")
    print(f"清理后: {cleaned_ans}")
