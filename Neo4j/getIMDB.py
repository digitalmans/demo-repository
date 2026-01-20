#!/usr/bin/env python
# _*_ coding:utf-8 _*_

from datasets import load_dataset
import pandas as pd
import os

def get_imdb_data():
    '''
    加载IMDB数据集并保存为CSV文件
    :return:
    '''
    # 加载IMDB数据集
    # 从 HuggingFace 加载 IMDB 数据集（会自动下载到缓存）
    print("正在加载IMDB数据集...")
    dataset = load_dataset('imdb')
    
    # 处理训练集
    train_data = []
    print("正在处理训练集...")
    for item in dataset['train']:
        train_data.append({
            'text': item['text'],
            'label': item['label']
        })
    
    # 处理测试集
    test_data = []
    print("正在处理测试集...")
    for item in dataset['test']:
        test_data.append({
            'text': item['text'],
            'label': item['label']
        })
    
    # 转换为DataFrame
    train_df = pd.DataFrame(train_data)
    test_df = pd.DataFrame(test_data)
    
    # 保存为CSV文件
    train_csv_path = './imdb_train.csv'
    test_csv_path = './imdb_test.csv'
    
    print(f"正在保存训练集到 {train_csv_path}...")
    train_df.to_csv(train_csv_path, index=False, encoding='utf-8')
    print(f"训练集已保存，共 {len(train_df)} 条数据")
    
    print(f"正在保存测试集到 {test_csv_path}...")
    test_df.to_csv(test_csv_path, index=False, encoding='utf-8')
    print(f"测试集已保存，共 {len(test_df)} 条数据")
    
    # 合并训练集和测试集
    all_data = pd.concat([train_df, test_df], ignore_index=True)
    all_csv_path = './imdb_all.csv'
    print(f"正在保存完整数据集到 {all_csv_path}...")
    all_data.to_csv(all_csv_path, index=False, encoding='utf-8')
    print(f"完整数据集已保存，共 {len(all_data)} 条数据")
    
    return train_df, test_df, all_data


if __name__ == '__main__':
    train_df, test_df, all_df = get_imdb_data()
    print("\n数据集统计信息:")
    print(f"训练集: {len(train_df)} 条")
    print(f"测试集: {len(test_df)} 条")
    print(f"总计: {len(all_df)} 条")
    print("\n标签分布:")
    print(all_df['label'].value_counts())