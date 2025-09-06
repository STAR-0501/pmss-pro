#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投影显示模块
独立进程用于显示投影画面
"""

import multiprocessing
import time

import pygame


def run_projection_display(projection_queue):
    """
    运行投影显示进程
    
    Args:
        projection_queue: 从主游戏进程接收画面数据的队列
    """
    # 初始化pygame
    pygame.init()
    
    # 设置投影显示窗口
    try:
        with open("config/screenSize.txt", "r", encoding="utf-8") as f:
            screen_size = [int(i.replace(" ", "")) for i in f.read().split("x")]
    except Exception:
        screen_size = [1920, 1080]  # 默认分辨率
    
    # 创建投影显示窗口
    projection_screen = pygame.display.set_mode(
        size=(screen_size[0], screen_size[1]),
        flags=pygame.FULLSCREEN
    )
    pygame.display.set_caption("PMSS-Pro 投影显示")
    
    # 设置图标
    try:
        icon = pygame.image.load("static/python.png").convert_alpha()
        pygame.display.set_icon(icon)
    except Exception:
        pass
    
    print(f"投影显示窗口已创建: {screen_size[0]} x {screen_size[1]}")
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # 从队列中获取画面数据
        try:
            if not projection_queue.empty():
                surface_data = projection_queue.get_nowait()
                
                # 重建surface
                surface_string = surface_data['data']
                surface_size = surface_data['size']
                
                # 从字符串重建surface
                temp_surface = pygame.image.fromstring(
                    surface_string, surface_size, 'RGB'
                )
                
                # 创建全息投影效果
                projection_screen.fill((211, 211, 211))  # 清空屏幕，使用lightgrey背景
                
                # 计算投影面大小，保持原始画面的长宽比例
                original_width, original_height = surface_size
                aspect_ratio = original_width / original_height
                
                # 计算中心位置
                center_x = screen_size[0] // 2
                center_y = screen_size[1] // 2
                
                # 计算投影面尺寸，确保四个窗口都能完全显示
                margin = 80  # 增加边距确保完全显示
                
                # 计算可用空间：屏幕尺寸减去边距，再除以3（中间正方形+两边各一个投影面）
                available_height = (screen_size[1] - 2.5 * margin) // 3
                available_width = (screen_size[0] - 2.5 * margin) // 3
                
                # 根据长宽比计算投影面尺寸，选择较小的限制
                if aspect_ratio > 1:  # 宽屏
                    proj_height = available_height
                    proj_width = int(proj_height * aspect_ratio)
                    if proj_width > available_width:
                        proj_width = available_width
                        proj_height = int(proj_width / aspect_ratio)
                else:  # 高屏或正方形
                    proj_width = available_width
                    proj_height = int(proj_width / aspect_ratio)
                    if proj_height > available_height:
                        proj_height = available_height
                        proj_width = int(proj_height * aspect_ratio)
                
                # 缩放原始画面到投影面大小，保持长宽比
                scaled_surface = pygame.transform.scale(
                    temp_surface, (proj_width, proj_height)
                )
                
                # 创建全息投影样式：四个方向的投影面围成中间正方形
                # 使用投影面的长边作为中间正方形的边长
                square_side = max(proj_width, proj_height)  # 使用长边作为正方形边长
                half_square = square_side // 2
                
                # 下方投影面（0度，原始方向，屏幕上方指向中心）
                bottom_surface = scaled_surface
                bottom_pos = (center_x - proj_width // 2, center_y + half_square)
                
                # 右方投影面（270度顺时针旋转，外侧为地板）
                right_surface = pygame.transform.rotate(scaled_surface, 90)
                # 旋转后宽高互换，使用原始的proj_height作为旋转后的宽度
                right_pos = (center_x + half_square, center_y - proj_width // 2)
                
                # 上方投影面（180度旋转，屏幕上方指向中心）
                top_surface = pygame.transform.rotate(scaled_surface, 180)
                top_pos = (center_x - proj_width // 2, center_y - half_square - proj_height)
                
                # 左方投影面（90度顺时针旋转，外侧为地板）
                left_surface = pygame.transform.rotate(scaled_surface, -90)
                # 旋转后宽高互换，使用原始的proj_height作为旋转后的宽度
                left_pos = (center_x - half_square - proj_height, center_y - proj_width // 2)
                
                # 绘制四个投影面
                projection_screen.blit(bottom_surface, bottom_pos)
                projection_screen.blit(right_surface, right_pos)
                projection_screen.blit(top_surface, top_pos)
                projection_screen.blit(left_surface, left_pos)
                
                # 绘制中间正方形的边框（可选）
                square_rect = pygame.Rect(center_x - half_square, center_y - half_square, square_side, square_side)
                pygame.draw.rect(projection_screen, (50, 50, 50), square_rect, 2)
                
                pygame.display.flip()
                
        except Exception as e:
            # 如果队列为空或其他错误，继续循环
            print(f"投影显示错误: {e}")
            import traceback
            traceback.print_exc()
        
        # 控制帧率
        clock.tick(60)
    
    pygame.quit()
    print("投影显示进程已退出")


if __name__ == "__main__":
    # 测试代码
    test_queue = multiprocessing.Queue()
    run_projection_display(test_queue)