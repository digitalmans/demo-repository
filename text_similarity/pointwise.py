#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
基于表示的方法 - Point-wise 模型
用于语义文本相似度计算
"""

import numpy as np
from collections import Counter


class WordEmbedding:
    """
    简单的词向量表示（模拟预训练词向量）
    """
    
    def __init__(self, vocab_size=10000, embedding_dim=100):
        """
        初始化词向量
        :param vocab_size: 词汇表大小
        :param embedding_dim: 词向量维度
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        # 随机初始化词向量（实际应用中应使用预训练的词向量）
        np.random.seed(42)
        self.embeddings = np.random.randn(vocab_size, embedding_dim)
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.vocab_count = 0
    
    def get_word_vector(self, word):
        """
        获取词的向量表示（查表方式）
        :param word: 词语
        :return: 词向量
        """
        if word not in self.word_to_idx:
            # 如果词不在词汇表中，分配一个新的索引
            if self.vocab_count < self.vocab_size:
                self.word_to_idx[word] = self.vocab_count
                self.idx_to_word[self.vocab_count] = word
                self.vocab_count += 1
            else:
                # 如果词汇表已满，使用哈希映射到现有索引
                idx = hash(word) % self.vocab_size
                self.word_to_idx[word] = idx
        
        idx = self.word_to_idx[word]
        return self.embeddings[idx]


class RepresentationLayer:
    """
    表示层：将词向量转换为句子向量
    支持BOW、CNN、RNN等方法
    """
    
    def __init__(self, method='bow', embedding_dim=100):
        """
        初始化表示层
        :param method: 方法类型 ('bow', 'cnn', 'rnn')
        :param embedding_dim: 词向量维度
        """
        self.method = method
        self.embedding_dim = embedding_dim
    
    def bow_representation(self, word_vectors):
        """
        Bag of Words 累加方法
        :param word_vectors: 词向量列表
        :return: 句子向量
        """
        if len(word_vectors) == 0:
            return np.zeros(self.embedding_dim)
        return np.mean(word_vectors, axis=0)
    
    def cnn_representation(self, word_vectors):
        """
        简单的CNN表示（简化版）
        :param word_vectors: 词向量列表
        :return: 句子向量
        """
        if len(word_vectors) == 0:
            return np.zeros(self.embedding_dim)
        # 简化版：使用最大池化
        return np.max(word_vectors, axis=0)
    
    def rnn_representation(self, word_vectors):
        """
        简单的RNN表示（简化版）
        :param word_vectors: 词向量列表
        :return: 句子向量
        """
        if len(word_vectors) == 0:
            return np.zeros(self.embedding_dim)
        # 简化版：使用最后一个词向量（实际应使用LSTM/GRU）
        return word_vectors[-1]
    
    def encode(self, word_vectors):
        """
        将词向量序列编码为句子向量
        :param word_vectors: 词向量列表
        :return: 句子向量
        """
        if self.method == 'bow':
            return self.bow_representation(word_vectors)
        elif self.method == 'cnn':
            return self.cnn_representation(word_vectors)
        elif self.method == 'rnn':
            return self.rnn_representation(word_vectors)
        else:
            return self.bow_representation(word_vectors)


class MatchingLayer:
    """
    匹配层：计算两个句子向量的相似度
    支持余弦相似度和MLP方法
    """
    
    def __init__(self, method='cosine', hidden_dim=128):
        """
        初始化匹配层
        :param method: 匹配方法 ('cosine', 'mlp')
        :param hidden_dim: MLP隐藏层维度
        """
        self.method = method
        self.hidden_dim = hidden_dim
        
        if method == 'mlp':
            # 初始化MLP权重（简化版）
            np.random.seed(42)
            self.W1 = np.random.randn(hidden_dim, hidden_dim * 2) * 0.01
            self.b1 = np.zeros(hidden_dim)
            self.W2 = np.random.randn(1, hidden_dim) * 0.01
            self.b2 = np.zeros(1)
    
    def cosine_similarity(self, vec1, vec2):
        """
        计算余弦相似度
        :param vec1: 向量1
        :param vec2: 向量2
        :return: 相似度得分 [0, 1]
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine = dot_product / (norm1 * norm2)
        # 将[-1, 1]映射到[0, 1]
        return (cosine + 1) / 2
    
    def mlp_similarity(self, vec1, vec2):
        """
        使用MLP计算相似度
        :param vec1: 向量1
        :param vec2: 向量2
        :return: 相似度得分 [0, 1]
        """
        # 拼接两个向量
        concat = np.concatenate([vec1, vec2])
        
        # 第一层
        h1 = np.tanh(np.dot(self.W1, concat) + self.b1)
        
        # 第二层
        score = np.dot(self.W2, h1) + self.b2
        
        # 使用sigmoid将得分映射到[0, 1]
        return 1 / (1 + np.exp(-score[0]))
    
    def match(self, vec1, vec2):
        """
        计算两个句子向量的匹配得分
        :param vec1: 句子向量1
        :param vec2: 句子向量2
        :return: 匹配得分 [0, 1]
        """
        if self.method == 'cosine':
            return self.cosine_similarity(vec1, vec2)
        elif self.method == 'mlp':
            return self.mlp_similarity(vec1, vec2)
        else:
            return self.cosine_similarity(vec1, vec2)


class PointWiseModel:
    """
    Point-wise 模型
    将文本相似度计算转换为二分类任务
    """
    
    def __init__(self, representation_method='bow', matching_method='cosine', 
                 embedding_dim=100, vocab_size=10000):
        """
        初始化Point-wise模型
        :param representation_method: 表示层方法 ('bow', 'cnn', 'rnn')
        :param matching_method: 匹配层方法 ('cosine', 'mlp')
        :param embedding_dim: 词向量维度
        :param vocab_size: 词汇表大小
        """
        self.word_embedding = WordEmbedding(vocab_size, embedding_dim)
        self.representation_layer = RepresentationLayer(representation_method, embedding_dim)
        self.matching_layer = MatchingLayer(matching_method, embedding_dim)
    
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
        预测两个句子的相似度
        :param sentence1: 句子1
        :param sentence2: 句子2
        :return: 相似度得分 [0, 1]
        """
        vec1 = self.encode_sentence(sentence1)
        vec2 = self.encode_sentence(sentence2)
        
        score = self.matching_layer.match(vec1, vec2)
        return score
    
    def binary_cross_entropy_loss(self, y_true, y_pred):
        """
        二分类交叉熵损失函数
        L = -y*log(y') - (1-y)*log(1-y')
        :param y_true: 真实标签 (0 或 1)
        :param y_pred: 预测概率 [0, 1]
        :return: 损失值
        """
        epsilon = 1e-15  # 防止log(0)
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        loss = -y_true * np.log(y_pred) - (1 - y_true) * np.log(1 - y_pred)
        return loss


if __name__ == '__main__':
    # 创建模型
    model = PointWiseModel(representation_method='bow', matching_method='cosine')
    
    # 测试句子对
    sentence1 = "宝马启动空调就开了"
    sentence2 = "宝马启动空调"
    sentence3 = "宝马一系启动"
    
    # 预测相似度
    score1 = model.predict(sentence1, sentence2)
    score2 = model.predict(sentence1, sentence3)
    
    print(f"句子1: {sentence1}")
    print(f"句子2: {sentence2}")
    print(f"相似度得分: {score1:.4f}")
    print()
    print(f"句子1: {sentence1}")
    print(f"句子3: {sentence3}")
    print(f"相似度得分: {score2:.4f}")
    print()
    
    # 测试损失函数
    y_true = 1  # 相似
    y_pred = score1
    loss = model.binary_cross_entropy_loss(y_true, y_pred)
    print(f"二分类交叉熵损失: {loss:.4f}")
