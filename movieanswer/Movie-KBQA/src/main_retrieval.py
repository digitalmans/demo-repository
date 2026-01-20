#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
检索式问答系统主入口
替代原有的main_service.py，使用检索式问答
"""

from retrieval_service import RetrievalService
import os


def main():
    """主函数"""
    print("="*60)
    print("电影问答机器人 - 检索式问答系统")
    print("="*60)
    
    # 初始化服务
    current_dir = os.path.dirname(os.path.abspath(__file__))
    kb_file = os.path.join(os.path.dirname(current_dir), 'data', 'knowledge_base.json')
    
    service = RetrievalService(kb_file=kb_file)
    
    print("\n系统已就绪，您可以开始提问了！")
    print("输入 'quit' 退出\n")
    
    while True:
        try:
            user_input = input("您: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                print("再见！")
                break
            
            # 回答问题
            answer = service.ask(user_input)
            print(f"机器人: {answer}\n")
        
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}\n")


if __name__ == '__main__':
    main()
