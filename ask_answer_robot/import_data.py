#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
快速数据导入脚本（非交互式）
直接导入所有语料库数据到Neo4j
"""

from data_importer import DataImporter

def main():
    """主函数"""
    print("=" * 60)
    print("问答机器人语料库导入工具")
    print("=" * 60)
    
    importer = DataImporter()
    
    # 不清空现有数据，直接追加导入
    print("\n开始导入语料库数据（不清空现有数据）...")
    importer.import_all_corpus(clear_existing=False)
    
    print("\n导入完成！")

if __name__ == '__main__':
    main()
