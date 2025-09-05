from typing import Self
from .ball import *
from .element import *
from .wall_position import *
from .vector2 import *
import pygame


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
        length: float,  # 轻杆的固定长度
        width: float,
        color: pygame.Color,
        dampingFactor: float = 0.1,  # 阻尼系数
    ) -> None:
        self.start: Ball | WallPosition = start
        self.end: Ball | WallPosition = end
        self.position: Vector2 = (start.getPosition() + end.getPosition()) / 2
        self.length: float = length  # 轻杆的固定长度
        self.width: float = width
        self.color: pygame.Color = color
        self.dampingFactor: float = dampingFactor  # 阻尼系数
        self.isLegal: bool = True
        self.type: str = "rod"
        
        # 轻杆的约束力
        self.constraintForce: float = 0.0
        
        # 轻杆的角度（弧度）
        self.angle: float = 0.0
        
        # 轻杆的角速度
        self.angularVelocity: float = 0.0
        
        # 轻杆的形变量（理想情况下应该接近0）
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
        """计算轻杆约束力并应用到连接的物体上
        
        实现刚性连接和力矩传递：
        1. 计算强约束力保持固定长度
        2. 应用位置修正确保刚性
        3. 计算并传递力矩
        
        Returns:
            bool: 是否成功计算并应用力
        """
        # 获取两端点位置
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()

        # 计算当前长度和方向
        deltaPosition = endPos - startPos
        currentLength = deltaPosition.magnitude()

        # 防止除零错误
        if currentLength < 0.001:
            self.deformation = 0.0
            self.constraintForce = 0.0
            return False

        # 计算单位方向向量
        direction = deltaPosition / currentLength

        # 计算形变量（与理想长度的差异）
        self.deformation = currentLength - self.length

        # 轻杆应该保持固定长度，使用强约束力
        constraintStiffness = 10000.0  # 非常大的刚度系数，确保刚性
        forceMagnitude = constraintStiffness * self.deformation
        self.constraintForce = forceMagnitude

        # 计算约束力向量
        constraintForce = direction * forceMagnitude
        
        # 更新角度
        prevAngle = self.angle
        self.updateAngle()
        
        # 计算角速度（角度变化/时间）
        # 由于没有明确的时间步长，这里使用一个近似值
        # 实际应用中应该使用真实的时间步长
        angleDiff = self.angle - prevAngle
        # 处理角度跨越2π的情况
        if angleDiff > math.pi:
            angleDiff -= 2 * math.pi
        elif angleDiff < -math.pi:
            angleDiff += 2 * math.pi
            
        # 假设时间步长为1/60秒（60fps）
        self.angularVelocity = angleDiff * 60

        # 应用约束力到两端物体
        if isinstance(self.start, Ball) and isinstance(self.end, Ball):
            # 计算相对速度
            relativeVelocity = self.end.velocity - self.start.velocity
            
            # 计算相对速度在杆方向上的分量
            relativeVelocityAlongRod = relativeVelocity.dot(direction)
            
            # 计算阻尼力（减少振荡）
            dampingForceMagnitude = self.dampingFactor * relativeVelocityAlongRod
            dampingForce = direction * dampingForceMagnitude

            # 应用力到两个球体（注意力的方向相反）
            self.start.force(constraintForce + dampingForce, isNatural=True)
            self.end.force(-constraintForce - dampingForce, isNatural=True)
            
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
                    if isinstance(self.end, Ball):
                        self.end.force(perpendicularForceStart, isNatural=True)
            
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
                    if isinstance(self.start, Ball):
                        self.start.force(perpendicularForceEnd, isNatural=True)

            # 位置修正（强制保持长度）- 刚性连接的核心
            totalMass = self.start.mass + self.end.mass
            if totalMass > 0:
                # 计算需要的位置修正量
                correction = direction * self.deformation

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
            self.start.force(constraintForce + dampingForce, isNatural=True)
            
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
            self.end.force(-constraintForce + dampingForce, isNatural=True)
            
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
        """绘制轻杆
        
        根据轻杆的状态绘制不同效果：
        1. 显示刚性连接的视觉效果
        2. 通过颜色变化表示约束力大小
        3. 显示角速度和力矩传递效果
        """
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()

        # 计算轻杆方向和长度
        direction = endPos - startPos
        currentLength = direction.magnitude()

        # 防止除零错误
        if currentLength < 0.001:
            return

        # 计算单位方向向量
        directionNorm = direction / currentLength

        # 计算垂直方向
        perpendicular = directionNorm.vertical()

        # 轻杆的绘制参数
        rodWidth = self.width

        # 计算形变比例（用于视觉效果）
        deformationRatio = currentLength / self.length

        # 绘制轻杆
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
            # 使用颜色变化来表示轻杆的约束力状态
            # 约束力越大，颜色变化越明显
            constraintForceFactor = min(abs(self.constraintForce) / 1000.0, 1.0)
            
            if abs(deformationRatio - 1.0) < 0.005:  # 几乎完全保持原长（更严格的阈值）
                drawColor = self.color

            elif deformationRatio < 1.0:  # 压缩状态
                # 压缩时颜色向红色过渡
                compressionFactor = min(abs(self.deformation) / (self.length * 0.05), 0.8)
                drawColor = colorMiddle(self.color, "red", compressionFactor * constraintForceFactor)

            else:  # 拉伸状态
                # 拉伸时颜色向蓝色过渡
                stretchFactor = min(abs(self.deformation) / (self.length * 0.05), 0.8)
                drawColor = colorMiddle(self.color, "blue", stretchFactor * constraintForceFactor)

            # 绘制主线 - 使用更粗的线条表示刚性
            pygame.draw.line(
                game.screen, drawColor, points[0], points[1], max(2, int(rodWidth))
            )

            # 在轻杆两端绘制小圆点表示连接点
            connectionRadius = max(3, int(rodWidth * 0.8))
            pygame.draw.circle(game.screen, drawColor, points[0], connectionRadius)
            pygame.draw.circle(game.screen, drawColor, points[1], connectionRadius)

            # 在轻杆中间绘制一个小标记，表示这是轻杆而非普通线段
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
