#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
最长公共子序列 (Longest Common Subsequence, LCS)
"""


def lcs_length(str1, str2):
    """
    计算两个字符串的最长公共子序列长度
    使用动态规划算法
    :param str1: 字符串1
    :param str2: 字符串2
    :return: 最长公共子序列的长度
    """
    m = len(str1)
    n = len(str2)
    
    # 创建DP表
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # 填充DP表
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]


def lcs_sequence(str1, str2):
    """
    获取两个字符串的最长公共子序列
    :param str1: 字符串1
    :param str2: 字符串2
    :return: 最长公共子序列
    """
    m = len(str1)
    n = len(str2)
    
    # 创建DP表
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # 填充DP表
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    # 回溯获取LCS
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if str1[i - 1] == str2[j - 1]:
            lcs.append(str1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    
    return ''.join(reversed(lcs))


def lcs_similarity(str1, str2):
    """
    基于LCS计算两个字符串的相似度
    相似度 = LCS长度 / max(len(str1), len(str2))
    :param str1: 字符串1
    :param str2: 字符串2
    :return: 相似度 (0-1之间)
    """
    if not str1 or not str2:
        return 0.0
    
    lcs_len = lcs_length(str1, str2)
    max_len = max(len(str1), len(str2))
    
    return lcs_len / max_len if max_len > 0 else 0.0


if __name__ == '__main__':
    # 示例
    str1 = "ABCDGH"
    str2 = "AEDFHR"
    
    lcs_len = lcs_length(str1, str2)
    lcs_seq = lcs_sequence(str1, str2)
    similarity = lcs_similarity(str1, str2)
    
    print(f"字符串1: {str1}")
    print(f"字符串2: {str2}")
    print(f"最长公共子序列长度: {lcs_len}")
    print(f"最长公共子序列: {lcs_seq}")
    print(f"相似度: {similarity:.4f}")
