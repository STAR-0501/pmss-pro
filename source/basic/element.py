from typing import Self

import pygame

from random import randint 
from .vector2 import *

gravityFactor = 5e4  # 添加引力常数调节参数


class Element:
    """游戏元素基类，定义通用接口"""

    def __init__(self, position: Vector2, color: pygame.Color) -> None:
        self.position: Vector2 = position
        self.color: pygame.Color = color
        self.highLighted: bool = False
        self.type: str = "element"
        self.attrs: list[dict] = []

    def setAttr(self, key: str, value: str):
        """设置属性"""
        ...

    def isMouseOn(self, game) -> bool:
        """检测鼠标是否在元素上"""
        pos = Vector2(
            game.screenToReal(pygame.mouse.get_pos()[0], game.x),
            game.screenToReal(pygame.mouse.get_pos()[1], game.y),
        )
        return self.isPosOn(game, pos)

    def isPosOn(self, game, pos: Vector2) -> bool:
        """检测坐标点是否在元素上"""
        ...

    def update(self, deltaTime: float) -> Self:
        """更新方法"""
        ...
        return self

    def draw(self, game) -> None:
        """绘制方法"""
        ...

    def updateAttrsList(self) -> None:
        """更新属性列表"""
        ...
