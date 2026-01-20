#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
检索式问答服务
主服务接口，提供问答功能和语料库管理
"""

import os
import sys
from knowledge_base import KnowledgeBase
from retrieval_engine import RetrievalEngine


class RetrievalService:
    """检索式问答服务"""
    
    def __init__(self, kb_file=None):
        """
        初始化服务
        :param kb_file: 知识库文件路径（可选，用于保存/加载）
        """
        self.kb_file = kb_file
        
        # 初始化知识库
        print("正在初始化知识库...")
        self.kb = KnowledgeBase()
        
        # 初始化检索引擎
        print("正在初始化检索引擎...")
        self.engine = RetrievalEngine(self.kb)
        
        # 如果指定了知识库文件且存在，则加载
        if kb_file and os.path.exists(kb_file):
            try:
                self.kb.load_from_file(kb_file)
                self.engine.update_knowledge_base()
            except Exception as e:
                print(f"警告: 加载知识库文件失败: {e}")
    
    def ask(self, question, top_k=1, threshold=0.05):
        """
        回答问题
        :param question: 用户问题
        :param top_k: 返回前k个答案
        :param threshold: 相似度阈值
        :return: 答案字符串或None
        """
        if not question or not question.strip():
            return "请输入您的问题。"
        
        # 检索答案
        answer = self.engine.answer(question, top_k=top_k, threshold=threshold)
        
        if answer is None:
            return "抱歉，我没有找到相关答案。请尝试换一种问法，或者添加相关的问答对到知识库中。"
        
        # 限制答案长度，最多2000字
        MAX_LENGTH = 2000
        if len(answer) > MAX_LENGTH:
            answer = answer[:MAX_LENGTH] + "\n\n(单次回答最多生成2000字)"
        
        return answer
    
    def search(self, question, top_k=3, threshold=0.05):
        """
        搜索相关问题
        :param question: 用户问题
        :param top_k: 返回前k个结果
        :param threshold: 相似度阈值
        :return: 结果列表
        """
        return self.engine.search(question, top_k=top_k, threshold=threshold)
    
    def add_qa(self, question, answer, category='custom'):
        """
        添加问答对到知识库
        :param question: 问题
        :param answer: 答案
        :param category: 类别
        :return: 是否成功
        """
        if not question or not answer:
            return False, "问题和答案不能为空"
        
        self.kb.add_qa_pair(question, answer, category)
        self.engine.update_knowledge_base()
        
        # 保存到文件（如果指定了）
        if self.kb_file:
            try:
                self.kb.save_to_file(self.kb_file)
            except Exception as e:
                print(f"警告: 保存知识库失败: {e}")
        
        return True, "问答对已添加"
    
    def remove_qa(self, question=None, answer=None):
        """
        从知识库删除问答对
        :param question: 要删除的问题（可选）
        :param answer: 要删除的答案（可选）
        :return: 是否成功
        """
        if not question and not answer:
            return False, "请指定要删除的问题或答案"
        
        success = self.kb.remove_qa_pair(question=question, answer=answer)
        
        if success:
            self.engine.update_knowledge_base()
            
            # 保存到文件（如果指定了）
            if self.kb_file:
                try:
                    self.kb.save_to_file(self.kb_file)
                except Exception as e:
                    print(f"警告: 保存知识库失败: {e}")
            
            return True, "问答对已删除"
        else:
            return False, "未找到匹配的问答对"
    
    def list_qa(self, category=None, limit=10):
        """
        列出问答对
        :param category: 类别过滤（可选）
        :param limit: 返回数量限制
        :return: 问答对列表
        """
        if category:
            qa_pairs = self.kb.get_qa_by_category(category)
        else:
            qa_pairs = self.kb.get_all_qa_pairs()
        
        return qa_pairs[:limit]
    
    def get_statistics(self):
        """获取知识库统计信息"""
        all_qa = self.kb.get_all_qa_pairs()
        categories = {}
        for _, _, cat in all_qa:
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_qa_pairs': len(all_qa),
            'categories': categories,
            'total_movies': len(self.kb.data_loader.movies),
            'total_persons': len(self.kb.data_loader.persons),
            'total_genres': len(self.kb.data_loader.genres)
        }
    
    def save_knowledge_base(self, filepath=None):
        """保存知识库到文件"""
        if filepath is None:
            filepath = self.kb_file
        
        if filepath is None:
            return False, "未指定保存路径"
        
        try:
            self.kb.save_to_file(filepath)
            return True, f"知识库已保存到: {filepath}"
        except Exception as e:
            return False, f"保存失败: {e}"
    
    def rebuild_knowledge_base(self):
        """重新构建知识库（从CSV数据）"""
        print("正在重新构建知识库...")
        self.kb = KnowledgeBase()
        self.engine = RetrievalEngine(self.kb)
        print("知识库重建完成")
        return True, "知识库已重建"


def main():
    """主函数 - 命令行交互界面"""
    print("="*60)
    print("电影问答机器人 - 检索式问答系统")
    print("="*60)
    
    # 初始化服务
    kb_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'knowledge_base.json')
    service = RetrievalService(kb_file=kb_file)
    
    print("\n系统已就绪，您可以开始提问了！")
    print("输入 'help' 查看帮助，输入 'quit' 退出\n")
    
    while True:
        try:
            user_input = input("您: ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                print("再见！")
                break
            
            elif user_input.lower() == 'help':
                print("\n可用命令:")
                print("  help - 显示帮助")
                print("  add - 添加问答对")
                print("  remove - 删除问答对")
                print("  list - 列出问答对")
                print("  stats - 显示统计信息")
                print("  rebuild - 重新构建知识库")
                print("  quit - 退出")
                print("\n直接输入问题即可获得答案\n")
                continue
            
            elif user_input.lower() == 'add':
                print("\n添加问答对:")
                question = input("  问题: ").strip()
                answer = input("  答案: ").strip()
                if question and answer:
                    success, msg = service.add_qa(question, answer)
                    print(f"  {msg}\n")
                else:
                    print("  问题和答案不能为空\n")
                continue
            
            elif user_input.lower() == 'remove':
                print("\n删除问答对:")
                question = input("  问题 (留空跳过): ").strip()
                answer = input("  答案 (留空跳过): ").strip()
                if question or answer:
                    success, msg = service.remove_qa(question=question if question else None, 
                                                     answer=answer if answer else None)
                    print(f"  {msg}\n")
                else:
                    print("  请至少输入问题或答案\n")
                continue
            
            elif user_input.lower() == 'list':
                print("\n问答对列表 (前10条):")
                qa_pairs = service.list_qa(limit=10)
                for i, (q, a, c) in enumerate(qa_pairs, 1):
                    print(f"  [{i}] [{c}]")
                    print(f"      问题: {q}")
                    print(f"      答案: {a[:80]}...")
                print()
                continue
            
            elif user_input.lower() == 'stats':
                stats = service.get_statistics()
                print("\n知识库统计:")
                print(f"  总问答对数: {stats['total_qa_pairs']}")
                print(f"  电影数量: {stats['total_movies']}")
                print(f"  演员数量: {stats['total_persons']}")
                print(f"  类型数量: {stats['total_genres']}")
                print(f"  类别分布:")
                for cat, count in stats['categories'].items():
                    print(f"    {cat}: {count}")
                print()
                continue
            
            elif user_input.lower() == 'rebuild':
                confirm = input("确定要重新构建知识库吗？这将覆盖现有知识库 (y/n): ").strip().lower()
                if confirm == 'y':
                    success, msg = service.rebuild_knowledge_base()
                    print(f"  {msg}\n")
                else:
                    print("  已取消\n")
                continue
            
            # 普通问答
            answer = service.ask(user_input)
            print(f"机器人: {answer}\n")
        
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}\n")


if __name__ == '__main__':
    main()
