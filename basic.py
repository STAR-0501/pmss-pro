from random import random
from typing import Self
import copy
import pygame
import math

G = 5e+4  # 添加引力常数调节参数

def colorStringToTuple(color: str) -> tuple[int, int, int]:
    """颜色字符串转RGB元组"""

    # 如果是颜色名称格式，先转换为pygame颜色对象获取RGB值
    if not color.startswith('#'):

        try:
            color_ = pygame.Color(color.lower())
            return (color_.r, color_.g, color_.b)
        
        except ValueError:
            # 如果颜色名称无效，返回默认黑色
            return (0, 0, 0)

    # 处理十六进制字符串格式
    return tuple(int(color[i: i+2], 16) for i in (1, 3, 5))

def colorTupleToString(color : tuple[int, int, int]) -> str:
    """RGB元组转颜色字符串"""
    return '#%02x%02x%02x' % color

def colorMiddle(color1 : tuple[int, int, int] | str, color2 : tuple[int, int, int] | str, factor : float = 0.5) -> tuple[int, int, int]:
    """计算平均颜色"""

    if isinstance(color1, str):
        color1 = colorStringToTuple(color1)

    if isinstance(color2, str):
        color2 = colorStringToTuple(color2)

    return (int(color1[0] * factor + color2[0] * (1 - factor)), int(color1[1] * factor + color2[1] * (1 - factor)), int(color1[2] * factor + color2[2] * (1 - factor)))

def colorOpposite(color : tuple[int, int, int]) -> tuple[int, int, int]:
    """计算反转颜色"""
    return (255 - color[0], 255 - color[1], 255 - color[2])

def colorSuitable(color1 : tuple[int, int, int] | str, color2 : tuple[int, int, int] | str) -> tuple[int, int, int]:
    """计算合适颜色"""
    return colorOpposite(colorMiddle(color1, color2))

class Vector2:
    """二维向量类，提供基本向量运算和几何操作方法"""
    def __init__(self, x : float | tuple[float, float], y : float = None) -> None:
        
        if y is None:
            self.x, self.y = x

        else:
            self.x = x
            self.y = y

    def __add__(self, other : Self) -> Self:
        """向量加法"""
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other : Self) -> Self:
        """向量减法"""
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, number : float) -> Self:
        """向量数乘"""
        return Vector2(self.x * number, self.y * number)

    def __truediv__(self, number : float) -> Self:
        """向量数除"""
        return Vector2(self.x / number, self.y / number)

    def __neg__(self) -> Self:
        """向量取反"""
        return Vector2(-self.x, -self.y)

    def __abs__(self) -> float:
        """向量长度"""
        return (self.x**2 + self.y**2)**0.5

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

    def dot(self, other : Self) -> float:
        """向量点积运算"""
        return self.x * other.x + self.y * other.y

    def distance(self, other : Self) -> float:
        """计算两点间欧氏距离"""
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

    def copy(self) -> Self:
        """返回向量副本"""
        return Vector2(self.x, self.y)

    def project(self, other : Self) -> Self:
        """计算当前向量在另一向量上的投影"""
        dot = self.x * other.x + self.y * other.y
        length = other.x**2 + other.y**2

        if length != 0:
            scalar = dot / length
        else:
            scalar = 0

        return Vector2(other.x * scalar, other.y * scalar)

    def projectVertical(self, other : Self) -> Self:
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

def triangleArea(p1 : Vector2, p2 : Vector2, p3 : Vector2) -> float:
    """计算三角形面积"""
    return abs((p1.x*(p2.y-p3.y) + p2.x*(p3.y-p1.y) + p3.x*(p1.y-p2.y))/2)

class CollisionLine:
    """碰撞线段类，处理线段相交检测和显示"""
    def __init__(self, start : Vector2, end : Vector2, isLine : bool = False, collisionFactor : float = 1, display : bool = True) -> None:
        self.start = start
        self.end = end
        self.vector = end - start
        self.isLine = isLine
        self.collisionFactor = collisionFactor
        self.display = display

    def isLineIntersect(self, other: Self) -> bool:
        """使用叉积法判断线段相交"""
        def crossProduct(v1: Vector2, v2: Vector2) -> float:
            return v1.x * v2.y - v1.y * v2.x

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
            pygame.draw.line(game.screen, "black", (game.realToScreen(self.start.x, game.x), game.realToScreen(self.start.y, game.y)), (game.realToScreen(self.end.x, game.x), game.realToScreen(self.end.y, game.y)))

class Element:
    """游戏元素基类，定义通用接口"""
    def __init__(self, position : Vector2, color : pygame.Color) -> None:
        self.position = position
        self.highLighted = False
        self.type = "element"
        self.attrs = []

    def isMouseOn(self, game) -> bool:
        """检测鼠标是否在元素上"""
        pos = Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y))
        return self.isPosOn(game, pos)
    
    def isPosOn(self, game, pos) -> bool:
        """检测坐标点是否在元素上"""
        ...

    def update(self, deltaTime) -> Self:
        """更新方法"""
        ...
        return self

    def draw(self, game) -> None:
        """绘制方法"""
        ...

    def updateAttrsList(self) -> None:
        """更新属性列表"""
        ...

class Coordinator():
    """坐标系辅助类，处理坐标转换和角度显示"""
    def __init__(self, x : float, y : float, width : float, game) -> None:
        self.position = Vector2(x, y)
        self.width = width
        self.degree = 0
        self.minDegree = 0
        self.minDirection = ZERO
        self.direction = []
        self.update(game)

    def draw(self, game, option, text="") -> None:
        """绘制坐标系指示器和角度信息"""

        for direction in self.direction:
            pygame.draw.line(game.screen, "black", (game.realToScreen(self.position.x, game.x), game.realToScreen(self.position.y, game.y)), (game.realToScreen(self.position.x + direction.x, game.x), game.realToScreen(self.position.y + direction.y, game.y)))
        
        self.showDegree(game, Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y)), option, text)

    def update(self, game) -> Self:
        """更新坐标系方向向量"""

        self.direction = [
            Vector2(game.screenToReal(self.width), game.screenToReal(0)), 
            Vector2(game.screenToReal(0), game.screenToReal(-self.width)), 
            Vector2(game.screenToReal(-self.width), game.screenToReal(0)), 
            Vector2(game.screenToReal(0), game.screenToReal(self.width))
        ]

        return self

    def isMouseOn(self) -> bool:
        """检测鼠标是否在坐标系上"""
        return self.minDegree == 0

    def showDegree(self, game, pos: Vector2, option, text) -> None:
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
            delta = min(abs(distance - self.degree), 360 - abs(distance - self.degree))

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
            game.screen, "black", 
            (game.realToScreen((self.position.x - radius/2), game.x), 
            game.realToScreen((self.position.y - radius/2), game.y), 
            game.realToScreen(radius), 
            game.realToScreen(radius)), 
            startAngle, endAngle, 2
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
            textX = game.realToScreen(self.position.x + (nowDirection.x/3), game.x) - textSize[0]/3
            textY = game.realToScreen(self.position.y + (nowDirection.y/3), game.y) - textSize[1]/3
            game.screen.blit(game.fontSmall.render(degreeText, True, "black"), (textX, textY))

        if text!= "":
            textSize = game.fontSmall.size(text)
            textX = game.realToScreen(self.position.x + (nowDirection.x*2/3), game.x) - textSize[0]*2/3
            textY = game.realToScreen(self.position.y + (nowDirection.y*2/3), game.y) - textSize[1]*2/3
            game.screen.blit(game.fontSmall.render(text, True, "black"), (textX, textY))

class Ball(Element):
    """球体物理实体类，处理运动学计算和碰撞响应"""
    def __init__(self, position : Vector2, radius : float, color : pygame.Color, mass : float, velocity : Vector2, artificialForces : list[Vector2], gravity : float = 1, collisionFactor : float = 1, gravitation : bool = False) -> None:
        self.position = position
        self.radius = radius
        self.color = color
        self.mass = mass
        self.velocity = velocity
        self.displayedVelocity = ZERO
        self.displayedVelocityFactor = 0
        self.naturalForces = []
        self.artificialForces = artificialForces
        self.acceleration = ZERO
        self.displayedAcceleration = ZERO
        self.displayedAccelerationFactor = 0
        self.gravity = gravity
        self.highLighted = False
        self.collisionFactor = collisionFactor
        self.airResistance = 1
        self.gravitation = gravitation
        self.type = "ball"
        self.isFollowing = False
        self.isShowingInfo = False
        self.attrs = []
        self.updateAttrsList()

    def isPosOn(self, game, pos: Vector2) -> bool:  
        """检测坐标点是否在球体范围内"""
        return (pos.x - self.position.x)**2 + (pos.y - self.position.y)**2 <= self.radius**2

    def isCollidedByBall(self, other : Self) -> bool:
        """检测球与球之间的碰撞"""
        distance = self.position.distance(other.position)
        return distance <= self.radius + other.radius

    def setAttr(self, name, value) -> None:
        """设置属性值"""
        if value != "":

            if name == "color":
                self.color = value

            if name == "radius":
                self.radius = float(value)

            if name == "mass":
                self.mass = float(value)

    def copy(self, game) -> None:
        """自我复制"""
        self.isFollowing = False
        newBall = copy.deepcopy(self)
        isMoving = True
        game.elements["all"].append(newBall)
        game.elements["ball"].append(newBall)

        while isMoving:
            newBall.position = Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y))

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
        screenCenterX = - game.x + game.screen.get_width() / (2 * game.ratio)
        screenCenterY = - game.y + game.screen.get_height() / (2 *game.ratio)

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

    def force(self, force : Vector2, isNatural : bool = False) -> Vector2:
        """施加外力并更新加速度"""
        if isNatural:
            self.naturalForces.append(force)

        else:
            self.artificialForces.append(force)

        return self.accelerate()

    def resetForce(self, isNatural : bool = False) -> None:
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

            {
                "type": "mass", 
                "value": self.mass, 
                "min": 0.1, 
                "max": 32767
            }, 

            {
                "type": "radius", 
                "value": self.radius, 
                "min": 1, 
                "max": 1024
            }, 
            
            {
                "type": "color", 
                "value": self.color, 
                "min": "#000000", 
                "max": "#FFFFFF"
            }
        ]

    def update(self, deltaTime) -> Self:
        """更新物理状态"""
        self.accelerate()
        substeps = 10  # 从4增加到10
        deltaTime /= substeps

        for _ in range(substeps):
            self.velocity += self.acceleration * deltaTime
            self.position += (self.velocity + self.acceleration * deltaTime * 20**0.5) * deltaTime

        self.velocity *= self.airResistance ** deltaTime

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
                game.screen, (255, 255, 0), 
                (game.realToScreen(self.position.x, game.x), 
                game.realToScreen(self.position.y, game.y)), 
                game.realToScreen(self.radius + 0.5), 0
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
                game.realToScreen(self.position.y, game.y)
            )

            drawRadius = game.realToScreen(currentRadius)

            # 创建临时surface实现透明度
            tempSurface = pygame.Surface((drawRadius*2, drawRadius*2), pygame.SRCALPHA)

            pygame.draw.circle(
                tempSurface, (red, green, blue, alpha), 
                (drawRadius, drawRadius), drawRadius, 0
            )
            
            game.screen.blit(tempSurface, (pos[0]-drawRadius, pos[1]-drawRadius))

        self.highLighted = False

    def reboundByWall(self, wall: Self) -> Vector2:
        """处理与墙体的碰撞反弹"""
        direction = self.position - wall.position
        self.position += direction * 0.1
        self.velocity = self.velocity * 0
        return self.velocity

    def reboundByLine(self, line: CollisionLine, timeIsReversed : bool = False) -> Vector2:
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
        
        self.displayedVelocity = self.velocity + (self.displayedVelocity - self.velocity) * self.displayedVelocityFactor
        self.displayedVelocityFactor = 1

        AP = self.position - line.start
        projectionRatio = AP.dot(AB) / lineLength

        # 计算最近点和法线
        if line.isLine:  # 直线的情况
            closest = line.start + AB * projectionRatio
            edgeNormal = Vector2(-AB.y, AB.x).normalize()
            # 根据球的位置确定法线方向
            normal = edgeNormal if (self.position - closest).dot(edgeNormal) > 0 else -edgeNormal

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
                normal = edgeNormal if (self.position - closest).dot(edgeNormal) > 0 else -edgeNormal

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
            self.velocity += normal * (velocityNormalAfterRebound * ((self.collisionFactor * line.collisionFactor if not timeIsReversed else 1/self.collisionFactor/line.collisionFactor) - 1))

            # 调整速度大小
            self.velocity = self.velocity.copy().normalize() * abs(abs(self.velocity) ** 2 - 2 * 98.1 * (1 - cosine ** 2) ** 0.5 * overlap) ** 0.5

        return self.velocity

    def reboundByBall(self, ball: Self) -> Vector2:
        """处理球与球之间的碰撞响应"""
        # 获取总质量
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

        self.displayedVelocity = self.velocity + (self.displayedVelocity - self.velocity) * self.displayedVelocityFactor
        self.displayedVelocityFactor = 1

        ball.displayedVelocity = ball.velocity + (ball.displayedVelocity - ball.velocity) * ball.displayedVelocityFactor
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
        newVelocityNormal1 = ((self.mass - ball.mass)*velocityNormal1 + 2*ball.mass*velocityNormal2) / totalMass
        newVelocityNormal2 = (2*self.mass*velocityNormal1 + (ball.mass - self.mass)*velocityNormal2) / totalMass

        # 应用碰撞因子到法向分量
        collisionFactor = self.collisionFactor * ball.collisionFactor
        newVelocityNormal1 *= collisionFactor
        newVelocityNormal2 *= collisionFactor

        # 重建速度矢量（保持原始方向）
        self.velocity = tangent * velocityTangent1 + normal * newVelocityNormal1
        ball.velocity = tangent * velocityTangent2 + normal * newVelocityNormal2

        # 位置修正 !!! 这里的位置修正有问题，需要修正
        overlap = (minDistance - actualDistance)
        if overlap > 0:
            relativeVelocity = (originalVelocity1 - originalVelocity2).dot(normal)
            if relativeVelocity < 0:
                collisionFactor = self.collisionFactor * ball.collisionFactor
                
                # 优化后的分离量计算
                if collisionFactor > 1e-8:
                    # 保持原有基于碰撞因子的修正
                    separation = normal * (overlap * (1.001 / collisionFactor))
                else:
                    # 当碰撞系数为0时，仅分离实际重叠部分
                    separation = normal * overlap * 1.001  # 小幅过调防止持续穿透
                    
                # 保持质量分配比例
                self.position += separation * (ball.mass / totalMass)
                ball.position -= separation * (self.mass / totalMass)

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
        forceMagnitude = G * self.mass * other.mass / (distance ** 2 + 1e-6)
        force = -direction * forceMagnitude  # 正确的吸引方向

        # 应用作用力时考虑质量分配
        self.force(force, isNatural=True)
        other.force(-force, isNatural=True)
        
        return force

    def getCircularVelocity(self, ball : Self, factor : float = 1) -> Vector2:
        """计算两个球的环绕速度"""
        # 计算距离
        distance = self.position.distance(ball.position)

        if distance == 0:
            return ZERO
        
        # 计算速度方向
        direction = (ball.position - self.position).vertical().normalize()

        # 计算速度大小
        velocity = direction * (ball.mass / distance * 1e+5) ** 0.5

        return velocity * factor + ball.velocity

    def merge(self, other: Self, game) -> Self:
        """处理球与球之间的天体合并"""

        totalPosition = (self.position * self.mass + other.position * other.mass) / (self.mass + other.mass)
        totalVelocity = (self.velocity * self.mass + other.velocity * other.mass) / (self.mass + other.mass)
        totalForce = self.artificialForces + other.artificialForces
        totalRadius = round((self.radius ** 2 + other.radius ** 2) ** 0.5, 1)
        totalMass = self.mass + other.mass
        totalColor = colorTupleToString(colorMiddle(self.color, other.color, self.radius / totalRadius))

        newBall = Ball(totalPosition, totalRadius, totalColor, totalMass, totalVelocity, totalForce, gravitation=game.isCelestialBodyMode)

        if self.isFollowing or other.isFollowing:
            newBall.isFollowing = True
            newBall.highLighted = True

        elif self.isShowingInfo or other.isShowingInfo:
            newBall.isShowingInfo = True
        
        newBall.displayedAcceleration = self.displayedAcceleration + other.displayedAcceleration
        newBall.displayedVelocity = self.displayedVelocity + other.displayedVelocity

        return newBall

    def getPosition(self) -> Vector2:
        """获取球的位置"""
        return self.position

class Wall(Element):
    """墙体类，处理多边形碰撞和显示"""
    def __init__(self, vertexes: list[Vector2], color : pygame.Color, isLine : bool = False) -> None:
        self.vertexes = vertexes
        self.color = color
        self.isLine = isLine

        self.position = Vector2(
            (vertexes[0].x + vertexes[1].x + vertexes[2].x + vertexes[3].x) / 4, 
            (vertexes[0].y + vertexes[1].y + vertexes[2].y + vertexes[3].y) / 4
        )
        
        self.originalPosition = self.position.copy()
        
        self.lines = [
            CollisionLine(vertexes[0], vertexes[1], isLine), CollisionLine(vertexes[1], vertexes[2], isLine), 
            CollisionLine(vertexes[2], vertexes[3], isLine), CollisionLine(vertexes[3], vertexes[0], isLine)
        ]
        
        self.highLighted = False
        self.type = "wall"

        self.attrs = []
        self.updateAttrsList()

    def setAttr(self, name, value) -> None:
        """设置属性值"""
        if value != "":
            if name == "color":
                self.color = value

    def copy(self, game) -> None:
        """自我复制"""
        newWall = copy.deepcopy(self)
        game.elements["all"].append(newWall)
        game.elements["wall"].append(newWall)
        isMoving = True 

        while isMoving:
            newWall.position = Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y))
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
            {
                "type": "color", 
                "value": self.color, 
                "min": "#000000", 
                "max": "#FFFFFF"
            }
        ]

    def update(self, deltaTime) -> Self:
        """更新墙体位置并维护碰撞线段"""
        # 计算位置
        offset = self.position - self.originalPosition
        for i in range(len(self.vertexes)):
            self.vertexes[i] += offset

        self.lines = [
            CollisionLine(self.vertexes[0], self.vertexes[1], self.isLine), CollisionLine(self.vertexes[1], self.vertexes[2]), 
            CollisionLine(self.vertexes[2], self.vertexes[3]), CollisionLine(self.vertexes[3], self.vertexes[0])
        ]
        
        self.originalPosition = self.position.copy()
        self.updateAttrsList()

        return self

    def checkVertexCollision(self, ball) -> None:
        """检测球与墙体顶点的碰撞"""
        for vertex in self.vertexes:
            if ball.position.distance(vertex) <= ball.radius:
                # 计算从顶点到球心的方向作为法线
                normal = (ball.position - vertex).normalize()
                self.handleVertexCollision(ball, vertex, normal)

    def handleVertexCollision(self, ball, vertex, normal) -> None:
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
        ray = CollisionLine(Vector2(mx, my), Vector2(mx + 10000, my))  # 假设射线足够长
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
                direction = (vertex - center)

                # 归一化后扩展
                if abs(direction) > 0:
                    direction.normalize()
                    
                    # 保持原始顶点顺序，沿方向向外扩展
                    highLightList.append(vertex + direction * expand)
                else:
                    highLightList.append(vertex.copy())

            pygame.draw.polygon(game.screen, (255, 255, 0), [(game.realToScreen(hightLight.x, game.x), game.realToScreen(hightLight.y, game.y)) for hightLight in highLightList], 0)

        pygame.draw.polygon(game.screen, self.color, [(game.realToScreen(vertex.x, game.x), game.realToScreen(vertex.y, game.y)) for vertex in self.vertexes], 0)
        self.highLighted = False

class WallPosition:
    """墙体位置类，储存墙体上某一点的相对位置"""
    def __init__(self, wall: Wall, position: Vector2) -> None:
        self.wall = wall
        self.position = position

    def getPosition(self) -> Vector2:
        """获取墙体位置"""
        return self.position + self.wall.position

class Rope:
    """绳索类，处理绳索的显示和物理效果"""
    def __init__(self, start: Ball | WallPosition, end: Ball | WallPosition, length: float, width: float, color) -> bool:
        self.start = start
        self.end = end
        self.length = length
        self.width = width
        self.color = color

        if isinstance(start, WallPosition) and isinstance(end, WallPosition):
            return False
        
        return True

    def isReachingLimit(self) -> bool:
        """判断绳索是否到达极限长度"""
        return self.length < abs(self.start.getPosition() - self.end.getPosition())
    
    def pullBall(self) -> bool:
        """处理球与绳索的影响"""
        distance = self.start.getPosition().distance(self.end.getPosition())
        overlap = distance - self.length

        # 位置修正
        if overlap > 0:

            if isinstance(self.start, Ball):
                ...

            elif isinstance(self.end, Ball):
                ...

    def update(self, deltaTime) -> Self:
        """更新绳索位置"""
        if isinstance(self.start, Ball) and isinstance(self.end, Ball):
            ...

        elif isinstance(self.start, WallPosition) and isinstance(self.end, Ball):
            ...

        elif isinstance(self.start, Ball) and isinstance(self.end, WallPosition):
            ...

        else:
            ...
        
        return self

    def draw(self, game) -> None:
        """绘制绳索"""
        pygame.draw.line(game.screen, self.color, (game.realToScreen(self.start.getPosition().x, game.x), game.realToScreen(self.start.getPosition().y, game.y)), (game.realToScreen(self.end.getPosition().x, game.x), game.realToScreen(self.end.getPosition().y, game.y)), self.width)
