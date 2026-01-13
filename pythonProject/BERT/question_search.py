#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
代码4.3 在问答库中查找相同问题
使用编辑距离查找相同或相似的问题
"""

import csv
try:
    from Levenshtein import distance as levenshtein_distance
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False
    print("警告: 未安装python-Levenshtein，将使用内置编辑距离算法")
    print("建议安装: pip install python-Levenshtein")


def edit_distance(str1, str2):
    """
    计算编辑距离（如果Levenshtein不可用，使用此函数）
    :param str1: 字符串1
    :param str2: 字符串2
    :return: 编辑距离
    """
    if LEVENSHTEIN_AVAILABLE:
        return levenshtein_distance(str1, str2)
    
    # 使用动态规划计算编辑距离
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,      # 删除
                    dp[i][j - 1] + 1,      # 插入
                    dp[i - 1][j - 1] + 1   # 替换
                )
    
    return dp[m][n]


def similarity_score(str1, str2):
    """
    计算两个字符串的相似度得分（0-1之间，1表示完全相同）
    :param str1: 字符串1
    :param str2: 字符串2
    :return: 相似度得分
    """
    if not str1 or not str2:
        return 0.0
    
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 1.0
    
    distance = edit_distance(str1, str2)
    similarity = 1.0 - (distance / max_len)
    return similarity


def find_similar_question(user_question, threshold=0.8):
    """
    在问答库中查找相同或相似的问题
    :param user_question: 用户输入的问题
    :param threshold: 相似度阈值，默认0.8
    :return: (found, question, answer, similarity) - 是否找到、问题、答案、相似度
    """
    # 读取问答数据
    source_dir = './insurance_data.csv'
    
    insurance_ques = []
    insurance_ans = []
    
    try:
        with open(source_dir, 'r', newline='', encoding='utf-8') as csvfile:
            read = csv.reader(csvfile)
            for row in read:
                if len(row) >= 2:
                    insurance_ques.append(row[0])
                    insurance_ans.append(row[1])
    except FileNotFoundError:
        print(f"错误: 找不到文件 {source_dir}")
        return False, None, None, 0.0
    
    if not insurance_ques:
        return False, None, None, 0.0
    
    # 清除用户问题中的空格
    user_question_clean = "".join(user_question.split())
    
    # 查找最相似的问题
    best_similarity = 0.0
    best_index = -1
    
    for i, question in enumerate(insurance_ques):
        # 清除问题中的空格
        question_clean = "".join(question.split())
        
        # 计算相似度
        sim = similarity_score(user_question_clean, question_clean)
        
        if sim > best_similarity:
            best_similarity = sim
            best_index = i
    
    # 判断是否找到相似问题
    if best_similarity >= threshold and best_index >= 0:
        return True, insurance_ques[best_index], insurance_ans[best_index], best_similarity
    else:
        return False, None, None, best_similarity


if __name__ == '__main__':
    # 测试
    test_question = "最近在安*长青树中看到什么豁免,这个是什么意思?"
    found, question, answer, similarity = find_similar_question(test_question)
    
    if found:
        print(f"找到相似问题 (相似度: {similarity:.4f})")
        print(f"问题: {question}")
        print(f"答案: {answer[:100]}...")
    else:
        print(f"未找到相似问题 (最高相似度: {similarity:.4f})")
