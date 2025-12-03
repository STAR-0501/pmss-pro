import copy
from random import random
from typing import Self

import pygame

from .collision_line import *
from .color import *
from .element import *
from .vector2 import *


class Ball(Element):
    """球体物理实体类，处理运动学计算和碰撞响应"""

    def __init__(
        self,
        position: Vector2,
        radius: float,
        color: pygame.Color,
        mass: float,
        velocity: Vector2,
        artificialForces: list[Vector2],
        gravity: float = 1,
        collisionFactor: float = 1,
        gravitation: bool = False,
        electricCharge: float = 0,
    ) -> None:
        self.position: Vector2 = position
        self.radius: float = radius
        self.color: pygame.Color = color
        self.mass: float = mass
        self.velocity: Vector2 = velocity
        self.displayedVelocity: Vector2 = ZERO
        self.displayedVelocityFactor: float = 0
        self.naturalForces: list[Vector2] = []
        self.artificialForces: list[Vector2] = artificialForces
        self.acceleration: Vector2 = ZERO
        self.displayedAcceleration: Vector2 = ZERO
        self.displayedAccelerationFactor: float = 0
        self.gravity: float = gravity
        self.highLighted: bool = False
        self.collisionFactor: float = collisionFactor
        self.airResistance: float = 1
        self.gravitation: bool = gravitation
        self.type: str = "ball"
        self.isFollowing: bool = False
        self.isShowingInfo: bool = False
        self.attrs: list[dict] = []
        self.electricCharge: float = electricCharge
        self.leaveTrail: bool = False
        self.trailPoints: list[Vector2] = []
        
        self.id = randint(0, 100000000)
        self.updateAttrsList()

    def isPosOn(self, game, pos: Vector2) -> bool:
        """检测坐标点是否在球体范围内"""

        # 计算距离平方
        distanceSquared = (pos.x - self.position.x) ** 2 + (
            pos.y - self.position.y
        ) ** 2

        # 对于小球增加一个最小点击半径（例如1.5个实际半径）
        effectiveRadius = max(
            self.radius, 5.0 / game.ratio
        )  # 确保点击区域至少有5个屏幕像素

        # 与有效半径平方比较
        return distanceSquared <= effectiveRadius**2

    def isCollidedByBall(self, other: Self) -> bool:
        """检测球与球之间的碰撞"""
        distance = self.position.distance(other.position)
        return distance <= self.radius + other.radius

    def setAttr(self, key: str, value: str) -> None:
        """设置属性值"""
        if value != "":

            if key == "color":
                self.color = value

            if key == "radius":
                self.radius = float(value)

            if key == "mass":
                self.mass = float(value)
                
            if key == "collisionFactor":
                self.collisionFactor = float(value)
                
            if key == "electricCharge":
                self.electricCharge = float(value)

            if key == "leaveTrail":
                try:
                    if isinstance(value, str):
                        self.leaveTrail = value.lower() in ["true", "1", "yes"]
                    else:
                        self.leaveTrail = bool(value)
                except Exception:
                    ...

    def copy(self, game) -> None:
        """自我复制"""
        self.isFollowing = False
        newBall = copy.deepcopy(self)
        isMoving = True
        game.elements["all"].append(newBall)
        game.elements["ball"].append(newBall)

        while isMoving:
            newBall.position = Vector2(
                game.screenToReal(pygame.mouse.get_pos()[0], game.x),
                game.screenToReal(pygame.mouse.get_pos()[1], game.y),
            )

            newBall.velocity = ZERO
            newBall.forces = []
            newBall.draw(game)

            game.update()
            pygame.display.update()
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    game.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        isMoving = False

    def follow(self, game) -> None:
        """使视角跟随"""
        # 计算屏幕中心在游戏世界坐标系中的位置
        screenCenterX = -game.x + game.screen.get_width() / (2 * game.ratio)
        screenCenterY = -game.y + game.screen.get_height() / (2 * game.ratio)

        # 计算 self.position 与屏幕中心的偏移量
        offsetX = self.position.x - screenCenterX
        offsetY = self.position.y - screenCenterY

        # 更新屏幕在游戏世界坐标系中的位置
        game.x -= offsetX
        game.y -= offsetY

    def isCollidedByLine(self, line: CollisionLine) -> bool:
        """检测球与线段的碰撞"""
        # 检查线段的起点和终点是否重合
        if line.start.distance(line.end) < 1e-5:
            return False

        AB = line.end - line.start
        AP = self.position - line.start
        projectionRatio = AP.dot(AB) / AB.dot(AB)

        if line.isLine:  # 直线无限延长
            closestPoint = line.start + AB * projectionRatio

        else:  # 普通线段
            projectionRatioClamped = max(0, min(projectionRatio, 1))
            closestPoint = line.start + AB * projectionRatioClamped

        distance = self.position.distance(closestPoint)
        return distance <= self.radius

    def accelerate(self) -> Vector2:
        """计算当前加速度"""
        self.acceleration.zero()

        for force in self.artificialForces:
            self.acceleration += force / self.mass

        for force in self.naturalForces:
            self.acceleration += force / self.mass

        self.acceleration += Vector2(0, 98.6 * self.gravity)
        return self.acceleration

    def force(self, force: Vector2, isNatural: bool = False) -> Vector2:
        """施加外力并更新加速度"""
        if isNatural:
            self.naturalForces.append(force)

        else:
            self.artificialForces.append(force)

        return self.accelerate()

    def resetForce(self, isNatural: bool = False) -> None:
        """重置外力"""
        if isNatural:
            self.naturalForces.clear()
        else:
            self.artificialForces.clear()

        self.acceleration.zero()
        self.accelerate()

    def updateAttrsList(self) -> None:
        """更新属性列表"""
        self.attrs = [
            {"type": "mass", "value": self.mass, "min": 0.1, "max": 32767},
            {"type": "radius", "value": self.radius, "min": 1, "max": 1024},
            {"type": "color", "value": self.color,
                "min": "#000000", "max": "#FFFFFF"},
            {"type": "electricCharge", "value": self.electricCharge, "min": -1000000, "max": 1000000},
        ]

    def update(self, deltaTime: float) -> Self:
        """更新物理状态"""
        self.accelerate()
        substeps = 10  # 从4增加到10
        deltaTime /= substeps

        for _ in range(substeps):
            self.velocity += self.acceleration * deltaTime
            self.position += (
                self.velocity + self.acceleration * deltaTime * 20**0.5
            ) * deltaTime

        self.velocity *= self.airResistance**deltaTime

        # self.displayedVelocity += (self.velocity - self.displayedVelocity) * 0.05
        # self.displayedAcceleration += (self.acceleration - self.displayedAcceleration) * 0.05
        self.displayedVelocityFactor *= 0.95
        self.displayedAccelerationFactor *= 0.95

        self.updateAttrsList()
        if self.leaveTrail:
            try:
                self.trailPoints.append(self.position.copy())
                if len(self.trailPoints) > 2000:
                    del self.trailPoints[0]
            except Exception:
                ...
        return self

    def draw(self, game) -> None:
        """绘制带渐变效果的小球"""
        if self.leaveTrail and self.trailPoints:
            draw_color = colorStringToTuple(self.color) if isinstance(self.color, str) else self.color
            for p in self.trailPoints:
                sx = game.realToScreen(p.x, game.x)
                sy = game.realToScreen(p.y, game.y)
                try:
                    pygame.draw.circle(game.screen, draw_color, (sx, sy), 2)
                except Exception:
                    ...
        if self.highLighted:
            pygame.draw.circle(
                game.screen,
                (255, 255, 0),
                (
                    game.realToScreen(self.position.x, game.x),
                    game.realToScreen(self.position.y, game.y),
                ),
                game.realToScreen(self.radius + 0.5),
                0,
            )

        # 确保颜色是tuple格式
        if isinstance(self.color, str):
            color = colorStringToTuple(self.color)
        else:
            color = self.color

        circleNumber = 20  # 固定20个同心圆

        # 绘制渐变效果
        for number in range(circleNumber):
            # 计算当前半径比例（从1.0到0.0）
            ratio = number / (circleNumber - 1)  # 修正比例计算

            # 当前实际半径
            currentRadius = self.radius * (1 - ratio)

            # 颜色混合计算（外部保持原色，内部变浅）
            # 混合比例：外部（ratio=0）保持原色，内部（ratio=1）变浅50%
            mixRatio = ratio  # 使用ratio来控制混合比例
            red = int(color[0] + (255 - color[0]) * mixRatio * 0.5)
            green = int(color[1] + (255 - color[1]) * mixRatio * 0.5)
            blue = int(color[2] + (255 - color[2]) * mixRatio * 0.5)

            # 透明度控制（外部不透明，内部半透明）
            alpha = int(255 * (1 - ratio * 0.5))  # 保持最低50%透明度

            # 转换坐标和尺寸
            pos = (
                game.realToScreen(self.position.x, game.x),
                game.realToScreen(self.position.y, game.y),
            )

            drawRadius = game.realToScreen(currentRadius)

            # 创建临时surface实现透明度
            tempSurface = pygame.Surface(
                (drawRadius * 2, drawRadius * 2), pygame.SRCALPHA)

            pygame.draw.circle(
                tempSurface,
                (red, green, blue, alpha),
                (drawRadius, drawRadius),
                drawRadius,
                0,
            )

            game.screen.blit(
                tempSurface, (pos[0] - drawRadius, pos[1] - drawRadius))

        self.highLighted = False

    def reboundByWall(self, wall: Self) -> Vector2:
        """处理与墙体的碰撞反弹"""
        direction = self.position - wall.position
        self.position += direction * 0.1
        
        # 计算墙体法线
        normal = direction.normalize()
        
        # 速度反射（保留切线分量）
        velocityNormal = self.velocity.dot(normal)
        self.velocity -= normal * (2 * velocityNormal)
        
        # 应用碰撞因子
        velocityNormalAfterRebound = self.velocity.dot(normal)
        self.velocity += normal * (velocityNormalAfterRebound * (self.collisionFactor * wall.collisionFactor - 1))
        
        return self.velocity

    def reboundByLine(
        self, line: CollisionLine, timeIsReversed: bool = False
    ) -> Vector2:
        """处理与线段的碰撞反弹逻辑"""
        AB = line.end - line.start
        lineLength = AB.dot(AB)

        if abs(self.velocity) == 0:
            cosine = 1

        else:
            cosine = abs(self.velocity.y) / abs(self.velocity)

        # 处理零长度线段
        if lineLength < 1e-5:
            return self.velocity

        self.displayedVelocity = (
            self.velocity + (self.displayedVelocity - self.velocity) * self.displayedVelocityFactor)
        self.displayedVelocityFactor = 1

        AP = self.position - line.start
        projectionRatio = AP.dot(AB) / lineLength

        # 计算最近点和法线
        if line.isLine:  # 直线的情况
            closest = line.start + AB * projectionRatio
            edgeNormal = Vector2(-AB.y, AB.x).normalize()
            # 根据球的位置确定法线方向
            normal = (edgeNormal if (self.position -
                      closest).dot(edgeNormal) > 0 else -edgeNormal)

        else:  # 线段的情况

            if projectionRatio < 0:
                closest = line.start
                normal = (self.position - closest).normalize()

            elif projectionRatio > 1:
                closest = line.end
                normal = (self.position - closest).normalize()

            else:
                closest = line.start + AB * projectionRatio
                edgeNormal = Vector2(-AB.y, AB.x).normalize()
                normal = (edgeNormal if (self.position -
                          closest).dot(edgeNormal) > 0 else -edgeNormal)

        # 位置修正
        overlap = self.radius - self.position.distance(closest)

        if overlap > 0:
            # 更精确的位置修正，穿透深度较大时增加能量损失
            energyLossFactor = 1 + min(1, overlap / self.radius)
            self.position += normal * (overlap * energyLossFactor)

            # 速度反射（保留切线分量）
            velocityNormal = self.velocity.dot(normal)
            self.velocity -= normal * (2 * velocityNormal)

            # 将法向分量乘以 self.collisionFactor
            velocityNormalAfterRebound = self.velocity.dot(normal)
            self.velocity += normal * (
                velocityNormalAfterRebound *
                (
                    (
                        self.collisionFactor * line.collisionFactor
                        if not timeIsReversed
                        else 1 / self.collisionFactor / line.collisionFactor
                    )
                    - 1
                )
            )
            
            # 不再调整速度大小
            # 原代码：
            # self.velocity = (
            #     self.velocity.copy().normalize() * abs(
            #         abs(self.velocity) ** 2 - 2 * 98.6 *
            #         (1 - cosine**2) ** 0.5 * overlap
            #     ) ** 0.5
            # )

        return self.velocity

    def reboundByBall(self, ball: Self) -> Vector2:
        """处理球与球之间的碰撞响应"""
        # 计算总质量
        totalMass = self.mass + ball.mass

        # 计算实际间距
        deltaPosition = self.position - ball.position
        actualDistance = abs(deltaPosition)
        minDistance = self.radius + ball.radius

        # 处理零距离特殊情况
        if actualDistance < 1e-5:
            # 使用随机方向避免零向量
            normal = Vector2(1, 0) if random() > 0.5 else Vector2(-1, 0)
            actualDistance = minDistance

        else:
            normal = deltaPosition / actualDistance

        self.displayedVelocity = (
            self.velocity + (self.displayedVelocity - self.velocity) * self.displayedVelocityFactor)
        self.displayedVelocityFactor = 1

        ball.displayedVelocity = (
            ball.velocity + (ball.displayedVelocity - ball.velocity) * ball.displayedVelocityFactor)
        ball.displayedVelocityFactor = 1

        tangent = normal.vertical()

        # 记录碰撞前速度用于位置修正
        originalVelocity1 = self.velocity.copy()
        originalVelocity2 = ball.velocity.copy()

        # 分解速度分量
        velocityNormal1 = originalVelocity1.dot(normal)
        velocityTangent1 = originalVelocity1.dot(tangent)
        velocityNormal2 = originalVelocity2.dot(normal)
        velocityTangent2 = originalVelocity2.dot(tangent)

        # 弹性碰撞公式
        newVelocityNormal1 = ((self.mass - ball.mass) * velocityNormal1 +
                              2 * ball.mass * velocityNormal2) / totalMass
        newVelocityNormal2 = (2 * self.mass * velocityNormal1 +
                              (ball.mass - self.mass) * velocityNormal2) / totalMass

        # 应用碰撞因子到法向分量
        collisionFactor = self.collisionFactor * ball.collisionFactor
        newVelocityNormal1 *= collisionFactor
        newVelocityNormal2 *= collisionFactor

        # 重建速度向量（保持原始方向）
        newVelocity1 = tangent * velocityTangent1 + normal * newVelocityNormal1
        newVelocity2 = tangent * velocityTangent2 + normal * newVelocityNormal2
        
        # 不再保持速度大小不变，让碰撞系数生效
        self.velocity = newVelocity1
        ball.velocity = newVelocity2

        # 位置修正
        overlap = minDistance - actualDistance

        if overlap > 0:
            # 无条件分离，防止穿透
            separation = normal * (overlap * 1.05)  # 增加分离系数

            # 按质量比例分配分离量
            self.position += separation * (ball.mass / totalMass)
            ball.position -= separation * (self.mass / totalMass)

            # 防止碰撞系数小于1时粘连
            min_sep_speed = 1.0  # 增大分离速度
            rel_vel = (self.velocity - ball.velocity).dot(normal)

            # 当相对速度不足以分离时，添加额外分离速度
            if rel_vel > -min_sep_speed:
                # 强制分离速度，碰撞系数越小，分离因子越大
                sepFactor = min(2.0, 2.0 - collisionFactor * 1.5)

                # 添加与重力方向相关的分离速度
                gravity_dir = Vector2(0, 1)  # 重力方向
                gravityComponent = normal.dot(gravity_dir)

                # 如果法线与重力方向有分量，增强该方向的分离
                if abs(gravityComponent) > 0.01:
                    # 根据重力方向调整分离力度
                    gravityBoost = 1.0 * gravityComponent * \
                        (2.0 - collisionFactor)

                    # 对上下方向的球体施加不同的分离力
                    if gravityComponent > 0:  # 下方球体需要更强的向上分离力
                        self.velocity += (
                            normal * (min_sep_speed * sepFactor +
                                      gravityBoost) * (ball.mass / totalMass)
                        )

                        ball.velocity -= (
                            normal * (min_sep_speed * sepFactor) *
                            (self.mass / totalMass)
                        )

                    else:  # 上方球体需要更强的向下分离力
                        self.velocity += (
                            normal * (min_sep_speed * sepFactor) *
                            (ball.mass / totalMass)
                        )

                        ball.velocity -= (
                            normal * (min_sep_speed * sepFactor +
                                      abs(gravityBoost)) * (self.mass / totalMass)
                        )
                else:
                    # 水平方向的普通分离
                    self.velocity += (
                        normal * min_sep_speed * sepFactor *
                        (ball.mass / totalMass)
                    )
                    ball.velocity -= (
                        normal * min_sep_speed * sepFactor *
                        (self.mass / totalMass)
                    )
        
        newElectricCharge = (self.electricCharge + ball.electricCharge) / 2
        self.electricCharge = newElectricCharge
        ball.electricCharge = newElectricCharge

        return self.velocity

    def gravitate(self, other: Self) -> Vector2:
        """处理球与球之间的引力"""

        minDistance = 1  # 防止距离过近导致力过大

        # 计算实际距离
        deltaPos = self.position - other.position
        distance = max(abs(deltaPos), minDistance)

        # 计算引力方向（保证单位向量稳定性）
        direction = deltaPos.normalize() if distance > 0 else ZERO

        # 完整万有引力公式（含距离缩放）
        forceMagnitude = gravityFactor * self.mass * \
            other.mass / (distance**2 + 1e-6)
        force = -direction * forceMagnitude  # 正确的吸引方向

        # 应用作用力时考虑质量分配
        self.force(force, isNatural=True)
        other.force(-force, isNatural=True)

        return force

    def electricForce(self, other: Self) -> Vector2:
        """计算球与球之间的电力"""
        minDistance = 1  # 防止距离过近导致力过大

        # 计算实际距离
        deltaPos = self.position - other.position
        distance = max(abs(deltaPos), minDistance)

        # 计算电力方向（保证单位向量稳定性）
        direction = deltaPos.normalize() if distance > 0 else ZERO

        # 完整电力公式（含距离缩放）
        forceMagnitude = electrostaticFactor * self.electricCharge * other.electricCharge / (
            distance**2 + 1e-6
        )
        force = direction * forceMagnitude  # 正确的吸引方向

        # 应用作用力时考虑质量分配
        self.force(force, isNatural=True)
        other.force(-force, isNatural=True)
        # print(self.acceleration.x, self.acceleration.y)

        return force

    def getCircularVelocity(self, ball: Self, factor: float = 1) -> Vector2:
        """计算两个球的环绕速度"""
        # 计算距离
        distance = self.position.distance(ball.position)

        if distance == 0:
            return ZERO

        # 计算速度方向
        direction = (ball.position - self.position).vertical().normalize()

        # 计算速度大小
        velocity = direction * (ball.mass / distance * 1e5) ** 0.5

        return velocity * factor + ball.velocity

    def merge(self, other: Self, game) -> Self:
        """处理球与球之间的天体合并"""

        totalPosition = (self.position * self.mass + other.position * other.mass) / (
            self.mass + other.mass
        )
        totalVelocity = (self.velocity * self.mass + other.velocity * other.mass) / (
            self.mass + other.mass
        )
        totalForce = self.artificialForces + other.artificialForces
        totalRadius = round((self.radius**2 + other.radius**2) ** 0.5, 1)
        totalMass = self.mass + other.mass
        totalColor = colorTupleToString(
            colorMiddle(self.color, other.color, self.radius / totalRadius)
        )

        newBall = Ball(
            totalPosition,
            totalRadius,
            totalColor,
            totalMass,
            totalVelocity,
            totalForce,
            gravitation=game.isCelestialBodyMode,
            electricCharge=self.electricCharge + other.electricCharge,
        )

        if self.isFollowing or other.isFollowing:
            newBall.isFollowing = True
            newBall.highLighted = True

        elif self.isShowingInfo or other.isShowingInfo:
            newBall.isShowingInfo = True

        newBall.displayedAcceleration = (
            self.displayedAcceleration + other.displayedAcceleration
        )

        newBall.displayedVelocity = self.displayedVelocity + other.displayedVelocity

        return newBall

    def getPosition(self) -> Vector2:
        """获取球的位置"""
        return self.position
