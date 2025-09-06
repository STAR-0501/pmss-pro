from typing import Self

import pygame

from .vector2 import *


class CollisionLine:
    """碰撞线段类，处理线段相交检测和显示"""

    def __init__(
        self,
        start: Vector2,
        end: Vector2,
        isLine: bool = False,
        collisionFactor: float = 1,
        display: bool = True,
    ) -> None:
        self.start: Vector2 = start
        self.end: Vector2 = end
        self.vector: Vector2 = end - start
        self.isLine: bool = isLine
        self.collisionFactor: float = collisionFactor
        self.display: bool = display

    def isLineIntersect(self, other: Self) -> bool:
        """使用叉积法判断线段相交"""

        def crossProduct(vector1: Vector2, vector2: Vector2) -> float:
            return vector1.x * vector2.y - vector1.y * vector2.x

        # 判断线段AB和线段CD是否相交
        A, B = self.start, self.end
        C, D = other.start, other.end

        # 计算向量AC, AD, BC, BD
        AC = C - A
        AD = D - A
        BC = A - C
        BD = B - C

        # 计算叉积
        AC_cross_AB = crossProduct(AC, self.vector)
        AD_cross_AB = crossProduct(AD, self.vector)
        BC_cross_CD = crossProduct(BC, other.vector)
        BD_cross_CD = crossProduct(BD, other.vector)

        # 判断线段是否相交
        return (AC_cross_AB * AD_cross_AB < 0) and (BC_cross_CD * BD_cross_CD < 0)

    def draw(self, game) -> None:
        """绘制线段到游戏窗口"""
        if self.display:
            pygame.draw.line(
                game.screen,
                "black",
                (
                    game.realToScreen(self.start.x, game.x),
                    game.realToScreen(self.start.y, game.y),
                ),
                (
                    game.realToScreen(self.end.x, game.x),
                    game.realToScreen(self.end.y, game.y),
                ),
            )
