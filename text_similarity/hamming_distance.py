#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
汉明距离（Hamming Distance）计算
"""


def hamming_distance(str1, str2):
    """
    计算两个等长字符串之间的汉明距离
    :param str1: 字符串1
    :param str2: 字符串2
    :return: 汉明距离
    """
    if len(str1) != len(str2):
        raise ValueError("两个字符串长度必须相等")
    
    distance = 0
    for i in range(len(str1)):
        if str1[i] != str2[i]:
            distance += 1
    
    return distance


if __name__ == '__main__':
    # 示例
    str1 = 'abc'
    str2 = 'abd'
    hd = hamming_distance(str1, str2)
    print(f"'{str1}' 和 '{str2}' 之间的汉明距离: {hd}")
    
    # 更多示例
    print(f"'karolin' 和 'kathrin' 之间的汉明距离: {hamming_distance('karolin', 'kathrin')}")
    print(f"'karolin' 和 'kerstin' 之间的汉明距离: {hamming_distance('karolin', 'kerstin')}")
