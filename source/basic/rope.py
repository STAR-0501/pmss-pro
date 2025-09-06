from typing import Self
from .ball import *
from .element import *
from .wall_position import *
from .vector2 import *
import pygame
import math


class Rope(Element):
    """绳索类，处理绳索的显示和物理效果
    
    绳索特性：
    1. 不可伸长，只能拉紧或松弛
    2. 只有在拉紧状态下才会产生张力
    3. 松弛状态下会形成悬链线
    """

    def __init__(
        self,
        start: Ball | WallPosition,
        end: Ball | WallPosition,
        length: float,
        width: float,
        color: pygame.Color,
        collisionFactor: float = 1.0,
        tensionStiffness: float = 5000.0,  # 张力刚度系数
        dampingFactor: float = 0.2,  # 阻尼系数
    ) -> None:
        self.start: Ball | WallPosition = start
        self.end: Ball | WallPosition = end
        self.position: Vector2 = (start.getPosition() + end.getPosition()) / 2
        self.length: float = length  # 绳索的固定长度
        self.width: float = width
        self.color: pygame.Color = color
        self.collisionFactor: float = collisionFactor
        self.tensionStiffness: float = tensionStiffness  # 张力刚度系数
        self.dampingFactor: float = dampingFactor  # 阻尼系数
        self.isLegal: bool = True
        self.type: str = "rope"
        self.tension: float = 0.0  # 当前张力大小

        if isinstance(start, WallPosition) and isinstance(end, WallPosition):
            self.isLegal = False

    def isReachingLimit(self) -> bool:
        """判断绳索是否到达极限长度（被拉紧）"""
        currentLength = self.getCurrentLength()
        return currentLength >= self.length * 0.999  # 更严格的阈值，减少突然切换
    
    def getCurrentLength(self) -> float:
        """获取绳索当前长度"""
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()
        return startPos.distance(endPos)
    
    def getTension(self) -> float:
        """获取当前张力大小"""
        return self.tension

    def calculateForce(self) -> bool:
        """计算绳索力并应用到连接的物体上，优化过渡效果"""
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()
        deltaPosition = endPos - startPos
        actualDistance = deltaPosition.magnitude()

        if actualDistance < 0.001:
            self.tension = 0.0
            return False

        direction = deltaPosition / actualDistance
        extension = actualDistance - self.length
        self.tension = 0.0

        if extension > 0:
            forceMagnitude = self.tensionStiffness * extension
            self.tension = forceMagnitude
            ropeForce = direction * forceMagnitude

            dampingForce = Vector2(0, 0)
            if isinstance(self.start, Ball) and isinstance(self.end, Ball):
                relativeVelocity = self.end.velocity - self.start.velocity
                dampingComponent = relativeVelocity.dot(direction)
                if dampingComponent > 0:
                    dampingForce = direction * dampingComponent * self.dampingFactor

            if isinstance(self.start, Ball):
                self.start.force(ropeForce + dampingForce, isNatural=True)
            if isinstance(self.end, Ball):
                self.end.force(-ropeForce - dampingForce, isNatural=True)

            # --- 优化的渐进式位置校正 ---
            # 目标：使绳子在拉伸后能更自然、更快速地恢复原长，从而改善动画过渡
            correction_ratio = min(0.8, (extension / self.length) * 2.0)
            correction = direction * (extension * correction_ratio)

            if isinstance(self.start, Ball) and isinstance(self.end, Ball):
                totalMass = self.start.mass + self.end.mass
                if totalMass > 0:
                    start_correction = correction * (self.end.mass / totalMass)
                    end_correction = correction * (self.start.mass / totalMass)
                    self.start.position += start_correction
                    self.end.position -= end_correction
            elif isinstance(self.start, Ball):
                self.start.position += correction
            elif isinstance(self.end, Ball):
                self.end.position -= correction
            
            return True

        return False

    def update(self, deltaTime: float) -> Self:
        """更新绳索位置和物理状态"""
        self.calculateForce()
        if isinstance(self.start, Ball) and isinstance(self.end, Ball):
            self.position = (self.start.position + self.end.position) / 2
        elif isinstance(self.start, WallPosition) and isinstance(self.end, Ball):
            self.position = (self.start.getPosition() + self.end.position) / 2
            self.start.update()
        elif isinstance(self.start, Ball) and isinstance(self.end, WallPosition):
            self.position = (self.start.position + self.end.getPosition()) / 2
            self.end.update()
        else:
            pass
        return self

    def draw(self, game) -> None:
        """绘制绳索，实现拉紧（直线）和松弛（悬链线）之间的平滑过渡"""
        startPos = self.start.getPosition()
        endPos = self.end.getPosition()
        actualDistance = startPos.distance(endPos)

        screen_start = (game.realToScreen(startPos.x, game.x), game.realToScreen(startPos.y, game.y))
        screen_end = (game.realToScreen(endPos.x, game.x), game.realToScreen(endPos.y, game.y))

        # 计算过渡因子，实现平滑过渡效果
        transition_factor = min(max((actualDistance / self.length - 0.99) / 0.01, 0.0), 1.0)
        
        if transition_factor >= 1.0 or self.isReachingLimit():
            # 完全拉直状态
            drawColor = self.color
            if self.tension > 0:
                tensionFactor = min(self.tension / (self.tensionStiffness * 0.1), 1.0)
                drawColor = colorMiddle(self.color, "red", tensionFactor * 0.7)
            pygame.draw.line(game.screen, drawColor, screen_start, screen_end, self.width)
        elif transition_factor <= 0.0:
            # 完全松弛状态，绘制悬链线
            self._drawCatenary(game, startPos, endPos, actualDistance)
        else:
            # 混合状态，结合直线和悬链线
            self._drawTransitionRope(game, startPos, endPos, actualDistance, transition_factor)

    def _drawCatenary(self, game, startPos: Vector2, endPos: Vector2, actualDistance: float) -> None:
        """绘制悬链线"""
        num_segments = 24
        points = []
        d = actualDistance
        L = self.length

        if d < 1e-6: return

        direction = (endPos - startPos).normalize()
        gravityDir = Vector2(0, 1)
        sagComponent = gravityDir - direction * direction.dot(gravityDir)
        sagDir = sagComponent.normalize() if sagComponent.magnitude() > 1e-6 else direction.vertical()

        a = 0.0
        if L > d:
            try:
                k = L / d
                z = math.sqrt(6 * (k - 1))
                for _ in range(5):
                    if z < 1e-8: break
                    if z > 700: z = 700; break
                    sinh_z = math.sinh(z)
                    cosh_z = math.cosh(z)
                    f_z = sinh_z - k * z
                    fp_z = cosh_z - k
                    if abs(fp_z) < 1e-9: break
                    z_new = z - f_z / fp_z
                    if abs(z_new - z) < 1e-9: z = z_new; break
                    z = z_new
                if z > 1e-8: a = d / (2 * z)
            except (ValueError, OverflowError):
                a = 0.0

        if a > 1e-6:
            try:
                c = a * math.cosh(d / (2 * a))
                for i in range(num_segments + 1):
                    t = i / num_segments
                    x_local = d * (t - 0.5)
                    y_local = c - a * math.cosh(x_local / a)
                    basePos = startPos + direction * (d * t)
                    finalPos = basePos + sagDir * y_local
                    points.append((game.realToScreen(finalPos.x, game.x), game.realToScreen(finalPos.y, game.y)))
            except (ValueError, OverflowError):
                a = 0.0

        if a < 1e-6:
            maxSag = math.sqrt(max(0, L*L - d*d)) / 2
            for i in range(num_segments + 1):
                t = i / num_segments
                basePos = startPos + direction * (d * t)
                sag = maxSag * math.sin(math.pi * t)
                finalPos = basePos + sagDir * sag
                points.append((game.realToScreen(finalPos.x, game.x), game.realToScreen(finalPos.y, game.y)))

        if len(points) > 1:
            pygame.draw.lines(game.screen, self.color, False, points, self.width)

    def _drawTransitionRope(self, game, startPos: Vector2, endPos: Vector2, actualDistance: float, transition_factor: float) -> None:
        """绘制过渡状态的绳索"""
        # 在过渡状态下，我们通过插值方式混合直线和悬链线
        num_segments = 24
        points = []
        d = actualDistance
        L = self.length

        if d < 1e-6: return

        direction = (endPos - startPos).normalize()
        gravityDir = Vector2(0, 1)
        sagComponent = gravityDir - direction * direction.dot(gravityDir)
        sagDir = sagComponent.normalize() if sagComponent.magnitude() > 1e-6 else direction.vertical()

        # 计算悬链线点
        catenary_points = []
        a = 0.0
        if L > d:
            try:
                k = L / d
                z = math.sqrt(6 * (k - 1))
                for _ in range(5):
                    if z < 1e-8: break
                    if z > 700: z = 700; break
                    sinh_z = math.sinh(z)
                    cosh_z = math.cosh(z)
                    f_z = sinh_z - k * z
                    fp_z = cosh_z - k
                    if abs(fp_z) < 1e-9: break
                    z_new = z - f_z / fp_z
                    if abs(z_new - z) < 1e-9: z = z_new; break
                    z = z_new
                if z > 1e-8: a = d / (2 * z)
            except (ValueError, OverflowError):
                a = 0.0

        if a > 1e-6:
            try:
                c = a * math.cosh(d / (2 * a))
                for i in range(num_segments + 1):
                    t = i / num_segments
                    x_local = d * (t - 0.5)
                    y_local = c - a * math.cosh(x_local / a)
                    basePos = startPos + direction * (d * t)
                    finalPos = basePos + sagDir * y_local
                    catenary_points.append(finalPos)
            except (ValueError, OverflowError):
                a = 0.0

        if a < 1e-6 or len(catenary_points) == 0:
            maxSag = math.sqrt(max(0, L*L - d*d)) / 2
            for i in range(num_segments + 1):
                t = i / num_segments
                basePos = startPos + direction * (d * t)
                sag = maxSag * math.sin(math.pi * t)
                finalPos = basePos + sagDir * sag
                catenary_points.append(finalPos)

        # 通过插值生成过渡点
        for i in range(num_segments + 1):
            t = i / num_segments
            catenary_point = catenary_points[i]
            linear_point = startPos + direction * (d * t)
            
            # 根据过渡因子插值
            interpolated_point = linear_point * transition_factor + catenary_point * (1 - transition_factor)
            points.append((game.realToScreen(interpolated_point.x, game.x), game.realToScreen(interpolated_point.y, game.y)))

        if len(points) > 1:
            pygame.draw.lines(game.screen, self.color, False, points, self.width)
