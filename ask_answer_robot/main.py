#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
问答机器人主入口程序
提供统一的启动接口
"""

import sys
import os


def print_menu():
    """打印主菜单"""
    print("\n" + "=" * 60)
    print("           基于Neo4j的检索式问答机器人")
    print("=" * 60)
    print("1. 导入语料库数据到Neo4j")
    print("2. 启动命令行问答界面")
    print("3. 启动Web问答界面")
    print("4. 退出")
    print("=" * 60)


def import_data():
    """导入语料库数据"""
    print("\n【导入语料库数据】")
    try:
        from data_importer import DataImporter
        
        importer = DataImporter()
        
        clear_choice = input("是否清空现有问答数据？(y/n，默认n): ").strip().lower()
        clear_existing = (clear_choice == 'y' or clear_choice == 'yes')
        
        importer.import_all_corpus(clear_existing=clear_existing)
        
        print("\n导入完成！")
    except Exception as e:
        print(f"导入失败: {e}")


def start_cli():
    """启动命令行界面"""
    print("\n【命令行问答界面】")
    print("提示: 输入 'quit' 或 'exit' 退出\n")
    
    try:
        from qa_service import QAService
        
        service = QAService()
        
        while True:
            question = input("您的问题: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break
            
            result = service.ask(question)
            
            if result:
                print(f"\n【答案】")
                print(f"{result['answer']}")
                print(f"\n[匹配问题: {result['question']}]")
                print(f"[相似度: {result['similarity']:.3f}]")
                
                if result.get('alternatives'):
                    print(f"\n[其他候选答案]")
                    for i, (q, a, s) in enumerate(result['alternatives'][:2], 1):
                        print(f"  {i}. [{s:.3f}] {a[:50]}...")
            else:
                print("\n抱歉，没有找到相关答案。")
            
            print()
    
    except Exception as e:
        print(f"启动失败: {e}")
        print("请确保Neo4j服务已启动，并且已导入语料库数据")


def start_web():
    """启动Web界面"""
    print("\n【Web问答界面】")
    print("正在启动Web服务...")
    
    try:
        from web_app import app, init_service
        
        if not init_service():
            print("无法启动服务，请检查Neo4j连接")
            return
        
        print("\n服务启动中...")
        print("访问地址: http://127.0.0.1:5003")
        print("按 Ctrl+C 停止服务\n")
        
        app.run(host='0.0.0.0', port=5003, debug=False)
    
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        print("请确保Neo4j服务已启动，并且已导入语料库数据")


def main():
    """主程序入口"""
    print("欢迎使用基于Neo4j的检索式问答机器人！")
    
    while True:
        print_menu()
        choice = input("请选择功能 (1-4): ").strip()
        
        if choice == '1':
            import_data()
        elif choice == '2':
            start_cli()
        elif choice == '3':
            start_web()
        elif choice == '4':
            print("\n感谢使用，再见！")
            sys.exit(0)
        else:
            print("\n无效的选择，请重新输入！")
        
        # 询问是否继续
        if choice != '3':  # Web服务会持续运行
            continue_choice = input("\n是否返回主菜单? (y/n): ").strip().lower()
            if continue_choice != 'y' and continue_choice != 'yes':
                print("\n感谢使用，再见！")
                break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
