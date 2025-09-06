from typing import Self
from .ball import *
from .collision_line import *
from .coordinator import *
from .element import *
from .vector2 import *
import pygame
import copy


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
        self.collisionFactor: float = 1.0

        self.attrs: list[dict] = []
        self.updateAttrsList()

    def setAttr(self, key: str, value: str) -> None:
        """设置属性值"""
        if value != "":
            if key == "color":
                self.color = value
            elif key == "collisionFactor":
                self.collisionFactor = float(value)

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
