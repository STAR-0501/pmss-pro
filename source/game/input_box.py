import time

import pygame

from ..basic import *
from .option import *

# from tkinter import messagebox
# 移除 tkinter 弹窗，改用 pygame 窗口内美化弹窗


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
        font_size: int | None = None,
    ) -> None:
        # 调整输入框大小，增加内边距
        padding = 15
        self.rect: pygame.Rect = pygame.Rect(x + padding, y + padding//2, width - 2*padding, height - padding)
        self.colorInactive: pygame.Color = pygame.Color(100, 149, 237)  # 矢车菊蓝
        self.colorActive: pygame.Color = pygame.Color(30, 144, 255)   # 道奇蓝
        self.color: pygame.Color = self.colorInactive
        self.text: str = text
        # 文本颜色：统一深蓝色
        self.textColor: pygame.Color = pygame.Color(25, 25, 112)  # 午夜蓝
        # 光标位置（字符索引）
        self.cursor_pos: int = len(text)
        # 如果未指定字体大小，则根据高度计算
        if font_size is None:
            font_size = int(height * 0.7)
        self.font: pygame.font.Font = pygame.font.Font("static/HarmonyOS_Sans_SC_Medium.ttf", font_size)
        self.textSurface: pygame.Surface = self.font.render(
            self.text, True, self.textColor)
        self.active: bool = False
        self.cursorVisible: bool = True
        self.cursorTimer: float = 0
        self.option: Option = option
        self.target: Element = target
        self.active: bool = False
        self.isColorError: bool = False
        
        # 增加内边距，让文本框比文字稍高
        self.padding = int(height * 0.15)

        if self.option["type"] != "color":
            self.min: float = float(self.option["min"])
            self.max: float = float(self.option["max"])

    def handleEvent(self, event: pygame.event, game: "Game") -> None:
        """处理输入事件"""

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 如果点击了输入框区域，激活输入框
            if self.rect.collidepoint(event.pos):
                self.active = True
                # 根据点击位置计算光标索引
                click_x = event.pos[0] - (self.rect.x + (self.rect.width - self.textSurface.get_width()) / 2)
                click_x = max(0, click_x)
                self.cursor_pos = 0
                for i in range(len(self.text)+1):
                    prefix_width = self.font.render(self.text[:i], True, self.textColor).get_width()
                    if prefix_width >= click_x:
                        self.cursor_pos = i
                        break
                else:
                    self.cursor_pos = len(self.text)
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
                        # 颜色不合法：在 pygame 窗口内展示美化弹窗，而不是系统弹窗
                        # 结构: { type, title, message }
                        game.uiModal = {
                            "type": "error",
                            "title": "错误",
                            "message": "您输入的颜色不合法!!!\n请输入合法的颜色编号或名称!",
                        }
                        game.isEditing = True

                else:

                    if self.option["type"] != "color":

                        if event.key == pygame.K_BACKSPACE:
                            if self.cursor_pos > 0:
                                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                                self.cursor_pos -= 1

                        if (
                            event.unicode.isdigit()
                            or event.unicode == "."
                            or event.unicode == "-"
                        ):

                            try:
                                self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                                self.cursor_pos += 1

                                # if float(self.text) < self.min:
                                #     self.text = str(self.min)

                                # elif float(self.text) > self.max:
                                #     self.text = str(self.max)

                            except ValueError:
                                self.text = self.text[:-1]

                    else:

                        if event.key == pygame.K_BACKSPACE:
                            if self.cursor_pos > 0:
                                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                                self.cursor_pos -= 1

                        if event.unicode.isalnum() or event.unicode == "#":
                            self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                            self.cursor_pos += 1

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
            # 方向键移动光标
            if event.key == pygame.K_LEFT:
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
            if event.key == pygame.K_RIGHT:
                if self.cursor_pos < len(self.text):
                    self.cursor_pos += 1
            # 始终使用统一的文本颜色渲染
            self.textSurface = self.font.render(self.text, True, self.textColor)

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
        # 绘制输入框背景
        pygame.draw.rect(screen, (245, 245, 245), self.rect, border_radius=5)  # 背景填充
        # 绘制输入框边框
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=5)

        # 计算文本在输入框内居中的位置（考虑内边距）
        text_width = self.textSurface.get_width()
        text_height = self.textSurface.get_height()
        
        # 水平居中：文本在输入框中央
        text_x = self.rect.x + (self.rect.width - text_width) / 2
        # 垂直居中：文本在输入框中央
        text_y = self.rect.y + (self.rect.height - text_height) / 2
        
        # 绘制输入框和文本（居中显示）
        screen.blit(self.textSurface, (text_x, text_y))

        # 渲染光标（基于居中文本的位置），按时间闪烁
        blink_speed_ms = 500  # 闪烁间隔
        ticks = pygame.time.get_ticks()
        if self.active and (ticks // blink_speed_ms) % 2 == 0:
            # 根据光标索引计算前缀宽度（使用统一文本颜色计算）
            prefix_width = self.font.render(self.text[:self.cursor_pos], True, self.textColor).get_width()
            cursor_x = text_x + prefix_width
            cursor_y = self.rect.y + self.rect.height / 2
            pygame.draw.line(
                screen,
                self.color,
                (cursor_x, cursor_y - 10),
                (cursor_x, cursor_y + 10),
                2,
            )
