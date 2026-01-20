#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
基于BERT模型的智能客服系统
"""

from .data_preprocessing import read_data, save_data
from .bert_vector import get_insurance_question, bertconvert
from .question_search import find_similar_question
from .customer_service import CustomerService
from .text_utils import replace_punctuation, clean_text, clean_ans
from .edit_distance_search import getSameQuestionByEditDistance, getSimilaryQuestionByIndex
from .cosine_similarity import cosine_similarity, cosine_similarity_batch
from .intelligent_service import getBestAnswer

__all__ = [
    'read_data',
    'save_data',
    'get_insurance_question',
    'bertconvert',
    'find_similar_question',
    'CustomerService',
    'replace_punctuation',
    'clean_text',
    'clean_ans',
    'getSameQuestionByEditDistance',
    'getSimilaryQuestionByIndex',
    'cosine_similarity',
    'cosine_similarity_batch',
    'getBestAnswer'
]
