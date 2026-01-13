#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
代码4.2 将问题数据转换为向量表示
通过bert-as-service将问题转换为BERT向量
"""

import numpy as np
import csv


def get_insurance_question():
    """
    获取问答数据中的问题
    :return: 问题列表
    """
    # 保险问答数据存储地址
    source_dir = './insurance_data.csv'
    
    # 存储保险问答数据中的全部问题
    insurance_question = []
    
    # 读取保险问答数据中的问题字段信息
    with open(source_dir, 'r', newline='', encoding='utf-8') as csvfile:
        read = csv.reader(csvfile)
        for data in read:
            insurance_question.append(data[0])
    
    print('获取到', len(insurance_question), '条问题')
    return insurance_question


def bertconvert(insurance_question):
    """
    通过BERT将问题转换为向量表示
    :param insurance_question: 问题列表
    :return: 向量表示
    """
    question_list = []
    
    # 调用 bert-as-service 将字符串转换为向量表示
    try:
        from bert_serving.client import BertClient
        bc = BertClient()
        
        for i in range(len(insurance_question)):
            curr_ques = insurance_question[i]
            # 清除问题字符串中的空格
            curr_ques = "".join(curr_ques.split())
            question_list.append(curr_ques)
        
        # 将问题字符串转换为向量表示
        insurance_ques_vector = bc.encode(question_list)
        
        # 将向量表示的数据保存为npy格式
        np.save("insurance_ques_vector.npy", insurance_ques_vector)
        print(f'已生成向量文件: insurance_ques_vector.npy')
        print(f'向量维度: {insurance_ques_vector.shape}')
        
        return insurance_ques_vector
        
    except ImportError:
        print("警告: 未安装bert-serving-client")
        print("请安装: pip install bert-serving-client")
        print("或者使用模拟模式生成随机向量")
        
        # 模拟模式：生成随机向量（用于测试）
        print("使用模拟模式生成随机向量...")
        num_questions = len(insurance_question)
        insurance_ques_vector = np.random.randn(num_questions, 768).astype(np.float32)
        np.save("insurance_ques_vector.npy", insurance_ques_vector)
        print(f'已生成模拟向量文件: insurance_ques_vector.npy')
        print(f'向量维度: {insurance_ques_vector.shape}')
        
        return insurance_ques_vector
    except Exception as e:
        print(f"BERT转换错误: {e}")
        raise


if __name__ == '__main__':
    print('将保险数据中问答数据中的问题生成向量文件...')
    insurance_question = get_insurance_question()
    bertconvert(insurance_question)
    print('生成向量文件结束!')
