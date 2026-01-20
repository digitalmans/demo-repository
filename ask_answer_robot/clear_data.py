#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
清空Neo4j中的问答数据
删除所有QA节点及其关系
"""

from data_importer import DataImporter

def main():
    """主函数"""
    print("=" * 60)
    print("清空Neo4j问答数据工具")
    print("=" * 60)
    print("\n警告: 此操作将删除Neo4j中所有的QA节点数据！")
    print("此操作不可恢复！")
    
    # 确认操作
    confirm = input("\n确定要清空所有问答数据吗？(输入 'yes' 确认): ").strip()
    
    if confirm.lower() != 'yes':
        print("操作已取消")
        return
    
    print("\n正在连接Neo4j数据库...")
    importer = DataImporter()
    
    print("正在清空问答数据...")
    importer.clear_database()
    
    print("\n✓ 数据清空完成！")

if __name__ == '__main__':
    main()
