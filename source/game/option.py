from ..basic import *
from .set_caps_lock import *


class Option:
    """菜单选项类"""

    def __init__(
        self, pos: Vector2, size: Vector2, type: str, attrs_: list, menu: "Menu"
    ) -> None:
        self.x: float = pos.x
        self.y: float = pos.y
        self.width: float = size.x
        self.height: float = size.y
        self.type: str = type
        self.pos: Vector2 = pos
        self.name: str = ""
        self.creationPoints: list = []
        self.isAbsorption: bool = False
        self.attrs: dict = {}
        self.selected: bool = False
        self.highLighted: bool = False
        self.attrs_: list = attrs_
        for attr in self.attrs_:
            self.attrs[attr["type"]] = attr["value"]

    def isLineCrossingWall(
        self, start: Vector2, end: Vector2, wall: Wall, game: "Game"
    ) -> bool:
        """
        检查线段是否完全穿过墙壁（而不仅仅是与边缘相交）
        """
        if wall.type != "wall":
            return False

        # 检查线段是否完全穿过墙体
        start_inside = self.isPointInsideWall(start, wall, game)
        end_inside = self.isPointInsideWall(end, wall, game)

        # 如果一个点在内部，一个点在外部，则线段穿过墙体
        if (start_inside and not end_inside) or (not start_inside and end_inside):
            return True

        # 如果两个点都在外部，检查线段是否与墙体的任意两条边相交
        if not start_inside and not end_inside:
            intersect_count = 0
            for i in range(len(wall.vertexes)):
                wall_start = wall.vertexes[i]
                wall_end = wall.vertexes[(i + 1) % len(wall.vertexes)]

                if self.doLinesIntersect(start, end, wall_start, wall_end):
                    intersect_count += 1

            return intersect_count >= 2

        return False

    def isPointInsideWall(self, point: Vector2, wall: Wall, game: "Game") -> bool:
        """
        检查点是否在墙体内部
        使用射线法判断点是否在多边形内部
        """
        if wall.type != "wall":
            return False

        # 射线法：从点向右发射一条射线，计算与多边形边的交点数
        intersect_count = 0
        for i in range(len(wall.vertexes)):
            v1 = wall.vertexes[i]
            v2 = wall.vertexes[(i + 1) % len(wall.vertexes)]

            if (v1.y > point.y) != (v2.y > point.y):
                x_intersect = (v2.x - v1.x) * (point.y -
                                               v1.y) / (v2.y - v1.y) + v1.x

                if point.x < x_intersect:
                    intersect_count += 1

        return intersect_count % 2 == 1

    def doLinesIntersect(
        self, p1: Vector2, p2: Vector2, p3: Vector2, p4: Vector2
    ) -> bool:
        """
        检查两条线段是否相交
        p1, p2: 第一条线段的端点
        p3, p4: 第二条线段的端点
        """

        # 计算方向
        def direction(a, b, c):
            return (c.y - a.y) * (b.x - a.x) - (b.y - a.y) * (c.x - a.x)

        # 检查点c是否在线段ab上
        def on_segment(a, b, c):
            return min(a.x, b.x) <= c.x <= max(a.x, b.x) and min(
                a.y, b.y
            ) <= c.y <= max(a.y, b.y)

        d1 = direction(p3, p4, p1)
        d2 = direction(p3, p4, p2)
        d3 = direction(p1, p2, p3)
        d4 = direction(p1, p2, p4)

        # 如果两条线段相交
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and (
            (d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)
        ):
            return True

        # 特殊情况：共线
        if d1 == 0 and on_segment(p3, p4, p1):
            return True
        if d2 == 0 and on_segment(p3, p4, p2):
            return True
        if d3 == 0 and on_segment(p1, p2, p3):
            return True
        if d4 == 0 and on_segment(p1, p2, p4):
            return True

        return False

    def drawArrow(
        self,
        game: "Game",
        startPos: tuple[float, float],
        endPos: tuple[float, float],
        color: pygame.Color,
    ) -> None:
        """绘制箭头（坐标参数用tuple而不是Vector2）"""
        pygame.draw.line(game.screen, color, startPos, endPos, 3)

        # 计算箭头的方向
        dx = endPos[0] - startPos[0]
        dy = endPos[1] - startPos[1]
        angle = math.atan2(dy, dx)

        # 箭头的大小
        arrowLength = 15
        arrowAngle = math.pi / 6  # 30度

        # 计算箭头的两个端点
        arrowPoint1 = (
            endPos[0] - arrowLength * math.cos(angle - arrowAngle),
            endPos[1] - arrowLength * math.sin(angle - arrowAngle),
        )

        arrowPoint2 = (
            endPos[0] - arrowLength * math.cos(angle + arrowAngle),
            endPos[1] - arrowLength * math.sin(angle + arrowAngle),
        )

        # 绘制箭头
        pygame.draw.polygon(game.screen, color, [
                            endPos, arrowPoint1, arrowPoint2])

    def isLineCrossingWall(self, start: Vector2, end: Vector2, wall: Wall) -> bool:
        """
        检查线段是否完全穿过墙壁
        start: 线段起点
        end: 线段终点
        wall: 墙壁对象
        """
        if wall.type != "wall":
            return False

        # 计算线段与墙体边的交点数
        intersect_count = 0
        for i in range(len(wall.vertexes)):
            wall_start = wall.vertexes[i]
            wall_end = wall.vertexes[(i + 1) % len(wall.vertexes)]

            if self.doLinesIntersect(start, end, wall_start, wall_end):
                intersect_count += 1

        # 如果与墙体的边相交两次或以上，则线段穿过墙体
        return intersect_count >= 2

    def doLinesIntersect(
        self, p1: Vector2, p2: Vector2, p3: Vector2, p4: Vector2
    ) -> bool:
        """
        检查两条线段是否相交
        p1, p2: 第一条线段的端点
        p3, p4: 第二条线段的端点
        """

        # 计算方向
        def direction(a, b, c):
            return (c.y - a.y) * (b.x - a.x) - (b.y - a.y) * (c.x - a.x)

        # 检查点c是否在线段ab上
        def on_segment(a, b, c):
            return min(a.x, b.x) <= c.x <= max(a.x, b.x) and min(
                a.y, b.y
            ) <= c.y <= max(a.y, b.y)

        d1 = direction(p3, p4, p1)
        d2 = direction(p3, p4, p2)
        d3 = direction(p1, p2, p3)
        d4 = direction(p1, p2, p4)

        # 如果两条线段相交
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and (
            (d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)
        ):
            return True

        # 特殊情况：共线
        if d1 == 0 and on_segment(p3, p4, p1):
            return True
        if d2 == 0 and on_segment(p3, p4, p2):
            return True
        if d3 == 0 and on_segment(p1, p2, p3):
            return True
        if d4 == 0 and on_segment(p1, p2, p4):
            return True

        return False

    def isPointInsideWall(self, point: Vector2, wall: Wall, game: "Game") -> bool:
        """
        检查点是否在墙体内部
        使用射线法判断点是否在多边形内部
        """
        if wall.type != "wall":
            return False

        # 射线法：从点向右发射一条射线，计算与多边形边的交点数
        intersect_count = 0
        for i in range(len(wall.vertexes)):
            v1 = wall.vertexes[i]
            v2 = wall.vertexes[(i + 1) % len(wall.vertexes)]

            if (v1.y > point.y) != (v2.y > point.y):
                x_intersect = (v2.x - v1.x) * (point.y -
                                               v1.y) / (v2.y - v1.y) + v1.x

                if point.x < x_intersect:
                    intersect_count += 1

        return intersect_count % 2 == 1

    def isMouseOn(self) -> bool:
        """判断鼠标是否在选项区域"""
        pos = pygame.mouse.get_pos()
        return self.isPosOn(Vector2(pos))

    def isPosOn(self, pos: Vector2) -> bool:
        """判断指定位置是否在选项区域"""
        return (
            pos.x > self.x
            and pos.x < self.x + self.width
            and pos.y > self.y
            and pos.y < self.y + self.height
        )

    def ballCreate(self, game: "Game") -> None:
        """创建球体"""
        game.isScreenMoving = False
        game.isMoving = False
        game.isElementCreating = True
        game.isDragging = False
        game.circularVelocityFactor = 1
        radius = float(self.attrs["radius"])
        color = self.attrs["color"]
        mass = float(self.attrs["mass"])
        ball = None
        self.selected = True
        self.highLighted = True
        coordinator = Coordinator(0, 0, 200, game)
        self.additionVelocity = ZERO

        while game.isElementCreating:

            game.isElementCreating = True
            mousePosition = pygame.mouse.get_pos()
            game.update()

            maximumGravitationBall = game.findMaximumGravitationBall(ball)
            if maximumGravitationBall is not None:
                maximumGravitationBallCopy = copy.deepcopy(
                    maximumGravitationBall)
                maximumGravitationBallCopy.velocity = ZERO

            if (
                game.isCelestialBodyMode
                and game.isCircularVelocityGetting
                and maximumGravitationBall is not None
            ):

                if 0 <= game.circularVelocityFactor <= 1:
                    circularVelocityFactorColor = colorMiddle(
                        "green", "yellow", game.circularVelocityFactor
                    )
                elif 1 <= game.circularVelocityFactor <= 2**0.5:
                    circularVelocityFactorColor = colorMiddle(
                        "yellow",
                        "green",
                        (game.circularVelocityFactor - 1) / (2**0.5 - 1),
                    )
                elif 2**0.5 <= game.circularVelocityFactor <= 2:
                    circularVelocityFactorColor = colorMiddle(
                        "red", "yellow", (game.circularVelocityFactor - 2**0.5)
                    )
                else:
                    circularVelocityFactorColor = "red"

                pygame.draw.circle(
                    game.screen,
                    circularVelocityFactorColor,
                    game.realToScreen(
                        maximumGravitationBall.position, Vector2(
                            game.x, game.y)
                    ).toTuple(),
                    game.realToScreen(
                        ball.position.distance(maximumGravitationBall.position)
                    ),
                    3,
                )
                velocity = ball.getCircularVelocity(
                    maximumGravitationBallCopy,
                    game.circularVelocityFactor
                    * (1 if game.isCircularVelocityDirectionAnticlockwise else -1),
                )
                self.drawArrow(
                    game,
                    mousePosition,
                    game.realToScreen(
                        ball.position
                        + velocity.copy().normalize() * abs(velocity) ** 0.5 * 2,
                        Vector2(game.x, game.y),
                    ).toTuple(),
                    circularVelocityFactorColor,
                )

                if game.circularVelocityFactor != 1:
                    circularVelocityFactorText = game.fontSmall.render(
                        f"{game.circularVelocityFactor: .1f}x",
                        True,
                        circularVelocityFactorColor,
                    )
                    circularVelocityFactorRect = circularVelocityFactorText.get_rect()
                    circularVelocityFactorRect.x = (
                        pygame.mouse.get_pos()[0] + game.fontSmall.get_height()
                    )
                    circularVelocityFactorRect.y = (
                        pygame.mouse.get_pos()[1]
                        - game.fontSmall.get_height()
                        - game.realToScreen(ball.radius)
                    )
                    game.screen.blit(
                        circularVelocityFactorText, circularVelocityFactorRect
                    )

            if not game.isDragging:

                ball = Ball(
                    Vector2(
                        game.screenToReal(mousePosition[0], game.x),
                        game.screenToReal(mousePosition[1], game.y),
                    ),
                    radius,
                    color,
                    mass,
                    ZERO,
                    [ZERO],
                    True,
                )
                self.creationPoints = [ball.position, ball.position]
                ball.draw(game)
                radiusText = game.fontSmall.render(
                    f"半径 = {radius}", True, colorSuitable(
                        ball.color, game.background)
                )
                radiusTextRect = radiusText.get_rect()
                radiusTextRect.x = mousePosition[0]
                radiusTextRect.y = mousePosition[1]
                game.screen.blit(radiusText, radiusTextRect)

                massText = game.fontSmall.render(
                    f"质量 = {mass: .1f}",
                    True,
                    colorSuitable(ball.color, game.background),
                )
                massTextRect = massText.get_rect()
                massTextRect.x = mousePosition[0]
                massTextRect.y = mousePosition[1] + radiusText.get_height()
                game.screen.blit(massText, massTextRect)

            if game.isDragging:

                if not game.isCelestialBodyMode or not game.isCircularVelocityGetting:
                    startPos = (
                        game.realToScreen(ball.position.x, game.x),
                        game.realToScreen(ball.position.y, game.y),
                    )
                    endPos = (
                        game.realToScreen(self.creationPoints[1].x, game.x),
                        game.realToScreen(self.creationPoints[1].y, game.y),
                    )

                    self.creationPoints[1] = Vector2(
                        game.screenToReal(mousePosition[0], game.x),
                        game.screenToReal(mousePosition[1], game.y),
                    )

                    if coordinator.isMouseOn():
                        self.drawArrow(game, startPos, endPos, "yellow")
                    else:
                        self.drawArrow(game, startPos, endPos, "blue")

                    ball.draw(game)
                    coordinator.position = ball.position
                    self.additionVelocity = (
                        self.creationPoints[1] - self.creationPoints[0]
                    ) * 2
                    coordinator.update(game)
                    coordinator.draw(game, self)

                else:
                    ball.position = Vector2(
                        game.screenToReal(mousePosition[0], game.x),
                        game.screenToReal(mousePosition[1], game.y),
                    )
                    ball.draw(game)
                    coordinator.position = ball.position
                    coordinator.update(game)
                    coordinator.draw(game, self)

            pygame.display.update()
            for event in pygame.event.get():

                game.isPressed = False
                if event.type == pygame.MOUSEBUTTONDOWN:

                    if event.button == 1:
                        allowToPlace = True
                        game.isDragging = True

                        for element in game.elements["all"]:
                            if element.isMouseOn(game):
                                allowToPlace = False
                                break

                        if not game.elementMenu.isMouseOn() and allowToPlace:
                            ball = Ball(
                                Vector2(
                                    game.screenToReal(
                                        mousePosition[0], game.x),
                                    game.screenToReal(
                                        mousePosition[1], game.y),
                                ),
                                radius,
                                color,
                                mass,
                                ZERO,
                                [ZERO],
                            )

                    elif (
                        event.button == 3
                        and game.isCelestialBodyMode
                        and game.isCircularVelocityGetting
                    ):
                        game.isCircularVelocityDirectionAnticlockwise = (
                            not game.isCircularVelocityDirectionAnticlockwise
                        )

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:

                    if self.isMouseOn():
                        self.highLighted = False
                        self.selected = False
                        game.isElementCreating = False
                        break

                    elif game.elementMenu.isMouseOn():
                        for option in game.elementMenu.options:
                            if option.isMouseOn() and not option.selected:
                                game.isElementCreating = False
                                self.highLighted = False
                                self.selected = False
                                option.createElement(
                                    game, Vector2(
                                        mousePosition[0], mousePosition[1])
                                )
                                break

                    elif not game.elementMenu.isMouseOn() or game.isDragging:
                        game.isDragging = False
                        ball = Ball(
                            ball.position,
                            radius,
                            color,
                            mass,
                            Vector2(
                                game.screenToReal(mousePosition[0], game.x)
                                - ball.position.x,
                                game.screenToReal(mousePosition[1], game.y)
                                - ball.position.y,
                            )
                            * 2,
                            [],
                            gravitation=game.isCelestialBodyMode,
                        )
                        maximumGravitationBall = game.findMaximumGravitationBall(
                            ball)
                        if maximumGravitationBall is not None:
                            maximumGravitationBallCopy = copy.deepcopy(
                                maximumGravitationBall
                            )
                            maximumGravitationBallCopy.velocity = ZERO

                        if (
                            maximumGravitationBall is not None
                            and game.isCelestialBodyMode
                            and game.isCircularVelocityGetting
                        ):
                            ball.velocity = ball.getCircularVelocity(
                                maximumGravitationBall,
                                game.circularVelocityFactor
                                * (
                                    1
                                    if game.isCircularVelocityDirectionAnticlockwise
                                    else -1
                                ),
                            )

                        game.elements["all"].append(ball)
                        game.elements["ball"].append(ball)

                        for ball in game.elements["ball"]:
                            ball.displayedAcceleration = (
                                ball.acceleration
                                + (ball.displayedAcceleration - ball.acceleration)
                                * ball.displayedAccelerationFactor
                            )
                            ball.displayedAccelerationFactor = 1

                    else:
                        for option in game.elementMenu.options:
                            if option.isMouseOn():
                                game.isElementCreating = False
                                self.highLighted = False
                                self.selected = False
                                method = eval(f"option.{option.type}Create")
                                method(game)
                                break

                if event.type == pygame.MOUSEWHEEL and not game.isDragging:

                    if (
                        not game.isCelestialBodyMode
                        or not game.isCircularVelocityGetting
                    ):

                        if event.y == 1:
                            if game.isMassSetting:
                                mass += 0.1
                            else:
                                radius += 1

                        if event.y == -1:
                            if game.isMassSetting and mass > 0.2:
                                mass -= 0.1
                            elif radius > 1:
                                radius -= 1

                    else:

                        if event.y == 1:
                            game.circularVelocityFactor += 0.1

                        if event.y == -1:
                            game.circularVelocityFactor -= 0.1

                            if game.circularVelocityFactor < 0:
                                game.circularVelocityFactor = 0

                if event.type == pygame.KEYUP:

                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        game.isMassSetting = False

                    if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                        game.isCircularVelocityGetting = False
                        game.circularVelocityFactor = 1

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:
                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)
                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.KEYDOWN:

                    if (
                        event.key == pygame.K_z
                        and game.isCtrlPressing
                        and len(self.elements["all"]) > 0
                    ):
                        game.undoLastElement()

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.showLoadedTip(
                            f"default/{str(event.key - pygame.K_0)}")

                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        game.isMassSetting = True

                    if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                        game.isCircularVelocityGetting = True

                    if event.key == pygame.K_SPACE:
                        game.isPaused = not game.isPaused

                    if event.key == pygame.K_r:
                        game.elements["all"].clear()

                        for option in game.elementMenu.options:
                            game.elements[option.type].clear()

                    if event.key == pygame.K_ESCAPE:
                        game.isElementCreating = False
                        self.highLighted = False
                        self.selected = False
                        break

                    if event.key == pygame.K_p:

                        if game.isCelestialBodyMode:
                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "0"

                                if option["type"] == "gravity":
                                    option["value"] = "1"

                            game.GroundSurfaceMode()

                        else:
                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "1"

                                if option["type"] == "gravity":
                                    option["value"] = "0"

                            game.CelestialBodyMode()

                game.screenMove(event)

    def wallCreate(self, game: "Game") -> None:
        """创建墙体"""
        game.isElementCreating = True
        self.highLighted = True
        self.selected = True
        clickNum = 0
        coordinator = Coordinator(0, 0, 0, game)

        while game.isElementCreating:
            game.isElementCreating = True
            game.update()

            if clickNum % 4 == 3:
                self.creationPoints[3] = Vector2(
                    self.creationPoints[0].x
                    + (self.creationPoints[2].x - self.creationPoints[1].x),
                    self.creationPoints[0].y
                    + (self.creationPoints[2].y - self.creationPoints[1].y),
                )
                wall = Wall(self.creationPoints, self.attrs["color"])
                game.elements["all"].append(wall)
                game.elements["wall"].append(wall)
                clickNum = 0

            if clickNum % 4 == 2:
                pygame.draw.line(
                    game.screen,
                    self.attrs["color"],
                    (
                        game.realToScreen(self.creationPoints[0].x, game.x),
                        game.realToScreen(self.creationPoints[0].y, game.y),
                    ),
                    (
                        game.realToScreen(self.creationPoints[1].x, game.x),
                        game.realToScreen(self.creationPoints[1].y, game.y),
                    ),
                )

                pos = pygame.mouse.get_pos()
                pos = Vector2(
                    game.screenToReal(pos[0], game.x), game.screenToReal(
                        pos[1], game.y)
                )
                line1 = self.creationPoints[0] - self.creationPoints[1]
                line2 = pos - self.creationPoints[1]
                line3 = line2.projectVertical(line1)
                self.creationPoints[2] = self.creationPoints[1] + line3
                self.creationPoints[3] = Vector2(
                    self.creationPoints[0].x
                    + (self.creationPoints[2].x - self.creationPoints[1].x),
                    self.creationPoints[0].y
                    + (self.creationPoints[2].y - self.creationPoints[1].y),
                )
                pygame.draw.polygon(
                    game.screen,
                    self.attrs["color"],
                    [
                        (
                            game.realToScreen(
                                self.creationPoints[0].x, game.x),
                            game.realToScreen(
                                self.creationPoints[0].y, game.y),
                        ),
                        (
                            game.realToScreen(
                                self.creationPoints[1].x, game.x),
                            game.realToScreen(
                                self.creationPoints[1].y, game.y),
                        ),
                        (
                            game.realToScreen(
                                self.creationPoints[2].x, game.x),
                            game.realToScreen(
                                self.creationPoints[2].y, game.y),
                        ),
                        (
                            game.realToScreen(
                                self.creationPoints[3].x, game.x),
                            game.realToScreen(
                                self.creationPoints[3].y, game.y),
                        ),
                    ],
                )
                pygame.display.update()

            if clickNum % 4 == 1:
                coordinator.width = 200
                coordinator.update(game)
                coordinator.draw(game, self)

                if coordinator.isMouseOn():
                    pygame.draw.line(
                        game.screen,
                        "yellow",
                        (
                            game.realToScreen(
                                self.creationPoints[0].x, game.x),
                            game.realToScreen(
                                self.creationPoints[0].y, game.y),
                        ),
                        (
                            game.realToScreen(
                                self.creationPoints[1].x, game.x),
                            game.realToScreen(
                                self.creationPoints[1].y, game.y),
                        ),
                    )
                else:
                    pygame.draw.line(
                        game.screen,
                        self.attrs["color"],
                        (
                            game.realToScreen(
                                self.creationPoints[0].x, game.x),
                            game.realToScreen(
                                self.creationPoints[0].y, game.y),
                        ),
                        pygame.mouse.get_pos(),
                    )

                pygame.display.update()

            if clickNum % 4 == 0:
                coordinator.position = Vector2(
                    game.screenToReal(pygame.mouse.get_pos()[0], game.x),
                    game.screenToReal(pygame.mouse.get_pos()[1], game.y),
                )
                coordinator.width = 10
                coordinator.update(game)
                coordinator.draw(game, self)
                pygame.display.update()

            for event in pygame.event.get():
                game.isPressed = False

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:

                        if not game.elementMenu.isMouseOn():
                            allowToPlace = True

                            for element in game.elements["ball"]:
                                if element.isMouseOn(game):
                                    allowToPlace = False
                                    break

                            if allowToPlace:

                                if clickNum % 4 == 2:
                                    clickNum += 1

                                if clickNum % 4 == 1:

                                    if not self.isAbsorption:
                                        self.creationPoints[1] = Vector2(
                                            game.screenToReal(
                                                event.pos[0], game.x),
                                            game.screenToReal(
                                                event.pos[1], game.y),
                                        )
                                        self.isAbsorption = False

                                    else:
                                        self.isAbsorption = False
                                    clickNum += 1

                                if clickNum % 4 == 0:
                                    self.creationPoints = [
                                        Vector2(
                                            game.screenToReal(
                                                event.pos[0], game.x),
                                            game.screenToReal(
                                                event.pos[1], game.y),
                                        )
                                        for i in range(4)
                                    ]
                                    clickNum += 1

                        if self.isMouseOn():
                            self.highLighted = False
                            self.selected = False
                            game.isElementCreating = False
                            break

                        for option in game.elementMenu.options:
                            if option.isMouseOn():
                                game.isElementCreating = False
                                self.highLighted = False
                                self.selected = False
                                method = eval(f"option.{option.type}Create")
                                method(game)
                                break

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.KEYDOWN:
                    if (
                        event.key == pygame.K_z
                        and game.isCtrlPressing
                        and len(self.elements["all"]) > 0
                    ):
                        game.undoLastElement()

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.showLoadedTip(
                            f"default/{str(event.key - pygame.K_0)}")

                    if event.key == pygame.K_SPACE:
                        game.isPaused = not game.isPaused

                    if event.key == pygame.K_r:
                        game.elements["all"].clear()
                        for option in game.elementMenu.options:
                            game.elements[option.type].clear()

                    if event.key == pygame.K_ESCAPE:
                        game.isElementCreating = False
                        self.highLighted = False
                        self.selected = False
                        break

                    if event.key == pygame.K_p:
                        if game.isCelestialBodyMode:
                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "0"

                                if option["type"] == "gravity":
                                    option["value"] = "1"

                            game.GroundSurfaceMode()

                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "1"

                                if option["type"] == "gravity":
                                    option["value"] = "0"

                            game.CelestialBodyMode()

                game.screenMove(event)

    def ropeCreate(self, game: "Game") -> None:
        """创建绳子"""
        game.isElementCreating = True
        self.highLighted = True
        self.selected = True
        clickNum = 0
        chosenElement = [
            Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
            Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
        ]
        lineColor = "black"

        while game.isElementCreating:
            game.isElementCreating = True
            game.update()

            for element in game.elements["ball"]:
                if element.isMouseOn(game) and not hasWallBetween:
                    element.highLighted = True
                    break
                else:
                    element.highLighted = False

            for element in game.elements["wall"]:
                if element.isMouseOn(game) and not hasWallBetween:
                    element.highLighted = True
                    break
                else:
                    element.highLighted = False

            # 检查预览线是否完全穿过墙体
            hasWallBetween = False
            start_pos = chosenElement[0].position
            mouse_pos = Vector2(
                game.screenToReal(pygame.mouse.get_pos()[0], game.x),
                game.screenToReal(pygame.mouse.get_pos()[1], game.y),
            )

            for wall in game.elements["wall"]:
                if self.isLineCrossingWall(start_pos, mouse_pos, wall):
                    hasWallBetween = True
                    break

            if clickNum % 2 == 0:
                pygame.display.update()

            if clickNum == 1:

                # 根据是否有墙壁阻挡设置线条颜色
                lineColor = "red" if hasWallBetween else "black"

                pygame.draw.line(
                    game.screen,
                    lineColor,
                    (
                        game.realToScreen(chosenElement[0].position.x, game.x),
                        game.realToScreen(chosenElement[0].position.y, game.y),
                    ),
                    pygame.mouse.get_pos(),
                    width=2,
                )
                pygame.display.update()

            if clickNum == 2:

                if not hasWallBetween:
                    length = game.realToScreen(
                        float(self.attrs["lengthLimit"]))
                    if length == 0:
                        length = abs(chosenElement[0].position - mouse_pos)
                    rope = Rope(
                        chosenElement[0], chosenElement[1], length, 2, "black")
                    game.elements["all"].append(rope)
                    game.elements["rope"].append(rope)

                    clickNum = 0
                    chosenElement = [
                        Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
                        Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
                    ]
                else:
                    clickNum = 1  # 回到第一次点击后的状态，保留第一个点

            for event in pygame.event.get():
                game.isPressed = False

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:

                        if not game.elementMenu.isMouseOn():
                            for element in game.elements["all"]:
                                if element.isMouseOn(game):

                                    if clickNum % 2 == 0:
                                        if element.type == "ball":
                                            chosenElement[0] = element
                                        if element.type == "wall":
                                            pos = Vector2(
                                                game.screenToReal(
                                                    event.pos[0], game.x),
                                                game.screenToReal(
                                                    event.pos[1], game.y),
                                            )
                                            wallPosition = WallPosition(
                                                element, pos)
                                            chosenElement[0] = wallPosition
                                        clickNum += 1
                                    else:
                                        if element.type == "ball":
                                            chosenElement[1] = element
                                        if element.type == "wall":
                                            pos = Vector2(
                                                game.screenToReal(
                                                    event.pos[0], game.x),
                                                game.screenToReal(
                                                    event.pos[1], game.y),
                                            )
                                            wallPosition = WallPosition(
                                                element, pos)
                                            chosenElement[1] = wallPosition
                                        clickNum += 1

                        elif self.isMouseOn():
                            self.highLighted = False
                            self.selected = False
                            game.isElementCreating = False
                            break

                        for option in game.elementMenu.options:
                            if option.isMouseOn():
                                game.isElementCreating = False
                                self.highLighted = False
                                self.selected = False
                                method = eval(f"option.{option.type}Create")
                                method(game)
                                break

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.KEYDOWN:
                    if (
                        event.key == pygame.K_z
                        and game.isCtrlPressing
                        and len(self.elements["all"]) > 0
                    ):
                        game.undoLastElement()

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.showLoadedTip(
                            f"default/{str(event.key - pygame.K_0)}")

                    if event.key == pygame.K_SPACE:
                        game.isPaused = not game.isPaused

                    if event.key == pygame.K_r:
                        game.elements["all"].clear()
                        for option in game.elementMenu.options:
                            game.elements[option.type].clear()

                    if event.key == pygame.K_ESCAPE:
                        game.isElementCreating = False
                        self.highLighted = False
                        self.selected = False
                        break

                    if event.key == pygame.K_p:
                        if game.isCelestialBodyMode:
                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "0"

                                if option["type"] == "gravity":
                                    option["value"] = "1"

                            game.GroundSurfaceMode()

                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "1"

                                if option["type"] == "gravity":
                                    option["value"] = "0"

                            game.CelestialBodyMode()

    def rodCreate(self, game: "Game") -> None:
        """创建轻杆"""
        game.isElementCreating = True
        self.highLighted = True
        self.selected = True
        clickNum = 0
        chosenElement = [
            Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
            Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
        ]
        lineColor = "black"

        while game.isElementCreating:
            game.isElementCreating = True
            game.update()

            for element in game.elements["ball"]:
                if element.isMouseOn(game) and not hasWallBetween:
                    element.highLighted = True
                    break
                else:
                    element.highLighted = False

            for element in game.elements["wall"]:
                if element.isMouseOn(game) and not hasWallBetween:
                    element.highLighted = True
                    break
                else:
                    element.highLighted = False

            # 检查预览线是否完全穿过墙体
            hasWallBetween = False
            start_pos = chosenElement[0].position
            mouse_pos = Vector2(
                game.screenToReal(pygame.mouse.get_pos()[0], game.x),
                game.screenToReal(pygame.mouse.get_pos()[1], game.y),
            )

            for wall in game.elements["wall"]:
                if self.isLineCrossingWall(start_pos, mouse_pos, wall):
                    hasWallBetween = True
                    break

            if clickNum % 2 == 0:
                pygame.display.update()

            if clickNum == 1:

                # 根据是否有墙壁阻挡设置线条颜色
                lineColor = "red" if hasWallBetween else "black"

                pygame.draw.line(
                    game.screen,
                    lineColor,
                    (
                        game.realToScreen(chosenElement[0].position.x, game.x),
                        game.realToScreen(chosenElement[0].position.y, game.y),
                    ),
                    pygame.mouse.get_pos(),
                    width=int(game.screenToReal(15)),
                )
                pygame.display.update()

            if clickNum == 2:

                if not hasWallBetween:
                    length = abs(
                        chosenElement[0].position - chosenElement[1].position)
                    if float(self.attrs["lengthLimit"]) > 0:
                        length = float(self.attrs["lengthLimit"])
                    rod = Rod(
                        chosenElement[0],
                        chosenElement[1],
                        length,
                        game.screenToReal(15),
                        "black",
                    )
                    game.elements["all"].append(rod)
                    game.elements["rod"].append(rod)

                    clickNum = 0
                    chosenElement = [
                        Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
                        Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
                    ]
                else:
                    clickNum = 1  # 回到第一次点击后的状态，保留第一个点

            for event in pygame.event.get():
                game.isPressed = False

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:

                        if not game.elementMenu.isMouseOn():
                            for element in game.elements["all"]:
                                if element.isMouseOn(game):

                                    if clickNum % 2 == 0:
                                        if element.type == "ball":
                                            chosenElement[0] = element
                                        if element.type == "wall":
                                            pos = Vector2(
                                                game.screenToReal(
                                                    event.pos[0], game.x),
                                                game.screenToReal(
                                                    event.pos[1], game.y),
                                            )
                                            wallPosition = WallPosition(
                                                element, pos)
                                            chosenElement[0] = wallPosition
                                        clickNum += 1
                                    else:
                                        if element.type == "ball":
                                            chosenElement[1] = element
                                        if element.type == "wall":
                                            pos = Vector2(
                                                game.screenToReal(
                                                    event.pos[0], game.x),
                                                game.screenToReal(
                                                    event.pos[1], game.y),
                                            )
                                            wallPosition = WallPosition(
                                                element, pos)
                                            chosenElement[1] = wallPosition
                                        clickNum += 1

                        elif self.isMouseOn():
                            self.highLighted = False
                            self.selected = False
                            game.isElementCreating = False
                            break

                        for option in game.elementMenu.options:
                            if option.isMouseOn():
                                game.isElementCreating = False
                                self.highLighted = False
                                self.selected = False
                                method = eval(f"option.{option.type}Create")
                                method(game)
                                break

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.KEYDOWN:
                    if (
                        event.key == pygame.K_z
                        and game.isCtrlPressing
                        and len(game.elements["all"]) > 0
                    ):
                        game.undoLastElement()

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.showLoadedTip(
                            f"default/{str(event.key - pygame.K_0)}")

                    if event.key == pygame.K_SPACE:
                        game.isPaused = not game.isPaused

                    if event.key == pygame.K_r:
                        game.elements["all"].clear()
                        for option in game.elementMenu.options:
                            game.elements[option.type].clear()

                    if event.key == pygame.K_ESCAPE:
                        game.isElementCreating = False
                        self.highLighted = False
                        self.selected = False
                        break

                    if event.key == pygame.K_p:
                        if game.isCelestialBodyMode:
                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "0"

                                if option["type"] == "gravity":
                                    option["value"] = "1"

                            game.GroundSurfaceMode()

                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "1"

                                if option["type"] == "gravity":
                                    option["value"] = "0"

                            game.CelestialBodyMode()

    def springCreate(self, game: "Game") -> None:
        """创建弹簧"""
        game.isElementCreating = True
        self.highLighted = True
        self.selected = True
        clickNum = 0
        chosenElement = [
            Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
            Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
        ]
        lineColor = "black"

        while game.isElementCreating:
            game.isElementCreating = True
            game.update()

            for element in game.elements["ball"]:
                if element.isMouseOn(game) and not hasWallBetween:
                    element.highLighted = True
                    break
                else:
                    element.highLighted = False

            for element in game.elements["wall"]:
                if element.isMouseOn(game) and not hasWallBetween:
                    element.highLighted = True
                    break
                else:
                    element.highLighted = False

            # 检查预览线是否完全穿过墙体
            hasWallBetween = False
            start_pos = chosenElement[0].position
            mouse_pos = Vector2(
                game.screenToReal(pygame.mouse.get_pos()[0], game.x),
                game.screenToReal(pygame.mouse.get_pos()[1], game.y),
            )

            for wall in game.elements["wall"]:
                if self.isLineCrossingWall(start_pos, mouse_pos, wall):
                    hasWallBetween = True
                    break

            if clickNum % 2 == 0:
                pygame.display.update()

            if clickNum == 1:

                # 根据是否有墙壁阻挡设置线条颜色
                lineColor = "red" if hasWallBetween else "black"

                pygame.draw.line(
                    game.screen,
                    lineColor,
                    (
                        game.realToScreen(chosenElement[0].position.x, game.x),
                        game.realToScreen(chosenElement[0].position.y, game.y),
                    ),
                    pygame.mouse.get_pos(),
                    width=2,
                )
                pygame.display.update()

            if clickNum == 2:

                if not hasWallBetween:
                    # 计算自然长度，如果设置了长度限制则使用限制值
                    restLength = abs(
                        chosenElement[0].position - chosenElement[1].position
                    )
                    if float(self.attrs["lengthLimit"]) > 0:
                        restLength = float(self.attrs["lengthLimit"])

                    # 创建弹簧，使用适当的刚度系数
                    stiffness = 100.0  # 默认刚度系数
                    if "stiffness" in self.attrs and float(self.attrs["stiffness"]) > 0:
                        stiffness = float(self.attrs["stiffness"])

                    spring = Spring(
                        chosenElement[0],
                        chosenElement[1],
                        restLength,
                        stiffness,
                        2,
                        "black",
                    )
                    game.elements["all"].append(spring)
                    game.elements["spring"].append(spring)

                    clickNum = 0
                    chosenElement = [
                        Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
                        Ball(Vector2(0, 0), 0, "black", 0, Vector2(0, 0), []),
                    ]
                else:
                    clickNum = 1  # 回到第一次点击后的状态，保留第一个点

            for event in pygame.event.get():
                game.isPressed = False

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:

                        if not game.elementMenu.isMouseOn():
                            for element in game.elements["all"]:
                                if element.isMouseOn(game):

                                    if clickNum % 2 == 0:
                                        if element.type == "ball":
                                            chosenElement[0] = element
                                        if element.type == "wall":
                                            pos = Vector2(
                                                game.screenToReal(
                                                    event.pos[0], game.x),
                                                game.screenToReal(
                                                    event.pos[1], game.y),
                                            )
                                            wallPosition = WallPosition(
                                                element, pos)
                                            chosenElement[0] = wallPosition
                                        clickNum += 1
                                    else:
                                        if element.type == "ball":
                                            chosenElement[1] = element
                                        if element.type == "wall":
                                            pos = Vector2(
                                                game.screenToReal(
                                                    event.pos[0], game.x),
                                                game.screenToReal(
                                                    event.pos[1], game.y),
                                            )
                                            wallPosition = WallPosition(
                                                element, pos)
                                            chosenElement[1] = wallPosition
                                        clickNum += 1

                        elif self.isMouseOn():
                            self.highLighted = False
                            self.selected = False
                            game.isElementCreating = False
                            break

                        for option in game.elementMenu.options:
                            if option.isMouseOn():
                                game.isElementCreating = False
                                self.highLighted = False
                                self.selected = False
                                method = eval(f"option.{option.type}Create")
                                method(game)
                                break

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.KEYDOWN:
                    if (
                        event.key == pygame.K_z
                        and game.isCtrlPressing
                        and len(game.elements["all"]) > 0
                    ):
                        game.undoLastElement()

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.showLoadedTip(
                            f"default/{str(event.key - pygame.K_0)}")

                    if event.key == pygame.K_SPACE:
                        game.isPaused = not game.isPaused

                    if event.key == pygame.K_r:
                        game.elements["all"].clear()
                        for option in game.elementMenu.options:
                            game.elements[option.type].clear()

                    if event.key == pygame.K_ESCAPE:
                        game.isElementCreating = False
                        self.highLighted = False
                        self.selected = False
                        break

                    if event.key == pygame.K_p:
                        if game.isCelestialBodyMode:
                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "0"

                                if option["type"] == "gravity":
                                    option["value"] = "1"

                            game.GroundSurfaceMode()

                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "1"

                                if option["type"] == "gravity":
                                    option["value"] = "0"

                            game.CelestialBodyMode()

    def exampleCreate(self, game: "Game") -> None:
        attrs = copy.deepcopy(self.attrs)
        attrs["path"] = attrs["path"].replace(".pkl", "")
        game.loadGame(attrs["path"])
        loadedTipText = game.fontSmall.render(
            f"{game.gameName}加载成功", True, (0, 0, 0)
        )
        loadedTipRect = loadedTipText.get_rect(
            center=(game.screen.get_width() / 2, game.screen.get_height() / 2)
        )

        game.update()
        game.screen.blit(loadedTipText, loadedTipRect)
        pygame.display.update()
        time.sleep(0.5)
        game.lastTime = time.time()
        game.currentTime = time.time()

    def elementEdit(self, game: "Game", attrs: list) -> None:
        """打开编辑元素属性框"""
        # 延迟导入以避免循环依赖
        from .input_menu import InputMenu
        inputMenu = InputMenu(
            Vector2(game.screen.get_width() / 2, game.screen.get_height() / 2),
            game,
            self,
        )

        # 从元素实例获取实时属性值
        updated_attrs = []
        for attr in self.attrs_:

            # 创建属性字典的深拷贝
            newAttr = copy.deepcopy(attr)

            # 用当前元素的实际属性值更新
            newAttr["value"] = str(self.attrs[attr["type"]])
            updated_attrs.append(newAttr)

        inputMenu.options = updated_attrs  # 使用更新后的属性列表
        game.openEditor(inputMenu)

    def setAttr(self, key: str, value: str) -> None:
        """设置元素属性"""
        for atr in self.attrs_:
            if atr["type"] == key:
                atr["value"] = value

        self.attrs[key] = value

    def draw(self, game: "Game") -> None:
        """绘制选项界面"""
        # 悬停缩放效果（替代黄色边框）
        hover = self.isMouseOn()
        radius = int(self.width * 15 / 100)

        # 与设置按钮一致的阴影风格（仅在悬停时显示）
        if hover:
            shadow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 50), shadow.get_rect(), border_radius=radius)
            game.screen.blit(shadow, (self.x + 4, self.y + 4))

        # 背景卡片
        pygame.draw.rect(
            game.screen,
            (255, 255, 255),
            (self.x, self.y, self.width, self.height),
            border_radius=radius,
        )

        if self.type == "ball":
            # 使用与实体小球一致的渐变绘制
            # 解析颜色
            base_color = self.attrs.get("color", (0, 0, 0))
            if isinstance(base_color, str):
                try:
                    color = colorStringToTuple(base_color)
                except Exception:
                    color = (0, 0, 0)
            else:
                color = base_color

            # 悬停缩放：整体内容按照 hover 轻微放大
            hover = self.isMouseOn()
            scale_factor = 1.0 if not hover else 1.08

            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            r = min(self.width, self.height) / 3 * scale_factor

            circleNumber = 20
            for number in range(circleNumber):
                ratio = number / (circleNumber - 1)
                currentRadius = r * (1 - ratio)

                mixRatio = ratio
                red = int(color[0] + (255 - color[0]) * mixRatio * 0.5)
                green = int(color[1] + (255 - color[1]) * mixRatio * 0.5)
                blue = int(color[2] + (255 - color[2]) * mixRatio * 0.5)
                alpha = int(255 * (1 - ratio * 0.5))

                drawRadius = int(currentRadius)
                if drawRadius <= 0:
                    continue

                tempSurface = pygame.Surface((drawRadius * 2, drawRadius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    tempSurface,
                    (red, green, blue, alpha),
                    (drawRadius, drawRadius),
                    drawRadius,
                    0,
                )
                # 按 scale_factor 居中贴图
                game.screen.blit(tempSurface, (cx - drawRadius, cy - drawRadius))

        if self.type == "wall":
            hover = self.isMouseOn()
            scale_factor = 1.0 if not hover else 1.08
            rect_w = self.width * 8 / 10 * scale_factor
            rect_h = self.height * 8 / 10 * scale_factor
            rect_x = self.x + (self.width - rect_w) / 2
            rect_y = self.y + (self.height - rect_h) / 2
            pygame.draw.rect(
                game.screen,
                self.attrs["color"],
                (
                    rect_x,
                    rect_y,
                    rect_w,
                    rect_h,
                ),
            )

        if self.type == "rope":
            # 悬停缩放（放大振幅，保持居中）
            hover = self.isMouseOn()
            scale_factor = 1.0 if not hover else 1.08
            points = []
            for i in range(11):
                x_pos = self.x + self.width * i / 10
                y_center = self.y + self.height / 2
                amplitude = (self.height / 4) * scale_factor
                y_pos = y_center + math.sin(i * math.pi / 5) * amplitude
                points.append((x_pos, y_pos))

            # 绘制曲线
            if len(points) >= 2:
                pygame.draw.lines(game.screen, "black", False, points, width=2)

        if self.type == "rod":
            # 悬停缩放（加长线段并保持居中）
            hover = self.isMouseOn()
            scale_factor = 1.0 if not hover else 1.08
            line_len = self.width * 8 / 10 * scale_factor
            cx = self.x + self.width / 2
            y = self.y + self.height / 2
            start_point = (cx - line_len / 2, y)
            end_point = (cx + line_len / 2, y)
            pygame.draw.line(game.screen, "black", start_point, end_point, width=3)

        if self.type == "spring":
            hover = self.isMouseOn()
            scale_factor = 1.0 if not hover else 1.08
            points = []
            y_center = self.y + self.height / 2
            amplitude = (self.height / 4) * scale_factor
            points.append((self.x + self.width / 10, y_center))
            segment_width = self.width * 8 / 10 / 8
            for i in range(8):
                x_i = self.x + self.width / 10 + segment_width * (i + 0.5)
                y_i = y_center - amplitude if i % 2 == 0 else y_center + amplitude
                points.append((x_i, y_i))
            points.append((self.x + self.width * 9 / 10, y_center))
            if len(points) >= 2:
                pygame.draw.lines(game.screen, "black", False, points, width=2)

        if self.type == "example":
            try:
                icon = pygame.image.load(self.attrs["icon"]).convert_alpha()
                scaled_icon = pygame.transform.smoothscale(icon, (int(self.width), int(self.height)))
                icon_x = self.x + self.width / 2 - scaled_icon.get_width() / 2
                icon_y = self.y + self.height / 2 - scaled_icon.get_height() / 2
                game.screen.blit(scaled_icon, (icon_x, icon_y))
            except KeyError:
                ...
            except FileNotFoundError:
                ...

    def createElement(self, game: "Game", pos: Vector2) -> None:
        """创建元素对象"""
        x = pos.x
        y = pos.y

        if (
            x > self.x
            and x < self.x + self.width
            and y > self.y
            and y < self.y + self.height
        ):
            method = eval(f"self.{self.type}Create")
            method(game)

    def edit(self, game: "Game", pos: Vector2) -> None:
        """编辑元素属性"""
        x = pos.x
        y = pos.y

        if (
            x > self.x
            and x < self.x + self.width
            and y > self.y
            and y < self.y + self.height
        ):
            self.elementEdit(game, list(self.attrs.keys()))
