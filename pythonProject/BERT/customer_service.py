#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
智能客服系统主程序
基于文本相似度的智能客服实现
"""

import numpy as np
from .question_search import find_similar_question
from .bert_vector import get_insurance_question, bertconvert


class CustomerService:
    """
    智能客服系统
    支持三种情况：
    1. 找到完全相同或高度相似的问题，直接返回答案
    2. 找到语义相似的问题，返回最相似问题的答案
    3. 无法处理的问题，返回提示信息
    """
    
    def __init__(self, edit_distance_threshold=0.8, bert_threshold=0.7):
        """
        初始化智能客服系统
        :param edit_distance_threshold: 编辑距离相似度阈值
        :param bert_threshold: BERT语义相似度阈值
        """
        self.edit_distance_threshold = edit_distance_threshold
        self.bert_threshold = bert_threshold
        self.questions = []
        self.answers = []
        self.question_vectors = None
        self._load_data()
        self._load_vectors()
    
    def _load_data(self):
        """加载问答数据"""
        import csv
        try:
            with open('./insurance_data.csv', 'r', newline='', encoding='utf-8') as csvfile:
                read = csv.reader(csvfile)
                for row in read:
                    if len(row) >= 2:
                        self.questions.append(row[0])
                        self.answers.append(row[1])
            print(f'已加载 {len(self.questions)} 条问答数据')
        except FileNotFoundError:
            print('警告: 找不到insurance_data.csv文件，请先运行数据预处理')
    
    def _load_vectors(self):
        """加载问题向量"""
        try:
            self.question_vectors = np.load('insurance_ques_vector.npy')
            print(f'已加载问题向量，维度: {self.question_vectors.shape}')
        except FileNotFoundError:
            print('警告: 找不到insurance_ques_vector.npy文件，将使用编辑距离模式')
            self.question_vectors = None
    
    def _bert_similarity(self, user_question):
        """
        使用BERT计算语义相似度
        :param user_question: 用户问题
        :return: (found, index, similarity, answer)
        """
        if self.question_vectors is None:
            return False, -1, 0.0, None
        
        try:
            from bert_serving.client import BertClient
            bc = BertClient()
            
            # 清除问题中的空格
            user_question_clean = "".join(user_question.split())
            
            # 转换为向量
            user_vector = bc.encode([user_question_clean])[0]
            
            # 计算余弦相似度
            similarities = np.dot(self.question_vectors, user_vector) / (
                np.linalg.norm(self.question_vectors, axis=1) * np.linalg.norm(user_vector)
            )
            
            # 找到最相似的问题
            best_index = np.argmax(similarities)
            best_similarity = float(similarities[best_index])
            
            if best_similarity >= self.bert_threshold:
                return True, best_index, best_similarity, self.answers[best_index]
            else:
                return False, best_index, best_similarity, None
                
        except ImportError:
            print("警告: bert-serving-client未安装，无法使用BERT语义匹配")
            return False, -1, 0.0, None
        except Exception as e:
            print(f"BERT相似度计算错误: {e}")
            return False, -1, 0.0, None
    
    def answer(self, user_question):
        """
        回答用户问题
        :param user_question: 用户输入的问题
        :return: (answer, method, similarity)
            answer: 答案文本
            method: 匹配方法 ('exact', 'semantic', 'not_found')
            similarity: 相似度得分
        """
        if not user_question or not user_question.strip():
            return "请输入您的问题", 'not_found', 0.0
        
        if not self.questions:
            return "问答库为空，请先加载数据", 'not_found', 0.0
        
        # 情况1: 使用编辑距离查找相同或高度相似的问题
        found, question, answer, similarity = find_similar_question(
            user_question, 
            threshold=self.edit_distance_threshold
        )
        
        if found:
            return answer, 'exact', similarity
        
        # 情况2: 使用BERT查找语义相似的问题
        bert_found, index, bert_similarity, bert_answer = self._bert_similarity(user_question)
        
        if bert_found:
            return bert_answer, 'semantic', bert_similarity
        
        # 情况3: 无法找到相似问题
        return "抱歉，我无法理解您的问题，请尝试换一种方式提问", 'not_found', max(similarity, bert_similarity)
    
    def batch_answer(self, questions):
        """
        批量回答问题
        :param questions: 问题列表
        :return: 答案列表
        """
        results = []
        for question in questions:
            answer, method, similarity = self.answer(question)
            results.append({
                'question': question,
                'answer': answer,
                'method': method,
                'similarity': similarity
            })
        return results


if __name__ == '__main__':
    # 测试智能客服系统
    print("="*50)
    print("智能客服系统测试")
    print("="*50)
    
    cs = CustomerService()
    
    # 测试问题
    test_questions = [
        "最近在安*长青树中看到什么豁免,这个是什么意思?",
        "和老婆利用假期去澳*探亲,但是第一次去不大熟悉,有没有相关保险呢?",
        "HUTS 中有没有适合帆船比赛的保险",
        "这是一个不存在的问题"
    ]
    
    for question in test_questions:
        print(f"\n用户问题: {question}")
        answer, method, similarity = cs.answer(question)
        print(f"匹配方法: {method}")
        print(f"相似度: {similarity:.4f}")
        print(f"系统回答: {answer[:100]}...")
