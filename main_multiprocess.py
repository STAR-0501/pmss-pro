#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物理运动模拟系统 - 多进程版本
分离操作界面和投影显示为两个独立进程
"""

import multiprocessing
import threading
import time

import pygame

from projection_display import run_projection_display
from source.core.ai_thread_loop import AIThreadLoop
from source.game.game import Game


def run_main_game(projection_queue):
    """运行主游戏进程（操作界面）"""
    # 初始化游戏
    game = Game()
    
    # 设置投影队列
    game.setProjectionQueue(projection_queue)
    
    # 创建并启动AI线程
    ai_thread = threading.Thread(target=AIThreadLoop, args=(game,))
    ai_thread.daemon = True
    ai_thread.start()
    
    # 主游戏循环 - 保持主窗口最小化运行
    while True:
        try:
            game.update()
            pygame.display.update()
        except KeyboardInterrupt:
            if game.isChatting:
                game.isChatting = False
            else:
                game.exit()
                break


def main():
    """主函数 - 启动多进程系统"""
    # 创建进程间通信队列
    projection_queue = multiprocessing.Queue(maxsize=10)
    
    # 创建投影显示进程
    projection_process = multiprocessing.Process(
        target=run_projection_display,
        args=(projection_queue,)
    )
    projection_process.daemon = True
    projection_process.start()
    
    print("投影显示进程已启动")
    
    # 等待一下让投影进程完全启动
    time.sleep(1)
    
    try:
        # 运行主游戏进程
        print("启动主游戏进程")
        run_main_game(projection_queue)
    except KeyboardInterrupt:
        print("\n正在关闭程序...")
    finally:
        # 清理进程
        if projection_process.is_alive():
            projection_process.terminate()
            projection_process.join(timeout=5)
        print("程序已关闭")


if __name__ == "__main__":
    # 设置多进程启动方法（Windows需要）
    multiprocessing.set_start_method('spawn', force=True)
    main()