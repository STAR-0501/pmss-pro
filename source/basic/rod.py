from typing import Self

import pygame

from .ball import *
from .element import *
from .vector2 import *
from .wall_position import *


class Rod(Element):
    """轻杆类，处理轻杆的显示和物理效果
    
    特性：
    1. 刚性连接：保持固定长度，不允许伸长或压缩
    2. 力矩传递：通过约束力传递力矩
    3. 即时位置修正：强制维持固定长度
    """

    def __init__(
        self,
        start: Ball | WallPosition,
        end: Ball | WallPosition,
        length: float,  # 弹簧的自然长度
        width: float,
        color: pygame.Color,
        dampingFactor: float = 0.1,  # 阻尼系数
        stiffness: float = 100000.0,  # 极大的弹性系数
    ) -> None:
        self.start: Ball | WallPosition = start
        self.end: Ball | WallPosition = end
        self.position: Vector2 = (start.getPosition() + end.getPosition()) / 2
        self.restLength: float = length  # 弹簧的自然长度
        self.width: float = width
        self.color: pygame.Color = color
        self.dampingFactor: float = dampingFactor  # 阻尼系数
        self.stiffness: float = stiffness  # 极大的弹性系数
        self.isLegal: bool = True
        self.type: str = "rod"
        
        self.id = randint(0, 100000000)
        
        # 弹簧力
        self.currentForce: float = 0.0
        
        # 弹簧的角度（弧度）
        self.angle: float = 0.0
        
        # 弹簧的角速度
        self.angularVelocity: float = 0.0
        
        # 弹簧的形变量
        self.deformation: float = 0.0

        if isinstance(start, WallPosition) and isinstance(end, WallPosition):
            self.isLegal = False
            
        # 初始化角度
        self.updateAngle()

    def updateAngle(self) -> None:
        """更新轻杆的角度
        
        根据两端点位置计算轻杆的当前角度
        """
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()
        
        # 计算方向向量
        direction = endPos - startPos
        
        # 计算角度（相对于x轴正方向）
        self.angle = math.atan2(direction.y, direction.x)
    
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
            self.currentForce = 0.0
            return False

        direction = deltaPosition / currentLength
        self.deformation = currentLength - self.restLength
        
        # 弹力 F = -k * x, x 是形变向量
        forceMagnitude = self.stiffness * self.deformation
        self.currentForce = forceMagnitude

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

        # 更新角度
        prevAngle = self.angle
        self.updateAngle()
        
        # 计算角速度（角度变化/时间）
        # 使用更小的时间步长以提高精度
        angleDiff = self.angle - prevAngle
        # 处理角度跨越2π的情况
        if angleDiff > math.pi:
            angleDiff -= 2 * math.pi
        elif angleDiff < -math.pi:
            angleDiff += 2 * math.pi
            
        # 使用更小的时间步长（1/120秒）以提高精度
        self.angularVelocity = angleDiff * 120

        # 如果两端都是球体，则进行力矩传递和位置修正
        if isinstance(self.start, Ball) and isinstance(self.end, Ball):
            # 力矩传递 - 计算垂直于杆的力分量
            # 对于start球体，考虑所有作用在其上的力
            if isinstance(self.start, Ball) and (len(self.start.naturalForces) > 0 or len(self.start.artificialForces) > 0):
                # 计算所有力的合力
                totalForce = Vector2(0, 0)
                for force in self.start.naturalForces:
                    totalForce += force
                for force in self.start.artificialForces:
                    totalForce += force
                
                if totalForce.magnitude() > 0:
                    # 计算外力在垂直于杆方向上的分量
                    perpendicular = direction.vertical()
                    perpendicularForceStart = perpendicular * totalForce.dot(perpendicular)
                    
                    # 将这个力分量传递给end球体，实现力矩传递
                    # 减少力矩传递以避免过度能量增加
                    if isinstance(self.end, Ball):
                        self.end.force(perpendicularForceStart * 0.3, isNatural=True)
            
            # 对于end球体，考虑所有作用在其上的力
            if isinstance(self.end, Ball) and (len(self.end.naturalForces) > 0 or len(self.end.artificialForces) > 0):
                # 计算所有力的合力
                totalForce = Vector2(0, 0)
                for force in self.end.naturalForces:
                    totalForce += force
                for force in self.end.artificialForces:
                    totalForce += force
                
                if totalForce.magnitude() > 0:
                    # 计算外力在垂直于杆方向上的分量
                    perpendicular = direction.vertical()
                    perpendicularForceEnd = perpendicular * totalForce.dot(perpendicular)
                    
                    # 将这个力分量传递给start球体，实现力矩传递
                    # 减少力矩传递以避免过度能量增加
                    if isinstance(self.start, Ball):
                        self.start.force(perpendicularForceEnd * 0.3, isNatural=True)

            # 位置修正（强制保持长度）- 刚性连接的核心
            # 使用渐进式修正以提高稳定性
            totalMass = self.start.mass + self.end.mass
            if totalMass > 0:
                # 计算需要的位置修正量，使用较小的修正系数
                correctionFactor = 0.2  # 进一步减小修正系数
                correction = direction * (self.deformation * correctionFactor)

                # 按质量比例分配修正量
                if self.start.mass > 0 and self.end.mass > 0:
                    self.start.position += correction * \
                        (self.end.mass / totalMass)
                    self.end.position -= correction * \
                        (self.start.mass / totalMass)

                elif self.start.mass > 0:  # 如果end是无限质量
                    self.start.position += correction
            
            # 力矩传递 - 计算垂直于杆的力分量
            # 对于start球体，考虑所有作用在其上的力
            if isinstance(self.start, Ball) and (len(self.start.naturalForces) > 0 or len(self.start.artificialForces) > 0):
                # 计算所有力的合力
                totalForce = Vector2(0, 0)
                for force in self.start.naturalForces:
                    totalForce += force
                for force in self.start.artificialForces:
                    totalForce += force
                
                if totalForce.magnitude() > 0:
                    # 计算外力在垂直于杆方向上的分量
                    perpendicular = direction.vertical()
                    perpendicularForceStart = perpendicular * totalForce.dot(perpendicular)
                    
                    # 将这个力分量传递给end球体，实现力矩传递
                    # 减少力矩传递以避免过度能量增加
                    if isinstance(self.end, Ball):
                        self.end.force(perpendicularForceStart * 0.5, isNatural=True)
            
            # 对于end球体，考虑所有作用在其上的力
            if isinstance(self.end, Ball) and (len(self.end.naturalForces) > 0 or len(self.end.artificialForces) > 0):
                # 计算所有力的合力
                totalForce = Vector2(0, 0)
                for force in self.end.naturalForces:
                    totalForce += force
                for force in self.end.artificialForces:
                    totalForce += force
                
                if totalForce.magnitude() > 0:
                    # 计算外力在垂直于杆方向上的分量
                    perpendicular = direction.vertical()
                    perpendicularForceEnd = perpendicular * totalForce.dot(perpendicular)
                    
                    # 将这个力分量传递给start球体，实现力矩传递
                    # 减少力矩传递以避免过度能量增加
                    if isinstance(self.start, Ball):
                        self.start.force(perpendicularForceEnd * 0.5, isNatural=True)

            # 位置修正（强制保持长度）- 刚性连接的核心
                # 使用渐进式修正以提高稳定性
                totalMass = self.start.mass + self.end.mass
                if totalMass > 0:
                    # 计算需要的位置修正量，使用较小的修正系数
                    correctionFactor = 0.3  # 渐进式修正系数
                    correction = direction * (self.deformation * correctionFactor)

                    # 按质量比例分配修正量
                    if self.start.mass > 0 and self.end.mass > 0:
                        self.start.position += correction * \
                            (self.end.mass / totalMass)
                        self.end.position -= correction * \
                            (self.start.mass / totalMass)

                    elif self.start.mass > 0:  # 如果end是无限质量
                        self.start.position += correction

                    elif self.end.mass > 0:  # 如果start是无限质量
                        self.end.position -= correction

            return True

        elif isinstance(self.start, Ball) and isinstance(self.end, WallPosition):
            # 计算球体相对于固定点的速度在杆方向上的分量
            relativeVelocityAlongRod = self.start.velocity.dot(direction)
            
            # 计算阻尼力
            dampingForceMagnitude = self.dampingFactor * relativeVelocityAlongRod
            dampingForce = direction * dampingForceMagnitude
            
            # 只对球体应用力
            self.start.force(springForceOnStart + dampingForce, isNatural=True)
            
            # 位置修正（强制保持长度）
            self.start.position += direction * self.deformation
            return True

        elif isinstance(self.start, WallPosition) and isinstance(self.end, Ball):
            # 计算球体相对于固定点的速度在杆方向上的分量
            relativeVelocityAlongRod = self.end.velocity.dot(-direction)
            
            # 计算阻尼力
            dampingForceMagnitude = self.dampingFactor * relativeVelocityAlongRod
            dampingForce = -direction * dampingForceMagnitude
            
            # 只对球体应用力
            self.end.force(-springForceOnStart + dampingForce, isNatural=True)
            
            # 位置修正（强制保持长度）
            self.end.position -= direction * self.deformation
            return True

        return False

    def update(self, deltaTime: float) -> Self:
        """更新轻杆状态
        
        计算约束力、更新角度和位置，确保刚性连接
        
        Args:
            deltaTime: 时间步长
            
        Returns:
            Self: 返回自身实例，支持链式调用
        """
        # 计算约束力和应用位置修正
        self.calculateForce()

        # 更新轻杆中心位置
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
        """绘制弹簧
        
        根据弹簧的状态绘制不同效果：
        1. 显示弹性连接的视觉效果
        2. 通过颜色变化表示弹力大小
        3. 显示角速度和力矩传递效果
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

        # 计算垂直方向
        perpendicular = directionNorm.vertical()

        # 弹簧的绘制参数
        rodWidth = self.width

        # 计算形变比例（用于视觉效果）
        deformationRatio = currentLength / self.restLength

        # 绘制弹簧
        points = []

        # 添加起点
        screenStartX = game.realToScreen(startPos.x, game.x)
        screenStartY = game.realToScreen(startPos.y, game.y)
        points.append((screenStartX, screenStartY))

        # 添加终点
        screenEndX = game.realToScreen(endPos.x, game.x)
        screenEndY = game.realToScreen(endPos.y, game.y)
        points.append((screenEndX, screenEndY))

        # 绘制轻杆线
        if len(points) > 1:
            # 使用颜色变化来表示弹簧的弹力状态
            # 弹力越大，颜色变化越明显
            forceFactor = min(abs(self.currentForce) / 1000.0, 1.0)
            
            if abs(deformationRatio - 1.0) < 0.005:  # 几乎完全保持原长（更严格的阈值）
                drawColor = self.color

            elif deformationRatio < 1.0:  # 压缩状态
                # 压缩时颜色向红色过渡
                compressionFactor = min(abs(self.deformation) / (self.restLength * 0.05), 0.8)
                drawColor = colorMiddle(self.color, "red", compressionFactor * forceFactor)

            else:  # 拉伸状态
                # 拉伸时颜色向蓝色过渡
                stretchFactor = min(abs(self.deformation) / (self.restLength * 0.05), 0.8)
                drawColor = colorMiddle(self.color, "blue", stretchFactor * forceFactor)

            # 绘制主线 - 使用更粗的线条表示刚性
            pygame.draw.line(
                game.screen, drawColor, points[0], points[1], max(2, int(rodWidth))
            )

            # 在弹簧两端绘制小圆点表示连接点
            connectionRadius = max(3, int(rodWidth * 0.8))
            pygame.draw.circle(game.screen, drawColor, points[0], connectionRadius)
            pygame.draw.circle(game.screen, drawColor, points[1], connectionRadius)

            # 在弹簧中间绘制一个小标记，表示这是弹簧而非普通线段
            midPoint = (
                (points[0][0] + points[1][0]) // 2,
                (points[0][1] + points[1][1]) // 2,
            )

            markSize = max(4, int(rodWidth * 0.9))

            # 中心标记颜色根据角速度变化
            # 角速度越大，颜色越亮
            angularVelocityFactor = min(abs(self.angularVelocity) / 10.0, 1.0)
            centerColor = colorMiddle(drawColor, "white", 0.3 + angularVelocityFactor * 0.5)
            
            pygame.draw.circle(game.screen, centerColor, midPoint, markSize)
            
            # 可选：显示力矩传递效果
            # 如果有明显的角速度，绘制一个箭头或标记表示旋转方向
            if abs(self.angularVelocity) > 1.0:
                # 计算箭头方向（垂直于杆）
                arrowDir = perpendicular
                if self.angularVelocity < 0:
                    arrowDir = -arrowDir
                
                # 计算箭头起点（杆的中点）
                arrowStart = midPoint
                
                # 计算箭头终点
                arrowLength = min(10 + abs(self.angularVelocity), 20)
                arrowEnd = (
                    int(midPoint[0] + arrowDir.x * arrowLength),
                    int(midPoint[1] + arrowDir.y * arrowLength)
                )
                
                # 绘制箭头线
                pygame.draw.line(game.screen, centerColor, arrowStart, arrowEnd, 2)
                
                # 绘制箭头头部
                headSize = 5
                headDir1 = Vector2(arrowDir.y, -arrowDir.x).normalize() * headSize
                headDir2 = Vector2(-arrowDir.y, arrowDir.x).normalize() * headSize
                
                headPoint1 = (
                    int(arrowEnd[0] + headDir1.x),
                    int(arrowEnd[1] + headDir1.y)
                )
                
                headPoint2 = (
                    int(arrowEnd[0] + headDir2.x),
                    int(arrowEnd[1] + headDir2.y)
                )
                
                pygame.draw.line(game.screen, centerColor, arrowEnd, headPoint1, 2)
                pygame.draw.line(game.screen, centerColor, arrowEnd, headPoint2, 2)
