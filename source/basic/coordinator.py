import math
from typing import Self

import pygame

from .vector2 import *


class Coordinator:
    """坐标系辅助类，处理坐标转换和角度显示"""

    def __init__(self, x: float, y: float, width: float, game) -> None:
        self.position: Vector2 = Vector2(x, y)
        self.width: float = width
        self.degree: float = 0
        self.minDegree: float = 0
        self.minDirection: Vector2 = ZERO
        self.direction: list[Vector2] = []
        self.update(game)

    def draw(self, game, option, text: str = "") -> None:
        """绘制坐标系指示器和角度信息"""

        for direction in self.direction:
            pygame.draw.line(
                game.screen,
                "black",
                (
                    game.realToScreen(self.position.x, game.x),
                    game.realToScreen(self.position.y, game.y),
                ),
                (
                    game.realToScreen(self.position.x + direction.x, game.x),
                    game.realToScreen(self.position.y + direction.y, game.y),
                ),
            )

        self.showDegree(
            game,
            Vector2(
                game.screenToReal(pygame.mouse.get_pos()[0], game.x),
                game.screenToReal(pygame.mouse.get_pos()[1], game.y),
            ),
            option,
            text,
        )

    def update(self, game) -> Self:
        """更新坐标系方向向量"""

        self.direction = [
            Vector2(game.screenToReal(self.width), game.screenToReal(0)),
            Vector2(game.screenToReal(0), game.screenToReal(-self.width)),
            Vector2(game.screenToReal(-self.width), game.screenToReal(0)),
            Vector2(game.screenToReal(0), game.screenToReal(self.width)),
        ]

        return self

    def isMouseOn(self) -> bool:
        """检测鼠标是否在坐标系上"""
        return self.minDegree == 0

    def showDegree(self, game, pos: Vector2, option, text: str) -> None:
        """显示当前鼠标位置的角度信息"""
        minDirectionDegree = 0
        nowDirection = pos - self.position

        # 使用 atan2 计算角度，范围 [-180°, 180°]
        self.degree = math.degrees(math.atan2(nowDirection.y, nowDirection.x))

        # 转换为 [0°, 360°]，并调整 y 轴向下时的角度
        self.degree = (360 - self.degree) % 360  # 反转角度以适应 y 轴向下
        self.minDegree = 360

        for direction in self.direction:
            distance = (self.direction.index(direction) * 90) % 360
            # 计算最小差值，考虑角度的周期性
            delta = min(abs(distance - self.degree),
                        360 - abs(distance - self.degree))

            if delta < self.minDegree:
                minDirectionDegree = distance
                self.minDegree = delta
                self.minDirection = direction

        if game.realToScreen(abs(nowDirection)) >= self.width:
            radius = game.screenToReal(self.width)

        else:
            radius = abs(nowDirection)

        if self.degree > minDirectionDegree:
            startAngle = math.radians(minDirectionDegree)
            endAngle = math.radians(self.degree)

        elif self.degree <= minDirectionDegree:
            startAngle = math.radians(self.degree)
            endAngle = math.radians(minDirectionDegree)

        if minDirectionDegree == 0 and self.degree > 270:
            startAngle = math.radians(self.degree)
            endAngle = math.radians(minDirectionDegree)

        # 绘制角度信息
        pygame.draw.arc(
            game.screen,
            "black",
            (
                game.realToScreen((self.position.x - radius / 2), game.x),
                game.realToScreen((self.position.y - radius / 2), game.y),
                game.realToScreen(radius),
                game.realToScreen(radius),
            ),
            startAngle,
            endAngle,
            2,
        )

        if self.minDegree <= 1.5 and self.minDegree != 0 and self.width > 10:
            self.minDegree = 0

            # 计算单位方向向量
            minDirectionUnit = self.minDirection.normalize()

            # 保持 nowDirection 的长度，但方向与 minDirection 一致
            point = self.position + minDirectionUnit * abs(nowDirection)
            option.creationPoints[1] = point
            option.isAbsorption = True

        else:
            option.isAbsorption = False

        if not self.isMouseOn():
            degreeText = str(round(self.minDegree)) + "°"
            textSize = game.fontSmall.size(degreeText)
            textX = (game.realToScreen(self.position.x +
                     (nowDirection.x / 3), game.x) - textSize[0] / 3)
            textY = (game.realToScreen(self.position.y +
                     (nowDirection.y / 3), game.y) - textSize[1] / 3)
            game.screen.blit(game.fontSmall.render(
                degreeText, True, "black"), (textX, textY))

        if text != "":
            textSize = game.fontSmall.size(text)
            textX = (game.realToScreen(self.position.x +
                     (nowDirection.x * 2 / 3), game.x) - textSize[0] * 2 / 3)
            textY = (game.realToScreen(self.position.y +
                     (nowDirection.y * 2 / 3), game.y) - textSize[1] * 2 / 3)
            game.screen.blit(game.fontSmall.render(
                text, True, "black"), (textX, textY))
