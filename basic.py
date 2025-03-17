from random import random
from typing import Self
import copy
import pygame
import math

# 颜色字符串转RGB元组
def colorStringToTuple(color: str) -> tuple[int, int, int]:
    # 如果是颜色名称格式，先转换为pygame颜色对象获取RGB值
    if not color.startswith('#'):
        try:
            c = pygame.Color(color.lower())
            return (c.r, c.g, c.b)
        except ValueError:
            # 如果颜色名称无效，返回默认黑色
            return (0, 0, 0)
    
    # 处理十六进制字符串格式
    return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

# RGB元组转颜色字符串
def colorTupleToString(color : tuple[int, int, int]) -> str:
    return '#%02x%02x%02x' % color

# 计算平均颜色
def colorMiddle(color1 : tuple[int, int, int], color2 : tuple[int, int, int], factor : float = 0.5) -> tuple[int, int, int]:
    if isinstance(color1, str):
        color1 = colorStringToTuple(color1)
    if isinstance(color2, str):
        color2 = colorStringToTuple(color2)
    return (int(color1[0] * factor + color2[0] * (1 - factor)), int(color1[1] * factor + color2[1] * (1 - factor)), int(color1[2] * factor + color2[2] * (1 - factor)))

# 计算反转颜色
def colorOpposite(color : tuple[int, int, int]) -> tuple[int, int, int]:
    return (255 - color[0], 255 - color[1], 255 - color[2])

# 计算合适颜色
def colorSuitable(color1 : tuple[int, int, int] | str, color2 : tuple[int, int, int] | str) -> tuple[int, int, int]:
    return colorOpposite(colorMiddle(color1, color2))

class Vector2:
    """二维向量类，提供基本向量运算和几何操作方法"""
    def __init__(self, x : float | tuple[float, float], y : float = None) -> None:
        if y is None:
            self.x, self.y = x
        else:
            self.x = x
            self.y = y

    def __add__(self, other : Self):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other : Self):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, number : float):
        return Vector2(self.x * number, self.y * number)

    def __truediv__(self, number : float):
        return Vector2(self.x / number, self.y / number)
    
    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __abs__(self) -> float:
        return (self.x**2 + self.y**2)**0.5

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

    #计算向量a在向量b上的投影
    def project(self, other : Self) -> Self:
        """计算当前向量在另一向量上的投影"""
        dot = self.x * other.x + self.y * other.y
        length = other.x**2 + other.y**2
        if length != 0: scalar = dot / length
        else: scalar = 0
        return Vector2(other.x * scalar, other.y * scalar)

    #计算向量a在垂直于向量b的向量上的投影
    def projectVertical(self, other : Self) -> Self:
        """计算当前向量在垂直方向上的投影"""
        dot = self.x * other.x + self.y * other.y
        length = other.x**2 + other.y**2
        if length != 0: scalar = dot / length
        else: scalar = 0
        return Vector2(self.x - other.x * scalar, self.y - other.y * scalar)

    #计算垂线
    def vertical(self) -> Self:
        """返回当前向量的垂直向量"""
        return Vector2(-self.y, self.x)

    def toTuple(self) -> tuple[float, float]:
        """转换为元组形式"""
        return (self.x, self.y)

def triangleArea(p1 : Vector2, p2 : Vector2, p3 : Vector2) -> float:
    """计算三角形面积"""
    return abs((p1.x*(p2.y-p3.y) + p2.x*(p3.y-p1.y) + p3.x*(p1.y-p2.y))/2)

class CollisionLine:
    """碰撞线段类，处理线段相交检测和显示"""
    def __init__(self, start : Vector2, end : Vector2, isLine : bool = False, collisionFactor : float = 1, display : bool = True):
        self.start = start
        self.end = end
        self.vector = end - start
        self.isLine = isLine
        self.collisionFactor = collisionFactor
        self.display = display
    
    def isLineIntersect(self, other: Self) -> bool:
        """使用叉积法判断线段相交"""
        def cross_product(v1: Vector2, v2: Vector2) -> float:
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
        AC_cross_AB = cross_product(AC, self.vector)
        AD_cross_AB = cross_product(AD, self.vector)
        BC_cross_CD = cross_product(BC, other.vector)
        BD_cross_CD = cross_product(BD, other.vector)

        # 判断线段是否相交
        return (AC_cross_AB * AD_cross_AB < 0) and (BC_cross_CD * BD_cross_CD < 0)

    def draw(self, game) -> None:
        """绘制线段到游戏窗口"""
        if self.display:
            pygame.draw.line(game.screen, "black", (game.realToScreen(self.start.x, game.x), game.realToScreen(self.start.y, game.y)), (game.realToScreen(self.end.x, game.x), game.realToScreen(self.end.y, game.y)))

class Element:
    """游戏元素基类，定义通用接口"""
    def __init__(self, position : Vector2, velocity : Vector2, mass : float, color : str) -> None:
        self.position = position
        self.highLighted = False
        self.type = "element"
        self.attrs = []
    def isMouseOn(self, game):
        """检测鼠标是否在元素上"""
        pos = Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y))
        return self.isPosOn(game, pos)
    def isPosOn(self, game, pos):
        ...
    def update(self, dt):
        ...
    def draw(self, game):
        ...
    
class Coordinator():
    """坐标系辅助类，处理坐标转换和角度显示"""
    def __init__(self, x : float, y : float, w : float, game) -> None:
        self.position = Vector2(x, y)
        self.w = w
        self.degree = 0
        self.minDegree = 0
        self.minDirection = Vector2(0, 0)
        self.direction = []
        self.update(game)

    def draw(self, game, option, text="") -> None:
        """绘制坐标系指示器和角度信息"""
        for direction in self.direction:
            pygame.draw.line(game.screen, "black", (game.realToScreen(self.position.x, game.x), game.realToScreen(self.position.y, game.y)), (game.realToScreen(self.position.x + direction.x, game.x), game.realToScreen(self.position.y + direction.y, game.y)))
        self.showDegree(game, Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y)), option, text)

    def update(self, game):
        """更新坐标系方向向量"""
        self.direction = [
            Vector2(game.screenToReal(self.w), game.screenToReal(0)), 
            Vector2(game.screenToReal(0), game.screenToReal(-self.w)), 
            Vector2(game.screenToReal(-self.w), game.screenToReal(0)), 
            Vector2(game.screenToReal(0), game.screenToReal(self.w))
        ]

    def isMouseOn(self) -> bool:
        return self.minDegree == 0

    def showDegree(self, game, pos: Vector2, option, text) -> None:
        """显示当前鼠标位置的角度信息"""
        minDirectionDegree = 0
        index = -1
        nowDirection = pos - self.position
        # 使用 atan2 计算角度，范围 [-180°, 180°]
        self.degree = math.degrees(math.atan2(nowDirection.y, nowDirection.x))
        # 转换为 [0°, 360°]，并调整 y 轴向下时的角度
        self.degree = (360 - self.degree) % 360  # 反转角度以适应 y 轴向下
        self.minDegree = 360
        for direction in self.direction:
            d = (self.direction.index(direction) * 90) % 360
            # 计算最小差值，考虑角度的周期性
            delta = min(abs(d - self.degree), 360 - abs(d - self.degree))
            if delta < self.minDegree:
                minDirectionDegree = d
                self.minDegree = delta
                self.minDirection = direction

        
        if game.realToScreen(abs(nowDirection)) >= self.w:
            radius = game.screenToReal(self.w)
        else:
            radius = abs(nowDirection)

        if self.degree > minDirectionDegree: 
            start_angle = math.radians(minDirectionDegree)
            end_angle = math.radians(self.degree)
        elif self.degree <= minDirectionDegree:
            start_angle = math.radians(self.degree)
            end_angle = math.radians(minDirectionDegree)
        if minDirectionDegree == 0 and self.degree > 270:
            start_angle = math.radians(self.degree)
            end_angle = math.radians(minDirectionDegree)
            # 绘制角度信息
        pygame.draw.arc(game.screen, "black", 
                        (game.realToScreen((self.position.x - radius/2), game.x), 
                         game.realToScreen((self.position.y - radius/2), game.y), 
                         game.realToScreen(radius), 
                         game.realToScreen(radius)), 
                        start_angle, end_angle, 2)
        
        if self.minDegree <= 1.5 and self.minDegree != 0 and self.w > 10:
            self.minDegree = 0
            # 计算单位方向向量
            minDirectionUnit = self.minDirection.normalize()
            # 保持 nowDirection 的长度，但方向与 minDirection 一致
            n = self.position + minDirectionUnit * abs(nowDirection)
            option.creationPoints[1] = n
            option.isAbsorption = True
        else:
            option.isAbsorption = False
         
        if not self.isMouseOn():
            degreeText = str(round(self.minDegree)) + "°"
            textSize = game.font.size(degreeText)   
            textX = game.realToScreen(self.position.x + (nowDirection.x/3), game.x) - textSize[0]/3
            textY = game.realToScreen(self.position.y + (nowDirection.y/3), game.y) - textSize[1]/3
            game.screen.blit(game.font.render(degreeText, True, "black"), (textX, textY))

        if text!= "":
            textSize = game.font.size(text)
            textX = game.realToScreen(self.position.x + (nowDirection.x*2/3), game.x) - textSize[0]*2/3
            textY = game.realToScreen(self.position.y + (nowDirection.y*2/3), game.y) - textSize[1]*2/3
            game.screen.blit(game.font.render(text, True, "black"), (textX, textY)) 

class Ball(Element):
    """小球物理实体类，处理运动学计算和碰撞响应"""
    def __init__(self, position : Vector2, radius, color, mass, velocity : Vector2, artificialForces : list[Vector2], gravity : float = 1, collisionFactor : float = 1, gravitation : bool = False) -> None:
        self.position = position
        self.radius = radius
        self.color = color
        self.mass = mass
        self.velocity = velocity
        self.naturalForces = []
        self.artificialForces = artificialForces
        self.acceleration = Vector2(0, 0)
        self.gravity = gravity
        self.highLighted = False
        self.collisionFactor = collisionFactor
        self.airResistance = 1
        self.gravitation = gravitation
        self.type = "ball"
        self.isFollowing = False
        self.attrs = [
            {
                "type": "mass",
                "value": self.mass,
                "min": 0.1,
                "max": 128
            },
            {
                "type": "radius",
                "value": self.radius,
                "min": 1,
                "max": 128
            },
            {
                "type": "color",
                "value": self.color,
                "min": "#000000",
                "max": "#FFFFFF"
            }
        ]

    def isPosOn(self, game, pos: Vector2):  
        """检测坐标点是否在球体范围内"""
        return (pos.x - self.position.x)**2 + (pos.y - self.position.y)**2 <= self.radius**2

    def isCollidedByBall(self, other : Self) -> bool:
        """检测球与球之间的碰撞"""
        distance = self.position.distance(other.position)
        return distance <= self.radius + other.radius

    def setAttr(self, name, value):
        if value != "":
            if name == "color":
                self.color = value
            if name == "radius":
                self.radius = float(value)
            if name == "mass":
                self.mass = float(value)

    def copy(self, game):
        
        self.isFollowing = False
        newBall = copy.deepcopy(self)
        isMoving = True
        game.elements["all"].append(newBall)
        game.elements["ball"].append(newBall)
        while isMoving:
            newBall.position = Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y))
            
            newBall.velocity = Vector2(0, 0)
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

    def follow(self, game):
        # 计算屏幕中心在游戏世界坐标系中的位置
        screen_center_x = - game.x + game.screen.get_width() / (2 * game.ratio)
        screen_center_y = - game.y + game.screen.get_height() / (2 *game.ratio)
        
        # 计算 self.position 与屏幕中心的偏移量
        offset_x = self.position.x - screen_center_x
        offset_y = self.position.y - screen_center_y
        
        # 更新屏幕在游戏世界坐标系中的位置
        game.x -= offset_x
        game.y -= offset_y
        

    def isCollidedByLine(self, line: CollisionLine) -> bool:
        """检测球与线段的碰撞"""
        # 检查线段的起点和终点是否重合
        if line.start.distance(line.end) < 1e-5:
            return False

        AB = line.end - line.start
        AP = self.position - line.start
        t = AP.dot(AB) / AB.dot(AB)

        if line.isLine:  # 直线无限延长
            closest_point = line.start + AB * t
        else:  # 普通线段
            t_clamped = max(0, min(t, 1))
            closest_point = line.start + AB * t_clamped

        distance = self.position.distance(closest_point)
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
        if isNatural:
            self.naturalForces.clear()
        else:
            self.artificialForces.clear()
        self.acceleration.zero()
        self.accelerate()

    def update(self, dt) -> Vector2:
        """更新物理状态"""
        self.accelerate()
        substeps = 10  # 从4增加到10
        dt /= substeps
        for _ in range(substeps):
            self.velocity += self.acceleration * dt
            self.position += self.velocity * dt
        self.velocity *= self.airResistance ** dt
        self.attrs = [
            {
                "type": "mass",
                "value": self.mass,
                "min": 0.1,
                "max": 128
            },
            {
                "type": "radius",
                "value": self.radius,
                "min": 1,
                "max": 128
            },
            {
                "type": "color",
                "value": self.color,
                "min": "#000000",
                "max": "#FFFFFF"
            }
        ]
        return self.position

    def draw(self, game) -> None:
        """绘制带渐变效果的小球"""
        if self.highLighted:
            pygame.draw.circle(game.screen, (255, 255, 0), 
                            (game.realToScreen(self.position.x, game.x), 
                            game.realToScreen(self.position.y, game.y)), 
                            game.realToScreen(self.radius + 0.5), 0)
        
        # 确保颜色是tuple格式
        if isinstance(self.color, str):
            c = colorStringToTuple(self.color)
        else:
            c = self.color
        
        num_circles = 20  # 固定20个同心圆
        
        # 绘制渐变效果
        for n in range(num_circles):
            # 计算当前半径比例（从1.0到0.0）
            ratio = n / (num_circles - 1)  # 修正比例计算
            
            # 当前实际半径
            current_radius = self.radius * (1 - ratio)
            
            # 颜色混合计算（外部保持原色，内部变浅）
            # 混合比例：外部（ratio=0）保持原色，内部（ratio=1）变浅50%
            mix_ratio = ratio  # 使用ratio来控制混合比例
            r = int(c[0] + (255 - c[0]) * mix_ratio * 0.5)
            g = int(c[1] + (255 - c[1]) * mix_ratio * 0.5)
            b = int(c[2] + (255 - c[2]) * mix_ratio * 0.5)
            
            # 透明度控制（外部不透明，内部半透明）
            alpha = int(255 * (1 - ratio * 0.5))  # 保持最低50%透明度
            
            # 转换坐标和尺寸
            pos = (
                game.realToScreen(self.position.x, game.x),
                game.realToScreen(self.position.y, game.y)
            )
            draw_radius = game.realToScreen(current_radius)
            
            # 创建临时surface实现透明度
            temp_surf = pygame.Surface((draw_radius*2, draw_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, (r, g, b, alpha), 
                            (draw_radius, draw_radius), 
                            draw_radius, 0)
            game.screen.blit(temp_surf, (pos[0]-draw_radius, pos[1]-draw_radius))
        
        self.highLighted = False

    def reboundByWall(self, wall: Self):
        """处理与墙体的碰撞反弹"""
        direction = self.position - wall.position
        self.position += direction * 0.1
        self.velocity = self.velocity * 0
        return self.velocity

    def reboundByLine(self, line: CollisionLine, timeIsReversed : bool = False) -> Vector2:
        """处理与线段的碰撞反弹逻辑"""
        AB = line.end - line.start
        line_length = AB.dot(AB)
        if abs(self.velocity) == 0:
            cosine = 1
        else:
            cosine = abs(self.velocity.y) / abs(self.velocity)
        
        # 处理零长度线段
        if line_length < 1e-5:
            return self.velocity
            
        AP = self.position - line.start
        t = AP.dot(AB) / line_length

        # 计算最近点和法线
        if line.isLine:  # 直线的情况
            closest = line.start + AB * t
            edge_normal = Vector2(-AB.y, AB.x).normalize()
            # 根据球的位置确定法线方向
            normal = edge_normal if (self.position - closest).dot(edge_normal) > 0 else -edge_normal
        else:  # 线段的情况
            if t < 0:
                closest = line.start
                normal = (self.position - closest).normalize()
            elif t > 1:
                closest = line.end
                normal = (self.position - closest).normalize()
            else:
                closest = line.start + AB * t
                edge_normal = Vector2(-AB.y, AB.x).normalize()
                normal = edge_normal if (self.position - closest).dot(edge_normal) > 0 else -edge_normal

        # 计算穿透深度
        penetration = self.radius - self.position.distance(closest)
        
        if penetration > 0:
            # 更精确的位置修正，穿透深度较大时增加能量损失
            energy_loss_factor = 1 + min(1, penetration / self.radius)
            self.position += normal * (penetration * energy_loss_factor)
            
            # 速度反射（保留切线分量）
            vel_normal = self.velocity.dot(normal)
            self.velocity -= normal * (2 * vel_normal)
            
            # 将法向分量乘以 self.collisionFactor
            vel_normal_after_rebound = self.velocity.dot(normal)
            self.velocity += normal * (vel_normal_after_rebound * ((self.collisionFactor * line.collisionFactor if not timeIsReversed else 1/self.collisionFactor/line.collisionFactor) - 1))
            
            # 调整速度大小
            self.velocity = self.velocity.copy().normalize() * abs(abs(self.velocity) ** 2 - 2 * 98.1 * cosine * (penetration)) ** 0.5

        return self.velocity

    def reboundByBall(self, ball: Self) -> Vector2:
        """处理球与球之间的碰撞响应"""
        # 获取双方质量
        m1 = self.mass
        m2 = ball.mass
        total_mass = m1 + m2

        # 计算实际间距
        delta = self.position - ball.position
        actual_distance = abs(delta)
        min_distance = self.radius + ball.radius
        
        # 处理零距离特殊情况
        if actual_distance < 1e-5:
            # 使用随机方向避免零向量
            normal = Vector2(1, 0) if random() > 0.5 else Vector2(-1, 0)
            actual_distance = min_distance
        else:
            normal = delta / actual_distance

        tangent = normal.vertical()
        
        # 记录碰撞前速度用于位置修正
        original_v1 = self.velocity.copy()
        original_v2 = ball.velocity.copy()
        
        # 分解速度分量
        v1n = original_v1.dot(normal)
        v1t = original_v1.dot(tangent)
        v2n = original_v2.dot(normal)
        v2t = original_v2.dot(tangent)
        
        # 弹性碰撞公式
        new_v1n = ((m1 - m2)*v1n + 2*m2*v2n) / total_mass
        new_v2n = (2*m1*v1n + (m2 - m1)*v2n) / total_mass
        
        # 应用碰撞因子到法向分量（新增部分）
        collision_factor = self.collisionFactor * ball.collisionFactor
        new_v1n *= collision_factor
        new_v2n *= collision_factor
        
        # 重建速度矢量（保持原始方向）
        self.velocity = tangent * v1t + normal * new_v1n
        ball.velocity = tangent * v2t + normal * new_v2n
        
        # 位置修正
        overlap = (min_distance - actual_distance)
        if overlap > 0:
            relative_velocity = (original_v1 - original_v2).dot(normal)
            if relative_velocity < 0:
                collision_factor = self.collisionFactor * ball.collisionFactor
                # 修改分离量计算方式
                separation = normal * (overlap * (1.001 / collision_factor))  
                self.position += separation * (m2 / total_mass)
                ball.position -= separation * (m1 / total_mass)

        return self.velocity

    # 物体之间的引力
    def gravitate(self, other: Self) -> Vector2:
        """处理球与球之间的引力（稳定版）"""
        G = 5e+4  # 添加引力常数调节参数
        min_distance = 1  # 防止距离过近导致力过大
        
        # 计算实际距离
        delta_pos = self.position - other.position
        distance = max(abs(delta_pos), min_distance)
        
        # 计算引力方向（保证单位向量稳定性）
        direction = delta_pos.normalize() if distance > 0 else Vector2(0,0)
        
        # 完整万有引力公式（含距离缩放）
        force_mag = G * self.mass * other.mass / (distance ** 2 + 1e-6)
        force = -direction * force_mag  # 正确的吸引方向
        
        # 应用作用力时考虑质量分配
        self.force(force, isNatural=True)
        other.force(-force, isNatural=True)
        
        return force

    # 计算环绕速度
    def getCircularVelocity(self, ball : Self) -> Vector2:
        """计算两个球的环绕速度"""
        # 计算距离
        distance = self.position.distance(ball.position)
        if distance == 0:
            return Vector2(0, 0)
        # 计算速度方向
        direction = (ball.position - self.position).vertical().normalize()
        # 计算速度大小
        velocity = direction * (ball.mass / distance * 1e+5) ** 0.5
        # 修改速度
        self.velocity = velocity + ball.velocity

        return self.velocity

    # 天体合并
    def merge(self, other: Self, game) -> Self:
        """处理球与球之间的天体合并"""
        
        total_position = (self.position * self.mass + other.position * other.mass) / (self.mass + other.mass)
        total_velocity = (self.velocity * self.mass + other.velocity * other.mass) / (self.mass + other.mass)
        total_force = self.artificialForces + other.artificialForces
        total_radius = round((self.radius ** 2 + other.radius ** 2) ** 0.5, 1)
        total_mass = self.mass + other.mass
        total_color = colorTupleToString(colorMiddle(self.color, other.color, self.radius / total_radius))
        
        newBall = Ball(total_position, total_radius, total_color, total_mass, total_velocity, total_force, gravitation=game.isCelestialBodyMode)
        return newBall

class Wall(Element):
    """墙体类，处理多边形碰撞和显示"""
    def __init__(self, vertexes: list[Vector2], color):
        self.vertexes = vertexes
        self.color = color
        self.position = Vector2((vertexes[0].x + vertexes[1].x + vertexes[2].x + vertexes[3].x) / 4,
                                (vertexes[0].y + vertexes[1].y + vertexes[2].y + vertexes[3].y) / 4)
        self.originalPosition = self.position.copy()
        self.lines = [CollisionLine(vertexes[0], vertexes[1]), CollisionLine(vertexes[1], vertexes[2]),
                     CollisionLine(vertexes[2], vertexes[3]), CollisionLine(vertexes[3], vertexes[0])]
        self.highLighted = False
        self.type = "wall"

    def setAttr(self, name, value):
        if value != "":
            if name == "color":
                self.color = value

    def copy(self, game):
        newWall = copy.deepcopy(self)
        game.elements["all"].append(newWall)
        game.elements["wall"].append(newWall)
        isMoving = True 
        while isMoving:
            newWall.position = Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y))
            newWall.draw(game)
            
            game.update()
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        isMoving = False

    def getPosToPoint(self, point: Vector2) -> Vector2:
        return self.position - point

    def update(self, dt):
        """更新墙体位置并维护碰撞线段"""
        # 计算位置
        offset = self.position - self.originalPosition
        for i in range(len(self.vertexes)):
            self.vertexes[i] += offset
        self.lines = [CollisionLine(self.vertexes[0], self.vertexes[1]), CollisionLine(self.vertexes[1], self.vertexes[2]),
                     CollisionLine(self.vertexes[2], self.vertexes[3]), CollisionLine(self.vertexes[3], self.vertexes[0])]
        self.originalPosition = self.position.copy()

        self.attrs = [
            {
                "type": "color",
                "value": self.color,
                "min": "#000000",
                "max": "#FFFFFF"
            }
        ]

    def check_vertex_collision(self, ball):
        """检测球与墙体顶点的碰撞"""
        for vertex in self.vertexes:
            if ball.position.distance(vertex) <= ball.radius:
                # 计算从顶点到球心的方向作为法线
                normal = (ball.position - vertex).normalize()
                self.handle_vertex_collision(ball, vertex, normal)

    def handle_vertex_collision(self, ball, vertex, normal):
        """处理顶点碰撞的响应"""
        # 计算穿透深度
        penetration = ball.radius - ball.position.distance(vertex)
        if penetration > 0:
            # 位置修正
            ball.position += normal * penetration * 1.1
            # 速度反射（使用顶点法线）
            vel_normal = ball.velocity.dot(normal)
            ball.velocity -= normal * (2 * vel_normal)

    def isPosOn(self, game, pos: Vector2):
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

    def draw(self, game):
        """绘制带高亮效果的墙体"""
        if self.highLighted: 
            # 计算中心点
            center = self.position
            # 计算扩展比例
            expand = 1  # 向外扩展
            
            highLightList = []
            for v in self.vertexes:
                # 获取中心到顶点的方向向量
                direction = (v - center)
                # 归一化后扩展
                if abs(direction) > 0:
                    direction.normalize()
                    # 保持原始顶点顺序，沿方向向外扩展
                    highLightList.append(v + direction * expand)
                else:
                    highLightList.append(v.copy())
            pygame.draw.polygon(game.screen, (255, 255, 0), [(game.realToScreen(hightLight.x, game.x), game.realToScreen(hightLight.y, game.y)) for hightLight in highLightList], 0)

        pygame.draw.polygon(game.screen, self.color, [(game.realToScreen(v.x, game.x), game.realToScreen(v.y, game.y)) for v in self.vertexes], 0)
        self.highLighted = False

class WallPosition:
    def __init__(self, wall: Wall, position: Vector2):
        self.wall = wall
        self.position = position

class Rope:
    def __init__(self, start: Ball | WallPosition, end: Ball | WallPosition, length: float, width: float, color) -> bool:
        self.start = start
        self.end = end
        self.length = length
        self.width = width
        self.color = color
        if isinstance(start, WallPosition) and isinstance(end, WallPosition):
            return False
        return True
    
    def update(self, dt):
        if isinstance(self.start, Ball) and isinstance(self.end, Ball):
            ...
        elif isinstance(self.start, WallPosition) and isinstance(self.end, Ball):
            ...
        elif isinstance(self.start, Ball) and isinstance(self.end, WallPosition):
            ...
        else:
            ...

    def draw(self, game):
        pygame.draw.line(game.screen, self.color, (game.realToScreen(self.start.position.x, game.x), game.realToScreen(self.start.position.y, game.y)), (game.realToScreen(self.end.position.x, game.x), game.realToScreen(self.end.position.y, game.y)), self.width)