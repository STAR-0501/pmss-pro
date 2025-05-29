from typing import Self
from .ball import *
from .element import *
from .wall_position import *
from .vector2 import *
import pygame
import math


class Rope(Element):
    """绳索类，处理绳索的显示和物理效果"""

    def __init__(
        self,
        start: Ball | WallPosition,
        end: Ball | WallPosition,
        length: float,
        width: float,
        color: pygame.Color,
        collisionFactor: float = 1.0,
    ) -> None:
        self.start: Ball | WallPosition = start
        self.end: Ball | WallPosition = end
        self.position: Vector2 = (start.getPosition() + end.getPosition()) / 2
        self.length: float = length
        self.width: float = width
        self.color: pygame.Color = color
        self.collisionFactor: float = collisionFactor
        self.isLegal: bool = True
        self.type: str = "rope"

        if isinstance(start, WallPosition) and isinstance(end, WallPosition):
            self.isLegal = False

    def isReachingLimit(self) -> bool:
        """判断绳索是否到达极限长度"""
        return self.length < abs(self.start.getPosition() - self.end.getPosition())

    def calculateForce(self) -> bool:
        """计算绳索力并应用到连接的物体上"""
        # 获取两端点位置
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()

        # 计算当前长度和方向
        deltaPosition = endPos - startPos
        actualDistance = deltaPosition.magnitude()

        # 防止除零错误
        if actualDistance < 0.001:
            return False

        # 计算单位方向向量
        direction = deltaPosition / actualDistance

        # 计算形变量（只考虑拉伸，绳索不会压缩）
        overlap = actualDistance - self.length

        # 只有当绳索被拉伸时才施加力
        if overlap > 0:
            # 计算绳索拉力大小（可以视为非常大的弹簧系数）
            stiffness = 1000.0  # 绳索刚度系数，比弹簧大得多
            forceMagnitude = stiffness * overlap

            # 计算绳索力向量
            ropeForce = direction * forceMagnitude

            # 应用绳索力到两端物体
            if isinstance(self.start, Ball) and isinstance(self.end, Ball):
                # 计算相对速度的阻尼力（减少振荡）
                dampingFactor = 0.1 * self.collisionFactor  # 阻尼系数与碰撞因子相关
                relativeVelocity = self.end.velocity - self.start.velocity
                dampingForce = (
                    direction * relativeVelocity.dot(direction) * dampingFactor)

                # 应用力到两个球体（注意力的方向相反）
                self.start.force(ropeForce + dampingForce, isNatural=True)
                self.end.force(-ropeForce - dampingForce, isNatural=True)

                # 位置修正（防止过度拉伸）
                totalMass = self.start.mass + self.end.mass
                separation = direction * (overlap * 0.05)  # 小幅度位置修正

                # 按质量比例分配分离量
                self.start.position += separation * (self.end.mass / totalMass)
                self.end.position -= separation * (self.start.mass / totalMass)

                return True

            elif isinstance(self.start, Ball) and isinstance(self.end, WallPosition):
                # 只对球体应用力
                self.start.force(ropeForce, isNatural=True)
                return True

            elif isinstance(self.start, WallPosition) and isinstance(self.end, Ball):
                # 只对球体应用力
                self.end.force(-ropeForce, isNatural=True)
                return True

        return False

    def update(self, deltaTime: float) -> Self:
        """更新绳索位置"""
        self.calculateForce()

        if isinstance(self.start, Ball) and isinstance(self.end, Ball):
            ...

        elif isinstance(self.start, WallPosition) and isinstance(self.end, Ball):
            self.start.update()

        elif isinstance(self.start, Ball) and isinstance(self.end, WallPosition):
            self.end.update()

        else:
            ...

        return self

    def draw(self, game) -> None:
        """绘制绳索"""
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()
        actualDistance = startPos.distance(endPos)

        # 如果绳索被拉紧，直接画直线
        if actualDistance >= self.length * 0.99:  # 允许1%的误差
            pygame.draw.line(
                game.screen,
                self.color,
                (
                    game.realToScreen(startPos.x, game.x),
                    game.realToScreen(startPos.y, game.y),
                ),
                (
                    game.realToScreen(endPos.x, game.x),
                    game.realToScreen(endPos.y, game.y),
                ),
                self.width,
            )
        else:
            # 绘制悬链线
            # 计算松弛程度
            slack = self.length - actualDistance

            # 计算方向向量
            direction = endPos - startPos
            if direction.magnitude() < 0.001:  # 防止除零错误
                direction = Vector2(1, 0)
            else:
                direction = direction.normalize()

            # 计算垂直方向
            perpendicular = direction.vertical()

            # 悬链线的最大下垂量，与松弛程度成正比
            maxSag = min(slack * 0.5, self.length * 0.3)  # 限制最大下垂量

            # 绘制多段线来近似悬链线
            segments = 20  # 分段数量
            points = []

            # 重力方向始终向下
            gravityDir = Vector2(0, 1)  # 重力方向

            # 确保下垂方向始终有向下的分量
            # 计算垂直方向与重力方向的点积
            dotWithGravity = perpendicular.dot(gravityDir)

            # 如果垂直方向与重力方向点积为负，说明垂直方向向上，需要反转
            if dotWithGravity < 0:
                perpendicular = -perpendicular

            for i in range(segments + 1):
                t = i / segments  # 参数 t 从 0 到 1

                # 线性插值计算基础位置
                basePos = startPos + direction * (actualDistance * t)

                # 计算下垂量，使用正弦函数模拟悬链线形状
                # 在中间位置下垂最大，两端为0
                sag = maxSag * math.sin(math.pi * t)

                # 计算下垂方向（重力方向和垂直方向的混合）
                # 如果绳索水平，则完全沿重力方向下垂
                # 如果绳索垂直，则沿垂直方向下垂
                dotWithHorizontal = abs(direction.dot(Vector2(1, 0)))
                sagDir = perpendicular * dotWithHorizontal + \
                    gravityDir * (1 - dotWithHorizontal)
                sagDir = sagDir.normalize()

                # 应用下垂
                finalPos = basePos + sagDir * sag

                # 转换为屏幕坐标
                screenX = game.realToScreen(finalPos.x, game.x)
                screenY = game.realToScreen(finalPos.y, game.y)
                points.append((screenX, screenY))

            # 绘制多段线
            if len(points) > 1:
                pygame.draw.lines(game.screen, self.color,
                                  False, points, self.width)
