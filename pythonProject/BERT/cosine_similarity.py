#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
代码4.6 计算向量余弦相似度
"""

import numpy as np


def cosine_similarity(vector1, vector2):
    """
    计算余弦相似度
    :param vector1: 待比较向量1
    :param vector2: 待比较向量2
    :return: 余弦相似度值
    """
    # 转换为numpy数组
    if not isinstance(vector1, np.ndarray):
        vector1 = np.array(vector1)
    if not isinstance(vector2, np.ndarray):
        vector2 = np.array(vector2)
    
    # 计算点积
    dot_product = np.dot(vector1, vector2)
    
    # 计算向量范数
    norm1 = np.linalg.norm(vector1)
    norm2 = np.linalg.norm(vector2)
    
    # 如果任一向量为零向量，返回0
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    
    # 计算余弦相似度
    similarity = dot_product / (norm1 * norm2)
    
    return round(similarity, 2)


def cosine_similarity_batch(query_vector, vectors):
    """
    批量计算余弦相似度
    :param query_vector: 查询向量
    :param vectors: 向量矩阵（每行是一个向量）
    :return: 相似度数组
    """
    if not isinstance(query_vector, np.ndarray):
        query_vector = np.array(query_vector)
    if not isinstance(vectors, np.ndarray):
        vectors = np.array(vectors)
    
    # 计算点积
    dot_products = np.dot(vectors, query_vector)
    
    # 计算范数
    query_norm = np.linalg.norm(query_vector)
    vector_norms = np.linalg.norm(vectors, axis=1)
    
    # 避免除零
    vector_norms = np.where(vector_norms == 0, 1e-10, vector_norms)
    
    # 计算余弦相似度
    similarities = dot_products / (query_norm * vector_norms)
    
    return similarities


if __name__ == '__main__':
    # 测试
    vec1 = np.array([1, 2, 3])
    vec2 = np.array([1, 2, 3])
    sim = cosine_similarity(vec1, vec2)
    print(f"相同向量相似度: {sim}")  # 应该为1.0
    
    vec3 = np.array([1, 0, 0])
    vec4 = np.array([0, 1, 0])
    sim2 = cosine_similarity(vec3, vec4)
    print(f"垂直向量相似度: {sim2}")  # 应该为0.0
