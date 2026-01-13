#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
代码4.3 查找相同问题
根据编辑距离计算问答库中是否存在相同的问题
"""

import csv
try:
    from Levenshtein import ratio as levenshtein_ratio
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False
    print("警告: 未安装python-Levenshtein，将使用内置算法")

from .text_utils import replace_punctuation


def edit_distance_ratio(str1, str2):
    """
    计算编辑距离相似度（0-1之间，1表示完全相同）
    :param str1: 字符串1
    :param str2: 字符串2
    :return: 相似度比值
    """
    if LEVENSHTEIN_AVAILABLE:
        return levenshtein_ratio(str1, str2)
    
    # 使用内置算法计算相似度（Levenshtein ratio的简化实现）
    if not str1 or not str2:
        return 0.0
    
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 1.0
    
    # 计算编辑距离
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
    
    distance = dp[m][n]
    similarity = 1.0 - (distance / max_len)
    return similarity


def getSameQuestionByEditDistance(curr_ques):
    """
    根据编辑距离计算问答库中是否存在相同的问题
    :param curr_ques: 当前用户输入的问题
    :return: (is_exist_same_ques, sys_reply, QA_que, QA_ans)
        is_exist_same_ques: 是否存在相同问题
        sys_reply: 系统回复
        QA_que: 找到的问题
        QA_ans: 找到的答案
    """
    same_question_threshold = 0.98
    insurance_data_path = './insurance_data.csv'
    
    max_similarity_val = 0
    max_similarity_index = 0
    
    # 读取问答库
    ques_ans = []
    try:
        with open(insurance_data_path, 'r', newline='', encoding='utf-8') as csvfile:
            read = csv.reader(csvfile)
            for row in read:
                if len(row) >= 2:
                    ques_ans.append(row)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {insurance_data_path}")
        return False, '', '', ''
    
    # 清理用户输入问题中的标点符号
    curr_ques_clean = replace_punctuation(curr_ques)
    
    # 遍历问答库，计算相似度
    curr_idx = 0
    for curr in ques_ans:
        curr_idx += 1
        csv_ques = curr[0]
        
        # 清理问答库中问题中的标点符号
        csv_ques_clean = replace_punctuation(csv_ques)
        
        # 计算编辑距离相似度
        edit_distance_val = edit_distance_ratio(csv_ques_clean, curr_ques_clean)
        
        # 更新最大相似度
        if edit_distance_val > max_similarity_val:
            max_similarity_val = edit_distance_val
            max_similarity_index = curr_idx
    
    # 初始化返回变量
    is_exist_same_ques = False
    sys_reply = ''
    QA_que = ''
    QA_ans = ''
    
    # 判断是否找到相同问题
    if max_similarity_val > same_question_threshold:
        # 根据索引获取问题和答案
        similaryQuestion, bestAns = getSimilaryQuestionByIndex(max_similarity_index)
        from .text_utils import clean_ans
        QA_ans = clean_ans(bestAns)
        QA_que = similaryQuestion
        is_exist_same_ques = True
    
    return is_exist_same_ques, sys_reply, QA_que, QA_ans


def getSimilaryQuestionByIndex(index):
    """
    代码4.7 实现根据问题索引查找问题及相应答案信息
    根据问答库中的问题索引获取其答案信息,返回答案数据中找到的问题及相应答案信息
    :param index: 问题索引（从1开始）
    :return: (question, answer)
    """
    # 问答库地址
    insurance_data_path = './insurance_data.csv'
    
    # 读取问答库
    try:
        with open(insurance_data_path, 'r', encoding='utf-8') as csvfile:
            read = csv.reader(csvfile)
            idx = 0
            
            # 遍历问答库
            for curr_data in read:
                idx += 1
                # 根据问题索引查找其答案信息
                if idx == index:
                    curr_ques = curr_data[0]
                    curr_ans = curr_data[1]
                    return curr_ques, curr_ans
            
            # 如果索引超出范围
            return '', ''
    except FileNotFoundError:
        print(f"错误: 找不到文件 {insurance_data_path}")
        return '', ''
    except Exception as e:
        print(f"读取问答库错误: {e}")
        return '', ''


if __name__ == '__main__':
    # 测试
    test_question = "最近在安*长青树中看到什么豁免,这个是什么意思?"
    is_exist, sys_reply, QA_que, QA_ans = getSameQuestionByEditDistance(test_question)
    
    print(f"问题: {test_question}")
    print(f"找到相同问题: {is_exist}")
    if is_exist:
        print(f"匹配问题: {QA_que}")
        print(f"答案: {QA_ans[:100]}...")
