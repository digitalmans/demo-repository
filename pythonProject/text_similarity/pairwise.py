#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Pair-wise 模型
用于语义文本相似度计算
通过构建偏序关系，使语义相似的句子对得分显著高于不相似的句子对
"""

import numpy as np
from collections import Counter


class PairwiseModel:
    """
    Pair-wise 模型
    训练数据格式: (Sentence1, Sentence2, Sentence3)
    - Sentence2: 与Sentence1语义相似
    - Sentence3: 与Sentence1语义不相似
    """
    
    def __init__(self, representation_method='bow', matching_method='cosine', 
                 embedding_dim=100, vocab_size=10000, margin=1.0):
        """
        初始化Pair-wise模型
        :param representation_method: 表示层方法 ('bow', 'cnn', 'rnn')
        :param matching_method: 匹配层方法 ('cosine', 'mlp')
        :param embedding_dim: 词向量维度
        :param vocab_size: 词汇表大小
        :param margin: Hinge loss的margin参数
        """
        from .pointwise import WordEmbedding, RepresentationLayer, MatchingLayer
        
        self.word_embedding = WordEmbedding(vocab_size, embedding_dim)
        self.representation_layer = RepresentationLayer(representation_method, embedding_dim)
        self.matching_layer = MatchingLayer(matching_method, embedding_dim)
        self.margin = margin
    
    def encode_sentence(self, sentence):
        """
        将句子编码为向量
        :param sentence: 句子（字符串或词列表）
        :return: 句子向量
        """
        if isinstance(sentence, str):
            words = sentence.split()
        else:
            words = sentence
        
        # 获取词向量
        word_vectors = [self.word_embedding.get_word_vector(word) for word in words]
        
        # 通过表示层编码
        sentence_vector = self.representation_layer.encode(word_vectors)
        
        return sentence_vector
    
    def predict(self, sentence1, sentence2):
        """
        预测两个句子的相似度得分
        :param sentence1: 句子1
        :param sentence2: 句子2
        :return: 相似度得分
        """
        vec1 = self.encode_sentence(sentence1)
        vec2 = self.encode_sentence(sentence2)
        
        score = self.matching_layer.match(vec1, vec2)
        return score
    
    def hinge_loss(self, score_pos, score_neg):
        """
        Hinge损失函数
        L = max(0, margin - (S(Q,D+) - S(Q,D-)))
        :param score_pos: 正样本得分 S(Q, D+)
        :param score_neg: 负样本得分 S(Q, D-)
        :return: 损失值
        """
        loss = max(0.0, self.margin - (score_pos - score_neg))
        return loss
    
    def log_loss(self, score_pos, score_neg):
        """
        Log损失函数（简化版）
        L = log(1 + exp(score_neg - score_pos))
        :param score_pos: 正样本得分
        :param score_neg: 负样本得分
        :return: 损失值
        """
        # 使用sigmoid的简化形式
        diff = score_neg - score_pos
        loss = np.log(1 + np.exp(diff))
        return loss
    
    def train_step(self, query, pos_sentence, neg_sentence, loss_type='hinge'):
        """
        执行一步训练
        :param query: 查询句子 Q
        :param pos_sentence: 正样本句子 D+
        :param neg_sentence: 负样本句子 D-
        :param loss_type: 损失函数类型 ('hinge' 或 'log')
        :return: 损失值
        """
        score_pos = self.predict(query, pos_sentence)
        score_neg = self.predict(query, neg_sentence)
        
        if loss_type == 'hinge':
            loss = self.hinge_loss(score_pos, score_neg)
        elif loss_type == 'log':
            loss = self.log_loss(score_pos, score_neg)
        else:
            raise ValueError(f"Unsupported loss type: {loss_type}")
        
        return loss, score_pos, score_neg


if __name__ == '__main__':
    # 创建模型
    model = PairwiseModel(representation_method='bow', matching_method='cosine', margin=1.0)
    
    # 测试数据
    query = "用电视机当笔记本电脑显示器好吗"
    pos_sentence = "电视机可以当笔记本电脑的显示器吗"
    neg_sentence = "笔记本电脑屏幕可以当电视机"
    
    # 计算得分
    score_pos = model.predict(query, pos_sentence)
    score_neg = model.predict(query, neg_sentence)
    
    print(f"查询: {query}")
    print(f"正样本: {pos_sentence}")
    print(f"正样本得分: {score_pos:.4f}")
    print(f"负样本: {neg_sentence}")
    print(f"负样本得分: {score_neg:.4f}")
    print()
    
    # 计算损失
    hinge_loss = model.hinge_loss(score_pos, score_neg)
    log_loss = model.log_loss(score_pos, score_neg)
    
    print(f"Hinge损失: {hinge_loss:.4f}")
    print(f"Log损失: {log_loss:.4f}")
