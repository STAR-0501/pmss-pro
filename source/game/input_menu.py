from ..basic import *
from .option import *
from .input_box import *
import pygame
import time

class InputMenu(Element):
    """输入菜单界面类"""

    def __init__(self, position: Vector2, game: "Game", target: Element) -> None:
        # 每个输入框的垂直间距
        self.verticalSpacing: float = 100
        self.position: Vector2 = position
        self.width: float = game.screen.get_width() / 3
        self.height: float = 0
        self.x: float = position.x - self.width / 2
        self.y: float = position.y - self.height / 2
        self.commitFunction: str = ""
        self.font: pygame.font.Font = pygame.font.Font(
            "static/HarmonyOS_Sans_SC_Medium.ttf", int(
                self.verticalSpacing / 6)
        )
        self.options: list[Option] = []
        self.inputBoxes: list[InputBox] = []
        self.target: Element = target

    def update(self, game: "Game") -> None:
        """更新输入菜单布局"""
        # game.isPaused = False
        game.tempFrames = 1
        length = len(self.options)
        self.height = 0
        self.inputBoxes.clear()

        for i in range(length):
            option = self.options[i]
            # 计算每个输入框的y坐标
            y = self.y + 10 + i * self.verticalSpacing
            inputBox = InputBox(
                self.x + self.width * 3 / 10,
                y,
                self.width - self.width * 3 / 10,
                self.verticalSpacing / 3,
                option,
                self.target,
                str(option["value"]),
            )
            self.height += self.verticalSpacing  # 更新InputMenu的高度
            self.inputBoxes.append(inputBox)

        self.x = self.position.x - self.width / 2
        self.y = self.position.y - self.height / 2
        game.lastTime = game.currentTime
        game.currentTime = time.time()

    def updateBoxes(self, event: pygame.event.Event, game: "Game") -> None:
        """更新输入框状态"""
        for box in self.inputBoxes:
            box.handleEvent(event, game)

    def draw(self, game: "Game") -> None:
        """绘制输入菜单"""
        pygame.draw.rect(
            game.screen,
            (255, 255, 255),
            (self.x, self.y, self.width, self.height),
            border_radius=int(self.width * 2 / 100),
        )

        # 绘制所有输入框和选项文本
        length = len(self.options)

        for i in range(length):
            optionType = self.options[i]["type"]
            inputBox = self.inputBoxes[i]

            # 绘制选项文本
            optionText = self.font.render(
                game.translation[optionType], True, (0, 0, 0))
            game.screen.blit(optionText, (self.x, inputBox.rect.y))

            # 绘制输入框
            inputBox.draw(game.screen)
