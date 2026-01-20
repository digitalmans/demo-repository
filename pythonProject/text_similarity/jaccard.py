#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Jaccard 距离和相似度计算
"""


def jaccard_similarity(set1, set2):
    """
    计算两个集合的Jaccard相似系数
    J(A,B) = |A ∩ B| / |A ∪ B|
    :param set1: 集合1
    :param set2: 集合2
    :return: Jaccard相似系数
    """
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return float(intersection / union)


def jaccard_distance(set1, set2):
    """
    计算两个集合的Jaccard距离
    Jδ(A,B) = 1 - J(A,B) = (|A ∪ B| - |A ∩ B|) / |A ∪ B|
    :param set1: 集合1
    :param set2: 集合2
    :return: Jaccard距离
    """
    return 1.0 - jaccard_similarity(set1, set2)


def jaccard_similarity_text(text1, text2, use_jieba=False):
    """
    计算两个文本的Jaccard相似系数
    :param text1: 文本1
    :param text2: 文本2
    :param use_jieba: 是否使用jieba分词（用于中文文本）
    :return: Jaccard相似系数
    """
    if use_jieba:
        try:
            import jieba
            # 对句子分词，默认精准模式
            terms_reference = jieba.cut(text1)
            terms_model = jieba.cut(text2)
            # 去重,如果不需要就改为list
            grams_reference = set(terms_reference)
            grams_model = set(terms_model)
        except ImportError:
            print("警告: 未安装jieba，使用空格分词")
            grams_reference = set(text1.split())
            grams_model = set(text2.split())
    else:
        # 使用空格分词
        grams_reference = set(text1.split())
        grams_model = set(text2.split())
    
    # 计算交集
    temp = 0
    for i in grams_reference:
        if i in grams_model:
            temp = temp + 1
    
    # 计算并集
    fenmu = len(grams_model) + len(grams_reference) - temp
    
    # 计算Jaccard相似系数
    if fenmu == 0:
        return 0.0
    
    jaccard_coefficient = float(temp / fenmu)
    return jaccard_coefficient


def jaccard_distance_text(text1, text2, use_jieba=False):
    """
    计算两个文本的Jaccard距离
    :param text1: 文本1
    :param text2: 文本2
    :param use_jieba: 是否使用jieba分词（用于中文文本）
    :return: Jaccard距离
    """
    return 1.0 - jaccard_similarity_text(text1, text2, use_jieba)


if __name__ == '__main__':
    # 示例1: 使用集合
    set1 = {'a', 'b', 'c', 'd'}
    set2 = {'b', 'c', 'd', 'e'}
    print(f"集合相似度: {jaccard_similarity(set1, set2)}")
    print(f"集合距离: {jaccard_distance(set1, set2)}")
    
    # 示例2: 使用文本（中文，需要jieba）
    a = "香农在信息论中提出的信息熵定义为自信息的期望"
    b = "信息熵作为自信息的期望"
    try:
        similarity = jaccard_similarity_text(a, b, use_jieba=True)
        print(f"文本相似度: {similarity}")
        print(f"文本距离: {jaccard_distance_text(a, b, use_jieba=True)}")
    except:
        print("需要安装jieba: pip install jieba")
