from __future__ import annotations

import abc
from random import randint
from typing import TYPE_CHECKING, Any

import pygame

from .vector2 import Vector2, ZERO

if TYPE_CHECKING:
    from ..game.game import Game

gravityFactor: float = 5e4  # 引力常数
electrostaticFactor: float = 1e3  # 静电常数


class Element(abc.ABC):
    """游戏元素基类，定义通用接口"""

    def __init__(self, position: Vector2, color: pygame.Color) -> None:
        self.position: Vector2 = position
        self.color: pygame.Color = color
        self.highLighted: bool = False
        self.type: str = "element"
        self.attrs: list[dict[str, Any]] = []

    @abc.abstractmethod
    def setAttr(self, key: str, value: str) -> None:
        """设置属性"""
        ...

    def isMouseOn(self, game: Game) -> bool:
        """检测鼠标是否在元素上"""
        mouse_pos = pygame.mouse.get_pos()
        rx = float(game.screenToReal(mouse_pos[0], game.x))  # type: ignore[call-overload]
        ry = float(game.screenToReal(mouse_pos[1], game.y))  # type: ignore[call-overload]
        pos = Vector2(rx, ry)
        return self.isPosOn(game, pos)

    def isPosOn(self, game: Game, pos: Vector2) -> bool:
        """检测坐标点是否在元素上（子类应重写此方法）"""
        return False

    def update(self, deltaTime: float) -> 'Element':
        """更新方法（子类应重写此方法）"""
        return self

    def draw(self, game: Game) -> None:
        """绘制方法（子类应重写此方法）"""
        ...

    def updateAttrsList(self) -> None:
        """更新属性列表（子类应重写此方法）"""
        ...
