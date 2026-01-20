#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
代码4.5 实现查找相似问题
智能客服核心服务模块
根据用户输入问题，系统给予用户相应回答
"""

import numpy as np
import csv
from .edit_distance_search import getSameQuestionByEditDistance, getSimilaryQuestionByIndex
from .cosine_similarity import cosine_similarity
from .text_utils import clean_ans, replace_punctuation


def getBestAnswer(input_ques):
    """
    根据用户输入问题,系统给予用户相应回答
    :param input_ques: 用户输入问题信息
    :return: (sys_reply, QA_que, QA_ans)
        sys_reply: 系统回复
        QA_que: 相似问题
        QA_ans: 推荐答案
    """
    # 根据编辑距离计算问答库中是否存在相同的问题
    is_exist_same_ques, sys_reply, QA_que, QA_ans = getSameQuestionByEditDistance(input_ques)
    
    if is_exist_same_ques:
        # 找到完全相同的问题，直接返回
        return sys_reply, QA_que, QA_ans
    else:
        # 使用BERT语义匹配查找相似问题
        # 保险问答数据中问题的向量表示数据地址
        insurance_data_vector_path = './insurance_ques_vector.npy'
        
        try:
            # 导入问答数据中问题的向量表述数据
            insurance_ques_vector = np.load(insurance_data_vector_path)
        except FileNotFoundError:
            print(f"警告: 找不到向量文件 {insurance_data_vector_path}")
            # 如果找不到向量文件，返回未找到答案
            sys_reply = '啊哦,小助手还没有掌握这方面的知识呢,我会将您的问题记录下来,并尽快找到专业的答案。'
            return sys_reply, '', ''
        
        try:
            # 实例化BERT向量转换工具
            from bert_serving.client import BertClient
            bc = BertClient()
            
            # 将用户输入问题通过BERT转换为向量表示
            input_ques_clean = "".join(input_ques.split())
            input_vec = bc.encode([input_ques_clean])
            
            # 查找问答库中语义最相似的前10个问题
            topk = 10
            
            # 计算输入问题与问答库中全部问题的相似度
            # 使用余弦相似度
            input_vec_norm = input_vec[0] / np.linalg.norm(input_vec[0])
            insurance_ques_vector_norm = insurance_ques_vector / np.linalg.norm(insurance_ques_vector, axis=1, keepdims=True)
            score = np.dot(insurance_ques_vector_norm, input_vec_norm)
            
            # 对相似计算结果排序并返回前10条问题
            topk_idx = np.argsort(score)[::-1][:topk]
            
            # 根据找到的最相似问题的索引获取其相似问题及答案
            similaryQuestion, bestAns = getSimilaryQuestionByIndex(topk_idx[0] + 1)  # 索引从1开始
            
            # 计算找到的语义最相似问题与用户输入问题的余弦相似度
            similar_val = cosine_similarity(input_vec[0], insurance_ques_vector[topk_idx[0]])
            
            # 用户输入问题与问答库中找到的相似问题的阈值设定
            similarity_question_threshold = 0.9
            
            # 若用户输入问题与找到的最相似问题的相似度小于设定的阈值,则表示系统没有找到答案
            # 否则将找到的相似问题及答案返回给用户
            if similar_val < similarity_question_threshold:
                sys_reply = '啊哦,小助手还没有掌握这方面的知识呢,我会将您的问题记录下来,并尽快找到专业的答案。'
                QA_que = ''
                QA_ans = ''
            else:
                sys_reply = '小助手没有这个问题的答案呢,给您推荐以下相似问题及答案以供参考哦~\n'
                QA_que = '相似问题:' + similaryQuestion + '\n'
                QA_ans = '推荐答案:' + bestAns + '\n'
                QA_ans = clean_ans(QA_ans)
            
            return sys_reply, QA_que, QA_ans
            
        except ImportError:
            print("警告: bert-serving-client未安装，无法使用BERT语义匹配")
            sys_reply = '啊哦,小助手还没有掌握这方面的知识呢,我会将您的问题记录下来,并尽快找到专业的答案。'
            return sys_reply, '', ''
        except Exception as e:
            print(f"BERT语义匹配错误: {e}")
            sys_reply = '啊哦,小助手还没有掌握这方面的知识呢,我会将您的问题记录下来,并尽快找到专业的答案。'
            return sys_reply, '', ''


if __name__ == '__main__':
    # 测试
    test_questions = [
        "最近在安*长青树中看到什么豁免,这个是什么意思?",
        "和老婆利用假期去澳*探亲,但是第一次去不大熟悉,有没有相关保险呢?",
        "太阳系有几个行星呢"
    ]
    
    for question in test_questions:
        print(f"\n用户问题: {question}")
        sys_reply, QA_que, QA_ans = getBestAnswer(question)
        print(f"系统回复: {sys_reply}")
        if QA_que:
            print(f"{QA_que}")
        if QA_ans:
            print(f"{QA_ans[:200]}...")
