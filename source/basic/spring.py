from typing import Self
from .ball import *
from .element import *
from .wall_position import *
from .vector2 import *
import pygame
import math


class Spring(Element):
    """弹簧类，处理弹簧的显示和物理效果"""

    def __init__(
        self,
        start: Ball | WallPosition,
        end: Ball | WallPosition,
        restLength: float,  # 弹簧的自然长度
        stiffness: float,  # 弹簧刚度系数
        width: float,
        color: pygame.Color,
        dampingFactor: float = 0.1,  # 阻尼系数
    ) -> None:
        self.start: Ball | WallPosition = start
        self.end: Ball | WallPosition = end
        self.position: Vector2 = (start.getPosition() + end.getPosition()) / 2
        self.restLength: float = restLength  # 弹簧的自然长度
        self.stiffness: float = stiffness  # 弹簧刚度系数
        self.width: float = width
        self.color: pygame.Color = color
        self.dampingFactor: float = dampingFactor  # 阻尼系数
        self.isLegal: bool = True
        self.coilCount: int = 10  # 弹簧圈数
        self.type: str = "spring"

        if isinstance(start, WallPosition) and isinstance(end, WallPosition):
            self.isLegal = False

    def calculateForce(self) -> bool:
        """计算弹簧力并应用到连接的物体上"""
        # 获取两端点位置
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()

        # 计算当前长度和方向
        deltaPosition = endPos - startPos
        currentLength = deltaPosition.magnitude()

        # 防止除零错误
        if currentLength < 0.001:
            return False

        # 计算单位方向向量
        direction = deltaPosition / currentLength

        # 计算形变量（正值表示拉伸，负值表示压缩）
        deformation = currentLength - self.restLength

        # 计算弹簧力大小 (F = -k * x)，其中k是弹簧系数，x是形变量
        forceMagnitude = self.stiffness * deformation

        # 计算弹簧力向量
        springForce = direction * forceMagnitude

        # 应用弹簧力到两端物体
        if isinstance(self.start, Ball) and isinstance(self.end, Ball):
            # 计算相对速度的阻尼力
            relativeVelocity = self.end.velocity - self.start.velocity
            dampingForce = (
                direction * relativeVelocity.dot(direction) * self.dampingFactor)

            # 应用力到两个球体（注意力的方向相反）
            self.start.force(springForce + dampingForce, isNatural=True)
            self.end.force(-springForce - dampingForce, isNatural=True)

            return True

        elif isinstance(self.start, Ball) and isinstance(self.end, WallPosition):
            # 只对球体应用力
            self.start.force(springForce, isNatural=True)
            return True

        elif isinstance(self.start, WallPosition) and isinstance(self.end, Ball):
            # 只对球体应用力
            self.end.force(-springForce, isNatural=True)
            return True

        return False

    def update(self, deltaTime: float) -> Self:
        """更新弹簧状态"""
        self.calculateForce()

        # 更新弹簧中心位置
        if isinstance(self.start, Ball) and isinstance(self.end, Ball):
            self.position = (self.start.position + self.end.position) / 2

        elif isinstance(self.start, WallPosition) and isinstance(self.end, Ball):
            self.position = (self.start.getPosition() + self.end.position) / 2
            self.start.update()

        elif isinstance(self.start, Ball) and isinstance(self.end, WallPosition):
            self.position = (self.start.position + self.end.getPosition()) / 2
            self.end.update()

        else:
            ...

        return self

    def draw(self, game) -> None:
        """绘制弹簧"""
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()

        # 计算弹簧方向和长度
        direction = endPos - startPos
        currentLength = direction.magnitude()

        # 防止除零错误
        if currentLength < 0.001:
            return

        # 计算单位方向向量
        directionNorm = direction / currentLength

        # 计算垂直方向
        perpendicular = directionNorm.vertical()

        # 弹簧的振幅（弹簧的宽度）
        amplitude = self.width * 2

        # 计算形变比例（用于视觉效果）
        deformationRatio = currentLength / self.restLength

        # 调整振幅根据形变
        if deformationRatio < 1.0:  # 压缩状态
            amplitude *= 2.0 - deformationRatio  # 压缩时振幅增大
        else:  # 拉伸状态
            amplitude *= 1.0 / deformationRatio  # 拉伸时振幅减小

        # 弹簧的段数（圈数 * 2）
        segments = self.coilCount * 2

        # 绘制弹簧线
        points = []

        # 添加起点
        screenStartX = game.realToScreen(startPos.x, game.x)
        screenStartY = game.realToScreen(startPos.y, game.y)
        points.append((screenStartX, screenStartY))

        # 弹簧的第一段直线部分（不扭曲的部分）
        straightPart = min(currentLength * 0.15, self.restLength * 0.15)
        coilStart = startPos + directionNorm * straightPart

        # 添加弹簧开始扭曲的点
        screenCoilStartX = game.realToScreen(coilStart.x, game.x)
        screenCoilStartY = game.realToScreen(coilStart.y, game.y)
        points.append((screenCoilStartX, screenCoilStartY))

        # 弹簧的最后一段直线部分
        coilEnd = endPos - directionNorm * straightPart

        # 弹簧的扭曲部分长度
        coilLength = (coilEnd - coilStart).magnitude()

        # 生成弹簧的扭曲部分
        for i in range(1, segments):
            t = i / segments

            # 沿弹簧方向的位置
            basePos = coilStart + directionNorm * (coilLength * t)

            # 计算正弦波形状（弹簧的扭曲）
            # 使用正弦函数创建弹簧的波浪形状
            waveOffset = amplitude * math.sin(t * math.pi * self.coilCount * 2)

            # 应用波形偏移
            finalPos = basePos + perpendicular * waveOffset

            # 转换为屏幕坐标
            screenX = game.realToScreen(finalPos.x, game.x)
            screenY = game.realToScreen(finalPos.y, game.y)
            points.append((screenX, screenY))

        # 添加弹簧结束扭曲的点
        screenCoilEndX = game.realToScreen(coilEnd.x, game.x)
        screenCoilEndY = game.realToScreen(coilEnd.y, game.y)
        points.append((screenCoilEndX, screenCoilEndY))

        # 添加终点
        screenEndX = game.realToScreen(endPos.x, game.x)
        screenEndY = game.realToScreen(endPos.y, game.y)
        points.append((screenEndX, screenEndY))

        # 绘制弹簧线
        if len(points) > 1:

            # 使用颜色变化来表示弹簧的形变状态
            if deformationRatio < 1.0:  # 压缩状态
                # 压缩时颜色向红色过渡
                drawColor = colorMiddle(
                    self.color, "red", 1.0 - deformationRatio)

            else:  # 拉伸状态
                # 拉伸时颜色向蓝色过渡
                stretchFactor = min(deformationRatio - 1.0, 1.0)  # 限制在0-1范围内
                drawColor = colorMiddle(self.color, "blue", stretchFactor)

            pygame.draw.lines(game.screen, drawColor, False,
                              points, max(1, int(self.width)))
