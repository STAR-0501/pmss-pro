from typing import Self
from .ball import *
from .element import *
from .wall_position import *
from .vector2 import *
import pygame


class Rod(Element):
    """轻杆类，处理轻杆的显示和物理效果"""

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

        if isinstance(start, WallPosition) and isinstance(end, WallPosition):
            self.isLegal = False

    def calculateForce(self) -> bool:
        """计算轻杆约束力并应用到连接的物体上"""
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

        # 计算形变量（与理想长度的差异）
        deformation = currentLength - self.length

        # 轻杆应该保持固定长度，使用强约束力
        constraintStiffness = 5000.0  # 非常大的刚度系数
        forceMagnitude = constraintStiffness * deformation

        # 计算约束力向量
        constraintForce = direction * forceMagnitude

        # 应用约束力到两端物体
        if isinstance(self.start, Ball) and isinstance(self.end, Ball):
            # 计算相对速度的阻尼力（减少振荡）
            relativeVelocity = self.end.velocity - self.start.velocity
            dampingForce = (
                direction * relativeVelocity.dot(direction) * self.dampingFactor)

            # 应用力到两个球体（注意力的方向相反）
            self.start.force(constraintForce + dampingForce, isNatural=True)
            self.end.force(-constraintForce - dampingForce, isNatural=True)

            # 位置修正（强制保持长度）
            totalMass = self.start.mass + self.end.mass
            if totalMass > 0:
                # 计算需要的位置修正量
                correction = direction * deformation

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
            # 只对球体应用力
            self.start.force(constraintForce, isNatural=True)
            # 位置修正（强制保持长度）
            self.start.position += direction * deformation
            return True

        elif isinstance(self.start, WallPosition) and isinstance(self.end, Ball):
            # 只对球体应用力
            self.end.force(-constraintForce, isNatural=True)
            # 位置修正（强制保持长度）
            self.end.position -= direction * deformation
            return True

        return False

    def update(self, deltaTime: float) -> Self:
        """更新轻杆状态"""
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

        else:
            ...

        return self

    def draw(self, game) -> None:
        """绘制轻杆"""
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

            # 使用颜色变化来表示轻杆的状态
            if abs(deformationRatio - 1.0) < 0.01:  # 几乎保持原长
                drawColor = self.color

            elif deformationRatio < 1.0:  # 压缩状态
                # 压缩时颜色向红色过渡
                compressionFactor = min(
                    1.0 - deformationRatio, 0.5
                )  # 限制在0-0.5范围内
                drawColor = colorMiddle(
                    self.color, "red", compressionFactor * 2)

            else:  # 拉伸状态
                # 拉伸时颜色向蓝色过渡
                stretchFactor = min(deformationRatio - 1.0, 0.5)  # 限制在0-0.5范围内
                drawColor = colorMiddle(self.color, "blue", stretchFactor * 2)

            # 绘制主线
            pygame.draw.line(
                game.screen, drawColor, points[0], points[1], max(
                    1, int(rodWidth))
            )

            # 在轻杆两端绘制小圆点表示连接点
            connectionRadius = max(2, int(rodWidth * 0.7))
            pygame.draw.circle(game.screen, drawColor,
                               points[0], connectionRadius)
            pygame.draw.circle(game.screen, drawColor,
                               points[1], connectionRadius)

            # 在轻杆中间绘制一个小标记，表示这是轻杆而非普通线段
            midPoint = (
                (points[0][0] + points[1][0]) // 2,
                (points[0][1] + points[1][1]) // 2,
            )

            markSize = max(3, int(rodWidth * 0.8))

            pygame.draw.circle(
                game.screen, colorMiddle(
                    drawColor, "white", 0.3), midPoint, markSize
            )
