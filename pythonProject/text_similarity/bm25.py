#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
BM25 算法实现
用于计算查询与文档之间的相似度
"""

import numpy as np
from collections import Counter


class BM25(object):
    """
    BM25 算法类
    """
    
    def __init__(self, docs):
        """
        初始化BM25
        :param docs: 传入的docs要求是已经分好词的list，每个元素是一个文档的词列表
        """
        self.docs = docs  # 传入的docs要求是已经分好词的list
        self.doc_num = len(docs)  # 文档数
        self.vocab = set([word for doc in self.docs for word in doc])  # 文档中所包含的所有词语
        self.avgdl = sum([len(doc) + 0.0 for doc in docs]) / self.doc_num  # 所有文档的平均长度
        self.k1 = 1.0
        self.b = 0.75
    
    def idf(self, word):
        """
        计算词的IDF值
        :param word: 词语
        :return: IDF值
        """
        if word not in self.vocab:
            word_idf = 0
        else:
            qn = {}
            for doc in self.docs:
                if word in doc:
                    qn[word] = qn.get(word, 0) + 1
            word_idf = np.log((self.doc_num - qn[word] + 0.5) / (qn[word] + 0.5))
        return word_idf
    
    def score(self, word):
        """
        计算词与所有文档的相似度分数
        :param word: 词语
        :return: 分数列表
        """
        score_list = []
        for doc in self.docs:
            word_count = Counter(doc)
            if word in word_count.keys():
                f = (word_count[word] + 0.0) / len(doc)
            else:
                f = 0.0
            r_score = (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * len(doc) / self.avgdl))
            score_list.append(self.idf(word) * r_score)
        return score_list
    
    def score_all(self, sequence):
        """
        计算查询序列与所有文档的相似度
        :param sequence: 查询词序列
        :return: 相似度分数
        """
        sum_score = []
        for word in sequence:
            sum_score.append(self.score(word))
        sim = np.sum(sum_score, axis=0)
        return sim


if __name__ == '__main__':
    # 测试文本
    text = '''自然语言处理是计算机科学领域与人工智能领域中的一个重要方向。它研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。
自然语言处理是一门融语言学、计算机科学、数学于一体的科学。因此,这一领域的研究将涉及自然语言日常使用的语言,所以它与语言学的研究有着密切的联系,但又有重要的区别。
自然语言处理并不是一般的研究自然语言,而在于研制能有效地实现自然语言通信的计算机系统,特别是软件系统。因而它是计算机科学的一部分。'''
    
    # 获取停用词（这里使用空列表，实际使用时需要加载停用词表）
    stopwords = []  # 实际使用时: open('./stopwords/哈工大停用词表.txt').read().split('\n')
    
    # 分词处理（这里简化处理，实际需要使用jieba）
    doc_list = [doc for doc in text.split('\n') if doc != '']
    docs = []
    for sentence in doc_list:
        # 简化处理：按空格分词，实际应使用 jieba.lcut(sentence)
        sentence_words = sentence.split()
        tokens = []
        for word in sentence_words:
            if word in stopwords:
                continue
            else:
                tokens.append(word)
        docs.append(tokens)
    
    # 创建BM25对象
    bm = BM25(docs)
    
    # 计算相似度
    score = bm.score_all(['自然语言', '计算机科学', '领域', '人工智能', '领域'])
    print(score)
