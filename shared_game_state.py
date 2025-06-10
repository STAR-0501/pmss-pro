# -*- coding: utf-8 -*-
"""
共享游戏状态模块
使用共享内存和变量在主游戏进程和投影显示进程间高效通信
"""

import multiprocessing
import threading
import time
from typing import Dict, List, Tuple, Any


class SharedGameState:
    """共享游戏状态类"""
    
    def __init__(self):
        # 使用简单的共享变量避免pickle问题
        self.screen_size = multiprocessing.Value('i', 1920), multiprocessing.Value('i', 1080)
        self.x = multiprocessing.Value('d', 0.0)
        self.y = multiprocessing.Value('d', 0.0)
        self.ratio = multiprocessing.Value('d', 1.0)
        self.background = multiprocessing.Array('c', b'lightgrey' + b'\0' * 20)
        
        # 球的数据（最多支持100个球）
        self.balls_count = multiprocessing.Value('i', 0)
        self.balls_data = multiprocessing.Array('d', [0.0] * (100 * 5))  # x,y,radius,mass,color_rgb
        
        # 墙的数据（最多支持50个墙）
        self.walls_count = multiprocessing.Value('i', 0)
        self.walls_data = multiprocessing.Array('d', [0.0] * (50 * 9))  # 4个顶点(x,y) + color_rgb
        
        # 控制状态
        self.is_celestial_mode = multiprocessing.Value('b', False)
        self.is_floor_illegal = multiprocessing.Value('b', False)
        
        # 更新标志
        self.data_updated = multiprocessing.Value('b', False)
        self.frame_counter = multiprocessing.Value('i', 0)
        
        # 线程锁
        self.lock = multiprocessing.Lock()
        
    def update_balls(self, balls_data: List[Dict]):
        """更新球的状态数据"""
        with self.lock:
            count = min(len(balls_data), 100)  # 最多100个球
            self.balls_count.value = count
            
            for i, ball in enumerate(balls_data[:count]):
                base_idx = i * 5
                self.balls_data[base_idx] = ball.get('x', 0)
                self.balls_data[base_idx + 1] = ball.get('y', 0)
                self.balls_data[base_idx + 2] = ball.get('radius', 1)
                self.balls_data[base_idx + 3] = ball.get('mass', 1)
                # 将颜色转换为单个数值（RGB打包）
                color = ball.get('color', (255, 255, 255))
                if isinstance(color, (list, tuple)) and len(color) >= 3:
                    color_val = (int(color[0]) << 16) + (int(color[1]) << 8) + int(color[2])
                else:
                    color_val = 16777215  # 白色
                self.balls_data[base_idx + 4] = color_val
            
            self.data_updated.value = True
    
    def update_walls(self, walls_data: List[Dict]):
        """更新墙的状态数据"""
        with self.lock:
            count = min(len(walls_data), 50)  # 最多50个墙
            self.walls_count.value = count
            
            for i, wall in enumerate(walls_data[:count]):
                base_idx = i * 9
                vertices = wall.get('vertices', [])
                # 存储4个顶点的坐标
                for j in range(4):
                    if j < len(vertices):
                        self.walls_data[base_idx + j * 2] = vertices[j].get('x', 0) if hasattr(vertices[j], 'get') else getattr(vertices[j], 'x', 0)
                        self.walls_data[base_idx + j * 2 + 1] = vertices[j].get('y', 0) if hasattr(vertices[j], 'get') else getattr(vertices[j], 'y', 0)
                    else:
                        self.walls_data[base_idx + j * 2] = 0
                        self.walls_data[base_idx + j * 2 + 1] = 0
                
                # 存储颜色
                color = wall.get('color', (128, 128, 128))
                if isinstance(color, (list, tuple)) and len(color) >= 3:
                    color_val = (int(color[0]) << 16) + (int(color[1]) << 8) + int(color[2])
                else:
                    color_val = 8421504  # 灰色
                self.walls_data[base_idx + 8] = color_val
            
            self.data_updated.value = True
    
    def update_view_state(self, x: float, y: float, ratio: float, background: str):
        """更新视图状态"""
        with self.lock:
            self.x.value = x
            self.y.value = y
            self.ratio.value = ratio
            # 更新背景字符串
            bg_bytes = background.encode('utf-8')[:30]  # 限制长度
            for i in range(len(self.background)):
                if i < len(bg_bytes):
                    self.background[i] = bg_bytes[i]
                else:
                    self.background[i] = 0
            self.data_updated.value = True
    
    def is_data_updated(self) -> bool:
        """检查数据是否已更新"""
        with self.lock:
            return self.data_updated.value
    
    def get_balls(self) -> List[Tuple]:
        """获取球的数据"""
        with self.lock:
            balls = []
            for i in range(self.balls_count.value):
                base_idx = i * 5
                x = self.balls_data[base_idx]
                y = self.balls_data[base_idx + 1]
                radius = self.balls_data[base_idx + 2]
                mass = self.balls_data[base_idx + 3]
                color_val = int(self.balls_data[base_idx + 4])
                # 解包颜色
                r = (color_val >> 16) & 0xFF
                g = (color_val >> 8) & 0xFF
                b = color_val & 0xFF
                balls.append((x, y, radius, mass, (r, g, b)))
            return balls
    
    def get_walls(self) -> List[Tuple]:
        """获取墙的数据"""
        with self.lock:
            walls = []
            for i in range(self.walls_count.value):
                base_idx = i * 9
                vertices = []
                for j in range(4):
                    x = self.walls_data[base_idx + j * 2]
                    y = self.walls_data[base_idx + j * 2 + 1]
                    vertices.append((x, y))
                
                color_val = int(self.walls_data[base_idx + 8])
                r = (color_val >> 16) & 0xFF
                g = (color_val >> 8) & 0xFF
                b = color_val & 0xFF
                walls.append((vertices, (r, g, b)))
            return walls
    
    def get_view_state(self) -> Tuple[float, float, float, str]:
        """获取视图状态"""
        with self.lock:
            # 解码背景字符串
            bg_bytes = bytes([b for b in self.background if b != 0])
            background = bg_bytes.decode('utf-8', errors='ignore')
            return (self.x.value, self.y.value, self.ratio.value, background)
    
    def mark_data_read(self):
        """标记数据已读取"""
        with self.lock:
            self.data_updated.value = False
    
    def increment_frame(self):
        """增加帧计数器"""
        with self.lock:
            self.frame_counter.value += 1
    
    def get_frame_count(self) -> int:
        """获取当前帧数"""
        with self.lock:
            return self.frame_counter.value
    
    def set_celestial_mode(self, enabled: bool):
        """设置天体模式"""
        with self.lock:
            self.is_celestial_mode.value = enabled
    
    def is_celestial_mode_enabled(self) -> bool:
        """检查是否启用天体模式"""
        with self.lock:
            return self.is_celestial_mode.value


# 全局共享状态实例
shared_game_state = None


def initialize_shared_state():
    """初始化共享状态"""
    global shared_game_state
    if shared_game_state is None:
        shared_game_state = SharedGameState()
    return shared_game_state


def get_shared_state():
    """获取共享状态实例"""
    global shared_game_state
    if shared_game_state is None:
        shared_game_state = initialize_shared_state()
    return shared_game_state