#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
文本相似度计算工具包
提供多种文本相似度计算方法
"""

from .edit_distance import edit_distance
from .hamming_distance import hamming_distance
from .tfidf import TFIDF
from .bm25 import BM25
from .ngram_distance import NGram
from .jaccard import jaccard_similarity, jaccard_distance, jaccard_similarity_text, jaccard_distance_text
from .lcs import lcs_length, lcs_sequence, lcs_similarity
from .pointwise import PointWiseModel
from .ngram import NGramModel
from .pairwise import PairwiseModel
from .loss_functions import BinaryCrossEntropyLoss, PairwiseHingeLoss, PairwiseLogLoss, SoftmaxWithLoss

__all__ = [
    'edit_distance', 
    'hamming_distance', 
    'TFIDF', 
    'BM25',
    'NGram',
    'jaccard_similarity',
    'jaccard_distance',
    'jaccard_similarity_text',
    'jaccard_distance_text',
    'lcs_length',
    'lcs_sequence',
    'lcs_similarity',
    'PointWiseModel',
    'NGramModel',
    'PairwiseModel',
    'BinaryCrossEntropyLoss',
    'PairwiseHingeLoss',
    'PairwiseLogLoss',
    'SoftmaxWithLoss'
]
