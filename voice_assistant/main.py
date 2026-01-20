#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
语音助手入口程序
提供语音识别(ASR)和语音生成(TTS)功能
"""

import sys
import os
from asr import asr, DemoError as ASRError
from tts import tts, DemoError as TTSError


def print_menu():
    """打印主菜单"""
    print("\n" + "="*50)
    print("           语音助手系统")
    print("="*50)
    print("1. 语音识别 (ASR) - 将语音转换为文本")
    print("2. 语音生成 (TTS) - 将文本转换为语音")
    print("3. 退出")
    print("="*50)


def asr_function():
    """语音识别功能"""
    print("\n【语音识别功能】")
    print("支持的音频格式: pcm, wav, amr")
    audio_file = input("请输入音频文件路径: ").strip()
    
    if not audio_file:
        print("错误: 未输入文件路径")
        return
    
    if not os.path.exists(audio_file):
        print(f"错误: 文件不存在 - {audio_file}")
        return
    
    try:
        print("\n正在识别中...")
        result = asr(audio_file)
        print(f"\n识别结果: {result}")
    except ASRError as e:
        print(f"识别错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")


def tts_function():
    """语音生成功能"""
    print("\n【语音生成功能】")
    print("提示: 生成的音频文件将保存为 result.mp3 (默认格式)")
    text = input("请输入要转换的文本: ").strip()
    
    if not text:
        print("错误: 未输入文本")
        return
    
    try:
        print("\n正在生成语音...")
        saved_file = tts(text)
        print(f"\n语音文件已生成: {saved_file}")
        if saved_file != "error.txt":
            print(f"您可以在当前目录找到文件: {saved_file}")
    except TTSError as e:
        print(f"生成错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")


def main():
    """主程序入口"""
    print("欢迎使用语音助手系统！")
    
    while True:
        print_menu()
        choice = input("请选择功能 (1-3): ").strip()
        
        if choice == '1':
            asr_function()
        elif choice == '2':
            tts_function()
        elif choice == '3':
            print("\n感谢使用，再见！")
            sys.exit(0)
        else:
            print("\n无效的选择，请重新输入！")
        
        # 询问是否继续
        continue_choice = input("\n是否继续使用? (y/n): ").strip().lower()
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
        sys.exit(1)
