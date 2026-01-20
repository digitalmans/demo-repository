#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
快速问答对导入脚本
导入预设的快速问答对到Neo4j数据库
这些问答对用于快速响应常见问题，不会出现在历史记录中
"""

from data_importer import DataImporter

# 预设的快速问答对
QUICK_QA_PAIRS = [
    ("太阳系中体积最大的行星是哪一颗？", "木星"),
    ("人体最大的器官是什么？", "皮肤"),
    ("澳大利亚的首都是悉尼吗？", "不是，是堪培拉"),
    ("蒙娜丽莎的作者是谁？", "达·芬奇"),
    ("水的化学式是什么？", "H2O"),
    ("企鹅主要生活在北极还是南极？", "南极"),
    ("光在真空中的传播速度大约是多少？", "约 30 万公里/秒"),
    ("著名的相对论是谁提出的？", "爱因斯坦"),
    ("一场标准的足球比赛中，每队有几名球员上场？", "11名"),
    ("世界上最高的山峰是哪座？", "珠穆朗玛峰")
]

def main():
    """主函数"""
    print("=" * 60)
    print("快速问答对导入工具")
    print("=" * 60)
    
    importer = DataImporter()
    
    print(f"\n准备导入 {len(QUICK_QA_PAIRS)} 个快速问答对...")
    
    # 导入问答对
    imported_count = importer.import_qa_pairs(QUICK_QA_PAIRS, "quick_qa")
    
    print(f"\n成功导入 {imported_count} 个快速问答对")
    print("\n这些问答对已添加到知识库中，可以立即使用。")
    print("注意：这些问答对不会出现在历史记录中，但可以被检索到。")

if __name__ == '__main__':
    main()
