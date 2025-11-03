import pygame

from ..basic import *
from .input_menu import *


class ControlOption:
    """控制选项类"""

    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        color: pygame.Color,
    ) -> None:
        self.name: str = name
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height
        self.color: pygame.Color = color

    def attrEditor(self, game: "Game", target: Element) -> None:
        """打开属性编辑器"""
        inputMenu = InputMenu(
            Vector2(game.screen.get_width() / 2, game.screen.get_height() / 2),
            game,
            target,
        )

        for option in game.elementMenu.optionsList:
            if option["type"] == target.type:
                inputMenu.options = target.attrs
                inputMenu.target = target

        game.openEditor(inputMenu)

    def copy(self, game: "Game", target: Element) -> None:
        """复制目标"""
        target.copy(game)

    def delete(self, game: "Game", target: Element) -> None:
        """删除目标"""
        # 如果删除的是球或墙，需要同时删除与之相连的绳索、轻杆和弹簧
        if target.type == "ball" or target.type == "wall":
            # 创建一个列表存储需要删除的元素
            to_remove = []

            # 检查绳索
            for rope in game.elements["rope"]:
                if (
                    rope.start == target
                    or rope.end == target
                    or (hasattr(rope.start, "wall") and rope.start.wall == target)
                    or (hasattr(rope.end, "wall") and rope.end.wall == target)
                ):
                    to_remove.append(rope)

            # 检查轻杆（如果存在）
            if "rod" in game.elements:
                for rod in game.elements["rod"]:
                    if (
                        rod.start == target
                        or rod.end == target
                        or (hasattr(rod.start, "wall") and rod.start.wall == target)
                        or (hasattr(rod.end, "wall") and rod.end.wall == target)
                    ):
                        to_remove.append(rod)

            # 检查弹簧（如果存在）
            if "spring" in game.elements:
                for spring in game.elements["spring"]:
                    if (
                        spring.start == target
                        or spring.end == target
                        or (
                            hasattr(spring.start, "wall")
                            and spring.start.wall == target
                        )
                        or (hasattr(spring.end, "wall") and spring.end.wall == target)
                    ):
                        to_remove.append(spring)

            # 删除相关的连接元素
            for element in to_remove:
                try:
                    game.elements["all"].remove(element)
                    game.elements[element.type].remove(element)
                except:
                    ...

        # 原有的删除逻辑
        for type in game.elements.keys():
            if target in game.elements[type]:
                game.elements[type].remove(target)

        for ball in game.elements["ball"]:
            ball.displayedAcceleration = (
                ball.acceleration
                + (ball.displayedAcceleration - ball.acceleration)
                * ball.displayedAccelerationFactor
            )
            ball.displayedAccelerationFactor = 1

    def follow(self, game: "Game", target: Element) -> None:
        """视角跟随目标"""
        target.isShowingInfo = False
        target.isFollowing = not target.isFollowing

        for element in game.elements["all"]:
            if element is not target:
                element.isFollowing = False

    def showInfo(self, game: "Game", target: Element) -> None:
        """显示目标信息"""
        target.isFollowing = False
        target.isShowingInfo = not target.isShowingInfo

    def addVelocity(self, game: "Game", target: Element) -> None:
        """添加速度"""
        tempOption = Option(ZERO, ZERO, "temp", [], game.elementMenu)
        isAdding = True
        target.highLighted = True
        game.update()
        game.isPaused = True

        coordinator = Coordinator(0, 0, 200, game)
        coordinator.position = target.position
        coordinator.update(game)
        tempOption.creationPoints = [target.position, target.position]
        self.additionVelocity = (
            tempOption.creationPoints[1] - tempOption.creationPoints[0]
        )
        originVelocity = target.velocity
        originAcceleration = target.acceleration

        while isAdding:
            target.position = tempOption.creationPoints[0]
            startPos = game.realToScreen(
                target.position, Vector2(game.x, game.y)
            ).toTuple()
            endPos = game.realToScreen(
                tempOption.creationPoints[1], Vector2(game.x, game.y)
            ).toTuple()
            target.velocity = originVelocity
            target.acceleration = originAcceleration

            game.update()
            pos = pygame.mouse.get_pos()
            tempOption.creationPoints[1] = game.screenToReal(
                Vector2(pos), Vector2(game.x, game.y)
            )

            if coordinator.isMouseOn():
                tempOption.drawArrow(game, startPos, endPos, "yellow")
            else:
                tempOption.drawArrow(game, startPos, endPos, "blue")

            coordinator.update(game)
            coordinator.draw(
                game, tempOption, str(
                    round(abs(self.additionVelocity) / 10)) + "m/s"
            )
            self.additionVelocity = (
                tempOption.creationPoints[1] - tempOption.creationPoints[0]
            )

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    target.displayedVelocity = (
                        target.velocity
                        + (target.displayedVelocity - target.velocity)
                        * target.displayedVelocityFactor
                    )
                    target.displayedVelocityFactor = 1
                    target.velocity += (
                        tempOption.creationPoints[1] -
                        tempOption.creationPoints[0]
                    )
                    isAdding = False
                    target.highLighted = False

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_g:
                        game.saveGame("autosave")

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        preset_file = game.getPresetFileByIndex(event.key - pygame.K_0)
                        if preset_file:
                            game.showLoadedTip(preset_file)

                    if event.key == pygame.K_ESCAPE:
                        isAdding = False
                        target.highLighted = False

            game.lastTime = game.currentTime
            game.currentTime = time.time()
            pygame.display.update()

        game.isPaused = False

    def clearVelocity(self, game: "Game", target: Element) -> None:
        """清除速度"""
        target.displayedVelocity = target.velocity
        target.displayedVelocityFactor = 1
        target.velocity = ZERO

    def addForce(self, game: "Game", target: Element) -> None:
        """添加力"""
        tempOption = Option(ZERO, ZERO, "temp", [], game.elementMenu)
        isAdding = True
        target.highLighted = True
        game.update()
        game.isPaused = True

        coordinator = Coordinator(0, 0, 200, game)
        coordinator.position = target.position
        coordinator.update(game)
        tempOption.creationPoints = [target.position, target.position]
        self.additionForce = tempOption.creationPoints[1] - \
            tempOption.creationPoints[0]
        originVelocity = target.velocity
        originAcceleration = target.acceleration

        while isAdding:
            target.position = tempOption.creationPoints[0]
            startPos = game.realToScreen(
                target.position, Vector2(game.x, game.y)
            ).toTuple()
            endPos = game.realToScreen(
                tempOption.creationPoints[1], Vector2(game.x, game.y)
            ).toTuple()
            target.velocity = originVelocity
            target.acceleration = originAcceleration

            game.update()
            pos = pygame.mouse.get_pos()
            tempOption.creationPoints[1] = Vector2(
                game.screenToReal(pos[0], game.x), game.screenToReal(
                    pos[1], game.y)
            )

            if coordinator.isMouseOn():
                tempOption.drawArrow(game, startPos, endPos, "yellow")
            else:
                tempOption.drawArrow(game, startPos, endPos, "red")

            coordinator.update(game)
            coordinator.draw(
                game, tempOption, str(
                    round(abs(self.additionForce)) / 10) + "N"
            )
            self.additionForce = (
                tempOption.creationPoints[1] - tempOption.creationPoints[0]
            )

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    target.displayedAcceleration = (
                        target.acceleration
                        + (target.displayedAcceleration - target.acceleration)
                        * target.displayedAccelerationFactor
                    )
                    target.displayedAccelerationFactor = 1
                    target.force(self.additionForce)
                    isAdding = False
                    target.highLighted = False

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_g:
                        game.saveGame("manualsave")

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        # 防止连续按键时延迟叠加
                        current_time = time.time()
                        if current_time - game.lastLoadTime < 0.5:
                            continue
                        
                        preset_file = game.getPresetFileByIndex(event.key - pygame.K_0)
                        if preset_file:
                            game.loadGame(preset_file)
                            loadedTipText = game.fontSmall.render(
                                f"{game.gameName} 加载成功", True, (0, 0, 0)
                            )
                            loadedTipRect = loadedTipText.get_rect(
                                center=(
                                    game.screen.get_width() / 2,
                                    game.screen.get_height() / 2,
                                )
                            )
                            game.screen.blit(loadedTipText, loadedTipRect)
                            game.update()
                            pygame.display.update()
                            game.lastLoadTime = current_time
                        game.lastTime = time.time()
                        game.currentTime = time.time()

                    if event.key == pygame.K_ESCAPE:
                        isAdding = False
                        target.highLighted = False

            game.lastTime = game.currentTime
            game.currentTime = time.time()
            pygame.display.update()

        game.isPaused = False

    def clearForce(self, game: "Game", target: Element) -> None:
        """清除所有外力"""
        target.displayedAcceleration = target.acceleration
        target.displayedAccelerationFactor = 1
        target.artificialForces.clear()

    def isMouseOn(self) -> bool:
        """判断鼠标是否在控件上"""
        return self.isPosOn(Vector2(pygame.mouse.get_pos()))

    def isPosOn(self, pos: Vector2) -> bool:
        """判断指定坐标是否在控件上"""
        return (
            self.x < pos.x < self.x + self.width
            and self.y < pos.y < self.y + self.height
        )

    def draw(self, game: "Game") -> None:
        """绘制控件"""
        pygame.draw.rect(
            game.screen,
            self.color,
            (self.x, self.y, self.width, self.height),
            border_radius=int(self.width * 2 / 100),
        )
        text = game.translation[self.name]
        textSurface = game.fontSmall.render(text, True, (0, 0, 0))
        game.screen.blit(
            textSurface,
            (
                self.x + self.width / 2 - textSurface.get_width() / 2,
                self.y + self.height / 2 - textSurface.get_height() / 2,
            ),
        )
