from ..basic import *
from tkinter import messagebox
from .option import *
import pygame
import time


class InputBox:
    """输入框控件类"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        option: Option,
        target: Element,
        text: str = "",
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width - 100, height)
        self.colorInactive: pygame.Color = pygame.Color("lightskyblue3")
        self.colorActive: pygame.Color = pygame.Color("dodgerblue2")
        self.color: pygame.Color = self.colorInactive
        self.text: str = text
        self.font: pygame.font.Font = pygame.font.Font(None, int(height))
        self.textSurface: pygame.Surface = self.font.render(
            self.text, True, self.color)
        self.active: bool = False
        self.cursorVisible: bool = True
        self.cursorTimer: float = 0
        self.option: Option = option
        self.target: Element = target
        self.active: bool = False
        self.isColorError: bool = False

        if self.option["type"] != "color":
            self.min: float = float(self.option["min"])
            self.max: float = float(self.option["max"])

    def handleEvent(self, event: pygame.event, game: "Game") -> None:
        """处理输入事件"""

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 如果点击了输入框区域，激活输入框
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.colorActive if self.active else self.colorInactive

        if event.type == pygame.KEYDOWN:

            if self.active:

                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:

                    if not self.isColorError:
                        game.isEditing = False
                        self.attrUpdate(self.target)

                    else:
                        messagebox.showerror(
                            "错误", "您输入的颜色不合法!!!\n请输入合法的颜色编号或名称!"
                        )
                        game.isEditing = True

                else:

                    if self.option["type"] != "color":

                        if event.key == pygame.K_BACKSPACE:
                            self.text = self.text[:-1]

                        if (
                            event.unicode.isdigit()
                            or event.unicode == "."
                            or event.unicode == "-"
                        ):

                            try:
                                self.text += event.unicode

                                if float(self.text) < self.min:
                                    self.text = str(self.min)

                                elif float(self.text) > self.max:
                                    self.text = str(self.max)

                            except ValueError:
                                self.text = self.text[:-1]

                    else:

                        if event.key == pygame.K_BACKSPACE:
                            self.text = self.text[:-1]

                        if event.unicode.isalnum() or event.unicode == "#":
                            self.text += event.unicode

                        self.isColorError = False

                        try:

                            if len(self.text) != 0 and self.text[0] == "#":
                                self.text = self.text[0:7]

                            pygame.Color(self.text)
                            self.attrUpdate(self.target)

                        except ValueError:
                            self.isColorError = True

            game.lastTime = game.currentTime
            game.currentTime = time.time()
            self.textSurface = self.font.render(self.text, True, self.color)

    def attrUpdate(self, target: Element) -> None:
        """更新目标属性"""
        if self.text == "":
            target.setAttr(self.option["type"], self.option["min"])
        else:
            target.setAttr(self.option["type"], self.text)

    def update(self) -> None:
        """更新输入框状态"""

        # 更新光标状态
        self.cursorTimer += 1

        if self.cursorTimer >= 30:
            self.cursorVisible = not self.cursorVisible
            self.cursorTimer = 0

    def draw(self, screen: pygame.Surface) -> None:
        """绘制输入框"""

        # 绘制输入框和文本
        screen.blit(self.textSurface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

        # 渲染光标
        if self.active and self.cursorVisible:
            cursorPos = (
                self.font.render(self.text, True, self.color).get_width()
                + self.rect.x
                + 5
            )
            pygame.draw.line(
                screen,
                self.color,
                (cursorPos, self.rect.y + 5),
                (cursorPos, self.rect.y + 27),
                2,
            )
