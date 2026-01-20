#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
代码4.1 数据预处理
从源数据中提取最佳答案的问答数据
"""

import csv


def read_data():
    """
    读取保险数据
    :return: 返回两个数组，分别存储读取到的保险问题描述和对应答案
    """
    # 源数据文件地址
    csv_dir = './baoxianzhidao_filter.csv'
    
    # 存储读取到的保险问题描述
    insurance_ques = []
    # 存储读取到的保险问题对应答案
    insurance_ans = []
    
    # 读取源数据
    with open(csv_dir, 'r', newline='', encoding='utf-8') as csvfile:
        read = csv.reader(csvfile)
        for row in read:
            # 选取源数据中答案为最优答案的问答数据
            if len(row) == 4 and row[3] == '1':
                # 若 question 字段非空,则将问题 title 字段与 question 字段拼接为问题描述
                # 若 question 字段为空,则将问题 title 字段作为问题描述
                if row[1]:
                    insurance_ques.append(row[0] + row[1])
                else:
                    insurance_ques.append(row[0])
                
                # 选取 replay 字段作为答案描述
                insurance_ans.append(row[2])
    
    return insurance_ques, insurance_ans


def save_data(insurance_ques, insurance_ans):
    """
    存储保险问答数据
    :param insurance_ques: 保险问题列表
    :param insurance_ans: 保险答案列表
    """
    # 遍历存储问答数据为 CSV 格式
    for idx in range(len(insurance_ans)):
        with open('insurance_data.csv', 'a', newline='', encoding='utf-8') as csvfile:
            spamwriter = csv.writer(csvfile)
            spamwriter.writerow([insurance_ques[idx], insurance_ans[idx]])


if __name__ == '__main__':
    insurance_ques, insurance_ans = read_data()
    print(f'读取到 {len(insurance_ques)} 条问答数据')
    
    # 保存处理后的数据
    # 注意：如果文件已存在，会追加数据，建议先删除旧文件
    import os
    if os.path.exists('insurance_data.csv'):
        os.remove('insurance_data.csv')
        print('已删除旧的insurance_data.csv文件')
    
    save_data(insurance_ques, insurance_ans)
    print('数据预处理完成，已保存到insurance_data.csv')
