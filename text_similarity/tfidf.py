#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
TF-IDF (Term Frequency-Inverse Document Frequency) 计算
"""

import numpy as np
from collections import defaultdict


class TFIDF(object):
    """
    用于计算文档 TF-IDF 的类
    """
    
    def __init__(self, corpus, word_sep='', smooth_value=0.01, scale=False):
        """
        初始化TFIDF计算器
        :param corpus: 语料库，列表格式，每个元素是一个文档（字符串或词列表）
        :param word_sep: 词分隔符，默认为空字符串
        :param smooth_value: 平滑值，默认为0.01
        :param scale: 是否进行标准化，默认为False
        """
        assert isinstance(corpus, list), 'Not support this type corpus.'
        self.corpus = corpus
        self.vob = defaultdict(int)  # 词汇表，存储词频
        self.word_sep = word_sep
        self.smooth_value = smooth_value
        self.doc_cnt = defaultdict(set)  # 文档计数，存储包含每个词的文档集合
        self.scale = scale
    
    def get_tf_idf(self):
        """
        计算TF-IDF值
        :return: TF-IDF矩阵，形状为 (文档数, 词汇表大小)
        """
        # 获取词表
        for i, line in enumerate(self.corpus):
            if isinstance(line, str):
                line = line.split(self.word_sep)
            for w in line:
                self.vob[f'{i}_{w}'] += 1
                self.doc_cnt[w].add(i)
        
        # 计算 TF-IDF
        output = np.zeros((len(self.corpus), len(self.vob)))
        for i, line in enumerate(self.corpus):
            if isinstance(line, str):
                line = line.split(self.word_sep)
            tmp_size = len(line)
            for j, w in enumerate(self.vob.keys()):
                w_ = w.split('_')[1]
                if w_ in line:
                    # TF * IDF
                    tf = self.vob[w] / tmp_size
                    idf = np.log((self.smooth_value + len(self.corpus)) / 
                                (self.smooth_value + len(self.doc_cnt[w_])) + 1)
                    output[i, j] = tf * idf
        
        # 标准化
        if self.scale:
            output = (output - output.mean(axis=1).reshape(len(self.corpus), -1)) / \
                     (output.std(axis=1).reshape(len(self.corpus), -1) + 1e-8)
        
        return output


if __name__ == '__main__':
    # 每个列表代表一个文档
    corpus = [
        ['this', 'is', 'a', 'simple', 'tfidf', 'code', 'but', 'code', 'might', 'has', 'bugs'],
        ['python', 'is', 'a', 'code', 'language', 'not', 'human', 'language'],
        ['learning', 'python', 'make', 'things', 'simple', 'but', 'not', 'simple', 'enough']
    ]
    result = TFIDF(corpus)
    print(result.get_tf_idf())
