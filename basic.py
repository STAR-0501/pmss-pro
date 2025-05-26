from random import random
from typing import Self
import copy
import pygame
import math

G = 5e4  # 添加引力常数调节参数


def colorStringToTuple(color: str) -> tuple[int, int, int]:
    """颜色字符串转RGB元组"""

    # 如果是颜色名称格式，先转换为pygame颜色对象获取RGB值
    if not color.startswith("#"):

        try:
            color_ = pygame.Color(color.lower())
            return (color_.r, color_.g, color_.b)

        except ValueError:
            # 如果颜色名称无效，返回默认黑色
            return (0, 0, 0)

    # 处理十六进制字符串格式
    return tuple(int(color[i: i + 2], 16) for i in (1, 3, 5))


def colorTupleToString(color: tuple[int, int, int]) -> str:
    """RGB元组转颜色字符串"""
    return "#%02x%02x%02x" % color


def colorMiddle(
    color1: tuple[int, int, int] | str,
    color2: tuple[int, int, int] | str,
    factor: float = 0.5,
) -> tuple[int, int, int]:
    """计算平均颜色"""

    if isinstance(color1, str):
        color1 = colorStringToTuple(color1)

    if isinstance(color2, str):
        color2 = colorStringToTuple(color2)

    return (
        int(color1[0] * factor + color2[0] * (1 - factor)),
        int(color1[1] * factor + color2[1] * (1 - factor)),
        int(color1[2] * factor + color2[2] * (1 - factor)),
    )


def colorOpposite(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """计算反转颜色"""
    return (255 - color[0], 255 - color[1], 255 - color[2])


def colorSuitable(
    color1: tuple[int, int, int] | str, color2: tuple[int, int, int] | str
) -> tuple[int, int, int]:
    """计算合适颜色"""
    return colorOpposite(colorMiddle(color1, color2))


class Vector2:
    """二维向量类，提供基本向量运算和几何操作方法"""

    def __init__(self, x: float | tuple[float, float], y: float = None) -> None:

        if y is None:
            self.x: float = x[0]
            self.y: float = x[1]

        else:
            self.x: float = x
            self.y: float = y

    def __add__(self, other: Self) -> Self:
        """向量加法"""
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Self) -> Self:
        """向量减法"""
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, number: float) -> Self:
        """向量数乘"""
        return Vector2(self.x * number, self.y * number)

    def __truediv__(self, number: float) -> Self:
        """向量数除"""
        return Vector2(self.x / number, self.y / number)

    def __neg__(self) -> Self:
        """向量取反"""
        return Vector2(-self.x, -self.y)

    def __abs__(self) -> float:
        """向量长度"""
        return (self.x**2 + self.y**2) ** 0.5

    def magnitude(self) -> float:
        """返回向量长度"""
        return abs(self)

    def zero(self) -> Self:
        """将向量置零"""
        self.x = 0
        self.y = 0
        return self

    def normalize(self) -> Self:
        """向量单位化"""
        length = abs(self)

        if length != 0:
            self.x /= length
            self.y /= length

        return self

    def dot(self, other: Self) -> float:
        """向量点积运算"""
        return self.x * other.x + self.y * other.y

    def distance(self, other: Self) -> float:
        """计算两点间欧氏距离"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def copy(self) -> Self:
        """返回向量副本"""
        return Vector2(self.x, self.y)

    def project(self, other: Self) -> Self:
        """计算当前向量在另一向量上的投影"""
        dot = self.x * other.x + self.y * other.y
        length = other.x**2 + other.y**2

        if length != 0:
            scalar = dot / length
        else:
            scalar = 0

        return Vector2(other.x * scalar, other.y * scalar)

    def projectVertical(self, other: Self) -> Self:
        """计算当前向量在垂直方向上的投影"""
        dot = self.x * other.x + self.y * other.y
        length = other.x**2 + other.y**2

        if length != 0:
            scalar = dot / length
        else:
            scalar = 0

        return Vector2(self.x - other.x * scalar, self.y - other.y * scalar)

    def vertical(self) -> Self:
        """返回当前向量的垂直向量"""
        return Vector2(-self.y, self.x)

    def toTuple(self) -> tuple[float, float]:
        """转换为元组形式"""
        return (self.x, self.y)


ZERO = Vector2(0, 0)


def triangleArea(p1: Vector2, p2: Vector2, p3: Vector2) -> float:
    """计算三角形面积"""
    return abs((p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y)) / 2)


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


class Element:
    """游戏元素基类，定义通用接口"""

    def __init__(self, position: Vector2, color: pygame.Color) -> None:
        self.position: Vector2 = position
        self.color: pygame.Color = color
        self.highLighted: bool = False
        self.type: str = "element"
        self.attrs: list[dict] = []

    def setAttr(self, key: str, value: str):
        """设置属性"""
        ...

    def isMouseOn(self, game) -> bool:
        """检测鼠标是否在元素上"""
        pos = Vector2(
            game.screenToReal(pygame.mouse.get_pos()[0], game.x),
            game.screenToReal(pygame.mouse.get_pos()[1], game.y),
        )
        return self.isPosOn(game, pos)

    def isPosOn(self, game, pos: Vector2) -> bool:
        """检测坐标点是否在元素上"""
        ...

    def update(self, deltaTime: float) -> Self:
        """更新方法"""
        ...
        return self

    def draw(self, game) -> None:
        """绘制方法"""
        ...

    def updateAttrsList(self) -> None:
        """更新属性列表"""
        ...


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

        self.acceleration += Vector2(0, 98.1 * self.gravity)
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
        return self

    def draw(self, game) -> None:
        """绘制带渐变效果的小球"""
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
        self.velocity = self.velocity * 0
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

            # 调整速度大小
            self.velocity = (
                self.velocity.copy().normalize() * abs(
                    abs(self.velocity) ** 2 - 2 * 98.1 *
                    (1 - cosine**2) ** 0.5 * overlap
                ) ** 0.5
            )

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
        self.velocity = tangent * velocityTangent1 + normal * newVelocityNormal1
        ball.velocity = tangent * velocityTangent2 + normal * newVelocityNormal2

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
        forceMagnitude = G * self.mass * other.mass / (distance**2 + 1e-6)
        force = -direction * forceMagnitude  # 正确的吸引方向

        # 应用作用力时考虑质量分配
        self.force(force, isNatural=True)
        other.force(-force, isNatural=True)

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


class Wall(Element):
    """墙体类，处理多边形碰撞和显示"""

    def __init__(
        self, vertexes: list[Vector2], color: pygame.Color, isLine: bool = False
    ) -> None:
        self.vertexes: list[Vector2] = vertexes
        self.color: pygame.Color = color
        self.isLine: bool = isLine

        self.position: Vector2 = Vector2(
            (vertexes[0].x + vertexes[1].x +
             vertexes[2].x + vertexes[3].x) / 4,
            (vertexes[0].y + vertexes[1].y +
             vertexes[2].y + vertexes[3].y) / 4,
        )

        self.originalPosition: Vector2 = self.position.copy()

        self.lines: list[CollisionLine] = [
            CollisionLine(vertexes[0], vertexes[1], isLine),
            CollisionLine(vertexes[1], vertexes[2], isLine),
            CollisionLine(vertexes[2], vertexes[3], isLine),
            CollisionLine(vertexes[3], vertexes[0], isLine),
        ]

        self.highLighted: bool = False
        self.type: str = "wall"

        self.attrs: list[dict] = []
        self.updateAttrsList()

    def setAttr(self, key: str, value: str) -> None:
        """设置属性值"""
        if value != "":
            if key == "color":
                self.color = value

    def copy(self, game) -> None:
        """自我复制"""
        newWall = copy.deepcopy(self)
        game.elements["all"].append(newWall)
        game.elements["wall"].append(newWall)
        isMoving = True

        while isMoving:

            newWall.position = Vector2(
                game.screenToReal(pygame.mouse.get_pos()[0], game.x),
                game.screenToReal(pygame.mouse.get_pos()[1], game.y),
            )

            newWall.draw(game)
            newWall.update(0.5)
            game.update()
            pygame.display.update()

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    game.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        isMoving = False

    def getPosToPoint(self, point: Vector2) -> Vector2:
        """获取墙体到点的方向向量"""
        return self.position - point

    def updateAttrsList(self) -> None:
        """更新属性列表"""
        self.attrs = [
            {"type": "color", "value": self.color,
                "min": "#000000", "max": "#FFFFFF"}
        ]

    def update(self, deltaTime: float) -> Self:
        """更新墙体位置并维护碰撞线段"""
        # 计算位置
        offset = self.position - self.originalPosition
        for i in range(len(self.vertexes)):
            self.vertexes[i] += offset

        self.lines = [
            CollisionLine(self.vertexes[0], self.vertexes[1], self.isLine),
            CollisionLine(self.vertexes[1], self.vertexes[2]),
            CollisionLine(self.vertexes[2], self.vertexes[3]),
            CollisionLine(self.vertexes[3], self.vertexes[0]),
        ]

        self.originalPosition = self.position.copy()
        self.updateAttrsList()

        return self

    def checkVertexCollision(self, ball: Ball) -> None:
        """检测球与墙体顶点的碰撞"""
        for vertex in self.vertexes:
            if ball.position.distance(vertex) <= ball.radius:
                # 计算从顶点到球心的方向作为法线
                normal = (ball.position - vertex).normalize()
                self.handleVertexCollision(ball, vertex, normal)

    def handleVertexCollision(
        self, ball: Ball, vertex: Vector2, normal: Vector2
    ) -> None:
        """处理顶点碰撞的响应"""
        # 计算穿透深度
        penetration = ball.radius - ball.position.distance(vertex)

        if penetration > 0:
            # 位置修正
            ball.position += normal * penetration * 1.1
            # 速度反射（使用顶点法线）
            velocityNormal = ball.velocity.dot(normal)
            ball.velocity -= normal * (2 * velocityNormal)

    def isPosOn(self, game, pos: Vector2) -> bool:
        """使用射线法判断点是否在多边形内部"""
        mx = pos.x
        my = pos.y

        # 射线法检测点是否在多边形内
        # 创建一条从点开始的水平射线
        ray = CollisionLine(Vector2(mx, my), Vector2(
            mx + 10000, my))  # 假设射线足够长
        intersections = 0

        for line in self.lines:
            if line.isLineIntersect(ray):
                intersections += 1

        # 如果射线与多边形的边相交的次数是奇数，则点在多边形内
        return intersections % 2 == 1

    def draw(self, game) -> None:
        """绘制带高亮效果的墙体"""
        if self.highLighted:

            # 计算中心点
            center = self.position

            # 计算扩展比例
            expand = 1  # 向外扩展

            highLightList = []

            for vertex in self.vertexes:

                # 获取中心到顶点的方向向量
                direction = vertex - center

                # 归一化后扩展
                if abs(direction) > 0:
                    direction.normalize()

                    # 保持原始顶点顺序，沿方向向外扩展
                    highLightList.append(vertex + direction * expand)
                else:
                    highLightList.append(vertex.copy())

            pygame.draw.polygon(
                game.screen,
                (255, 255, 0),
                [
                    (
                        game.realToScreen(hightLight.x, game.x),
                        game.realToScreen(hightLight.y, game.y),
                    )
                    for hightLight in highLightList
                ],
                0,
            )

        pygame.draw.polygon(
            game.screen,
            self.color,
            [
                (
                    game.realToScreen(vertex.x, game.x),
                    game.realToScreen(vertex.y, game.y),
                )
                for vertex in self.vertexes
            ],
            0,
        )
        self.highLighted = False


class WallPosition:
    """墙体位置类，储存墙体上某一点的相对位置"""

    def __init__(self, wall: Wall, position: Vector2) -> None:
        self.wall: Wall = wall
        self.position: Vector2 = position

        self.deltaPosition = self.position - wall.position

        self.x = wall.position.x + position.x
        self.y = wall.position.y + position.y

    def getPosition(self) -> Vector2:
        """获取墙体位置"""
        return self.deltaPosition + self.wall.position

    def update(self) -> None:
        """更新位置"""
        self.x = self.wall.position.x + self.deltaPosition.x
        self.y = self.wall.position.y + self.deltaPosition.y
        self.position = self.getPosition()


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
