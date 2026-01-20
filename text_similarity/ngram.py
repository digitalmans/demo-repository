#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
N-gram 语言模型
统计语言模型，用于计算文本的概率
"""

from collections import defaultdict, Counter


class NGramModel(object):
    """
    N-gram 语言模型
    """
    
    def __init__(self, n=2):
        """
        初始化N-gram模型
        :param n: N值，默认为2（bigram）
        """
        self.n = n
        self.ngrams = defaultdict(Counter)  # 存储n-gram计数
        self.vocab = set()  # 词汇表
    
    def train(self, corpus):
        """
        训练模型
        :param corpus: 训练语料，列表格式，每个元素是一个文档（字符串或词列表）
        """
        for doc in corpus:
            if isinstance(doc, str):
                # 如果是字符串，按空格分词
                tokens = doc.split()
            else:
                tokens = doc
            
            # 添加开始和结束标记
            tokens = ['<s>'] * (self.n - 1) + tokens + ['</s>']
            
            # 统计n-gram
            for i in range(len(tokens) - self.n + 1):
                ngram = tuple(tokens[i:i + self.n])
                context = tuple(ngram[:-1])
                word = ngram[-1]
                self.ngrams[context][word] += 1
                self.vocab.add(word)
    
    def probability(self, word, context):
        """
        计算给定上下文下词的概率
        :param word: 词
        :param context: 上下文（前n-1个词）
        :return: 概率
        """
        context = tuple(context)
        if context not in self.ngrams:
            return 0.0
        
        total = sum(self.ngrams[context].values())
        if total == 0:
            return 0.0
        
        return self.ngrams[context][word] / total
    
    def sentence_probability(self, sentence):
        """
        计算句子的概率
        :param sentence: 句子（字符串或词列表）
        :return: 概率
        """
        if isinstance(sentence, str):
            tokens = sentence.split()
        else:
            tokens = sentence
        
        tokens = ['<s>'] * (self.n - 1) + tokens + ['</s>']
        prob = 1.0
        
        for i in range(self.n - 1, len(tokens)):
            context = tuple(tokens[i - self.n + 1:i])
            word = tokens[i]
            prob *= self.probability(word, context)
        
        return prob


if __name__ == '__main__':
    # 示例：训练bigram模型
    corpus = [
        '自然语言处理是计算机科学领域',
        '人工智能是计算机科学的重要方向',
        '自然语言处理与人工智能密切相关'
    ]
    
    model = NGramModel(n=2)  # bigram模型
    model.train(corpus)
    
    # 计算句子概率
    test_sentence = '自然语言处理'
    prob = model.sentence_probability(test_sentence)
    print(f"句子 '{test_sentence}' 的概率: {prob}")
