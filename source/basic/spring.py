import math
from typing import Self

import pygame

from .ball import *
from .element import *
from .vector2 import *
from .wall_position import *


class Spring(Element):
    """弹簧类，处理弹簧的显示和物理效果
    
    特性：
    1. 遵循胡克定律：F = -k * x，其中k是弹簧刚度，x是形变量
    2. 存储弹性势能：E = 0.5 * k * x^2
    3. 考虑阻尼力：F_damping = -c * v，其中c是阻尼系数，v是相对速度
    """

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
        self.deformation: float = 0.0  # 当前形变量
        self.potentialEnergy: float = 0.0  # 当前弹性势能
        self.currentForce: float = 0.0  # 当前弹力大小

        if isinstance(start, WallPosition) and isinstance(end, WallPosition):
            self.isLegal = False

    def calculateForce(self) -> bool:
        """计算弹簧力并应用到连接的物体上

        根据胡克定律和阻尼效应，精确计算并施加力，确保物理模拟的准确性。
        """
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()
        deltaPosition = endPos - startPos
        currentLength = deltaPosition.magnitude()

        if currentLength < 1e-6:
            self.deformation = 0.0
            self.potentialEnergy = 0.0
            self.currentForce = 0.0
            return False

        direction = deltaPosition / currentLength
        self.deformation = currentLength - self.restLength
        
        # 弹力 F = -k * x, x 是形变向量
        # F_on_end = -stiffness * deformation * direction
        # F_on_start = +stiffness * deformation * direction
        forceMagnitude = self.stiffness * self.deformation
        self.currentForce = forceMagnitude
        self.potentialEnergy = 0.5 * self.stiffness * self.deformation**2

        springForceOnStart = direction * forceMagnitude

        # --- 统一且修正的阻尼力计算 ---
        # 阻尼力 F_damping = -c * v_relative，其中 v_relative 是沿弹簧方向的相对速度
        v_start = self.start.velocity if isinstance(self.start, Ball) else Vector2(0, 0)
        v_end = self.end.velocity if isinstance(self.end, Ball) else Vector2(0, 0)
        relative_velocity = v_end - v_start
        v_rel_along_spring = relative_velocity.dot(direction)
        
        # 阻尼力与相对速度方向相反
        dampingForceMagnitude = self.dampingFactor * v_rel_along_spring
        dampingForceOnStart = direction * dampingForceMagnitude

        # --- 将力和阻尼施加到物体上 ---
        if isinstance(self.start, Ball):
            self.start.force(springForceOnStart + dampingForceOnStart, isNatural=True)
        
        if isinstance(self.end, Ball):
            self.end.force(-(springForceOnStart + dampingForceOnStart), isNatural=True)

        return True

    def update(self, deltaTime: float) -> Self:
        """更新弹簧状态
        
        计算弹簧力、弹性势能，并更新弹簧位置
        
        Args:
            deltaTime: 时间步长
            
        Returns:
            Self: 返回自身实例，支持链式调用
        """
        # 计算弹簧力和弹性势能
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

        elif isinstance(self.start, WallPosition) and isinstance(self.end, WallPosition):
            self.position = (self.start.getPosition() + self.end.getPosition()) / 2
            self.start.update()
            self.end.update()

        return self

    def draw(self, game) -> None:
        """绘制弹簧 - 固定频率振幅版本
        
        使用固定的正弦波频率和振幅，基于初始距离和物体半径均值
        移除所有形变指示器，保持简洁的视觉效果
        """
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
        perpendicular = directionNorm.vertical()

        # 固定振幅：基于两边物体的半径均值
        startRadius = getattr(self.start, 'radius', self.width) if isinstance(self.start, Ball) else self.width
        endRadius = getattr(self.end, 'radius', self.width) if isinstance(self.end, Ball) else self.width
        meanRadius = (startRadius + endRadius) / 2
        baseRadius = meanRadius * 0.8  # 使用固定振幅
        deformationRatio = currentLength / self.restLength
        
        # 平滑的形变限制（使用平滑过渡而非硬截断）
        if deformationRatio < 0.3:
            # 平滑过渡到最小长度
            t = (deformationRatio - 0.1) / 0.2
            deformationRatio = 0.3 + (deformationRatio - 0.3) * max(0, t)
        elif deformationRatio > 4.0:
            # 平滑过渡到最大长度
            t = (4.5 - deformationRatio) / 0.5
            deformationRatio = 4.0 + (deformationRatio - 4.0) * max(0, t)

        # 固定频率：基于初始自然长度和半径均值
        startRadius = getattr(self.start, 'radius', self.width) if isinstance(self.start, Ball) else self.width
        endRadius = getattr(self.end, 'radius', self.width) if isinstance(self.end, Ball) else self.width
        meanRadius = (startRadius + endRadius) / 2
        
        # 固定频率：初始状态下的标准频率
        fixedFrequency = 2 * math.pi * self.coilCount / self.restLength
        actualCoils = self.coilCount  # 保持固定圈数
        
        # 绘制参数
        lineWidth = max(1, int(self.width * 0.6))
        
        # 颜色设计 - 更平滑的渐变
        baseColor = self.color
        
        # 确保baseColor是RGB元组格式
        if isinstance(baseColor, str):
            colorMap = {
                "red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255),
                "yellow": (255, 255, 0), "purple": (128, 0, 128), "orange": (255, 165, 0),
                "black": (0, 0, 0), "white": (255, 255, 255), "gray": (128, 128, 128),
                "cyan": (0, 255, 255), "magenta": (255, 0, 255)
            }
            baseColor = colorMap.get(baseColor.lower(), (120, 120, 120))
        
        # 平滑的颜色过渡
        colorIntensity = min(1.0, abs(deformationRatio - 1.0) * 1.5)
        if deformationRatio < 1.0:  # 压缩
            # 从基础色到橙红色的平滑过渡
            r = int(baseColor[0] + (255 - baseColor[0]) * colorIntensity * 0.7)
            g = int(baseColor[1] * (1 - colorIntensity * 0.5))
            b = int(baseColor[2] * (1 - colorIntensity * 0.8))
        else:  # 拉伸
            # 从基础色到蓝紫色的平滑过渡
            r = int(baseColor[0] * (1 - colorIntensity * 0.5))
            g = int(baseColor[1] + (200 - baseColor[1]) * colorIntensity * 0.7)
            b = int(baseColor[2] + (255 - baseColor[2]) * colorIntensity * 0.7)
        
        drawColor = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

        # 生成流畅的螺旋弹簧点
        points = []
        
        # 起点
        screenStartX = game.realToScreen(startPos.x, game.x)
        screenStartY = game.realToScreen(startPos.y, game.y)
        
        # 动态计算直线段长度（随长度自适应）
        straightLength = min(currentLength * 0.08, 15)
        
        # 螺旋段起点
        spiralStart = startPos + directionNorm * straightLength
        spiralEnd = endPos - directionNorm * straightLength
        spiralLength = max(0, (spiralEnd - spiralStart).magnitude())
        
        # 使用更多点确保平滑度
        totalPoints = max(30, int(actualCoils * 12))
        
        # 生成平滑的螺旋路径
        for i in range(totalPoints + 1):
            t = i / totalPoints
            
            # 沿弹簧方向的基础位置
            basePos = spiralStart + directionNorm * (spiralLength * t)
            
            # 螺旋相位（使用连续的实际线圈数）
            phase = t * 2 * math.pi * actualCoils
            
            # 半径随长度微调（模拟真实弹簧的透视效果）
            radiusVariation = 1.0 + math.sin(phase * 0.3) * 0.1
            currentRadius = baseRadius * radiusVariation
            
            # 螺旋偏移
            spiralX = math.cos(phase) * currentRadius
            spiralY = math.sin(phase) * currentRadius
            spiralOffset = perpendicular * spiralX + directionNorm.vertical() * spiralY
            
            # 添加自然的弹性弯曲
            elasticity = 1.0 - abs(deformationRatio - 1.0) * 0.3
            spiralOffset = spiralOffset * max(0.5, elasticity)
            
            # 最终位置
            finalPos = basePos + spiralOffset
            
            screenX = game.realToScreen(finalPos.x, game.x)
            screenY = game.realToScreen(finalPos.y, game.y)
            
            if i == 0:
                # 包含直线连接段
                points.append((screenStartX, screenStartY))
                points.append((game.realToScreen(spiralStart.x, game.x), game.realToScreen(spiralStart.y, game.y)))
            
            points.append((screenX, screenY))
            
            if i == totalPoints:
                # 包含终点连接段
                points.append((game.realToScreen(spiralEnd.x, game.x), game.realToScreen(spiralEnd.y, game.y)))
                points.append((game.realToScreen(endPos.x, game.x), game.realToScreen(endPos.y, game.y)))

        # 使用抗锯齿绘制
        if len(points) > 1:
            # 使用抗锯齿线条提高视觉质量
            pygame.draw.aalines(game.screen, drawColor, False, points)
            # 叠加粗线增强立体感
            if lineWidth > 1:
                pygame.draw.lines(game.screen, drawColor, False, points, lineWidth)

            # 在两端绘制连接圆点，突出金属连接件
            end_radius = max(2, int(self.width * 1.2))
            pygame.draw.circle(game.screen, drawColor, (screenStartX, screenStartY), end_radius)
            end_screen_x = game.realToScreen(endPos.x, game.x)
            end_screen_y = game.realToScreen(endPos.y, game.y)
            pygame.draw.circle(game.screen, drawColor, (end_screen_x, end_screen_y), end_radius)
