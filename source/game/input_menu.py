from ..basic import *
from .option import *
from .input_box import *
import pygame
import time


class InputMenu(Element):
    """输入菜单界面类"""

    def __init__(self, position: Vector2, game: "Game", target: Element) -> None:
        # 优化垂直间距和整体布局
        self.verticalSpacing: float = 80  # 减小间距
        self.position: Vector2 = position
        self.width: float = game.screen.get_width() / 2.5  # 增加宽度
        self.height: float = 0
        self.x: float = position.x - self.width / 2
        self.y: float = position.y - self.height / 2
        self.commitFunction: str = ""
        self.font: pygame.font.Font = pygame.font.Font(
            "static/HarmonyOS_Sans_SC_Medium.ttf", int(
                self.verticalSpacing / 5)  # 增大字体
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

        # 添加顶部和底部边距
        top_margin = 30
        bottom_margin = 30
        
        for i in range(length):
            option = self.options[i]
            # 计算每个输入框的y坐标，添加顶部边距
            y = self.y + top_margin + i * self.verticalSpacing
            
            # 调整输入框大小比例
            inputBox = InputBox(
                self.x + self.width * 0.35,  # 调整左侧区域比例
                y,
                self.width * 0.6,  # 增加输入框宽度
                int(self.verticalSpacing * 0.65),  # 输入框高度略增
                option,
                self.target,
                str(option["value"]),
                int(self.verticalSpacing * 0.5 * 0.7),  # 固定字体大小
            )
            self.height += self.verticalSpacing  # 更新InputMenu的高度
            self.inputBoxes.append(inputBox)

        # 包含顶部和底部边距的总高度
        total_height = self.height + top_margin + bottom_margin
        self.x = self.position.x - self.width / 2
        self.y = self.position.y - total_height / 2
        game.lastTime = game.currentTime
        game.currentTime = time.time()

    def updateBoxes(self, event: pygame.event.Event, game: "Game") -> None:
        """更新输入框状态"""
        for box in self.inputBoxes:
            box.handleEvent(event, game)

    def draw(self, game: "Game") -> None:
        """绘制输入菜单"""
        # 绘制现代化输入菜单背景（天蓝色渐变）
        background_color = (240, 248, 255)  # 爱丽丝蓝
        border_color = (100, 149, 237)  # 矢车菊蓝
        
        # 添加阴影效果
        shadow_offset = 3
        shadow_rect = pygame.Rect(
            self.x + shadow_offset, 
            self.y + shadow_offset, 
            self.width, 
            self.height
        )
        pygame.draw.rect(
            game.screen,
            (220, 220, 220),  # 浅灰色阴影
            shadow_rect,
            border_radius=15,
        )
        
        # 绘制主背景
        pygame.draw.rect(
            game.screen,
            background_color,
            (self.x, self.y + 15, self.width, self.height),
            border_radius=15,
        )
        # 绘制输入菜单边框
        pygame.draw.rect(
            game.screen,
            border_color,
            (self.x, self.y + 15, self.width, self.height),
            3,  # 加粗边框
            border_radius=15,
        )

        # 绘制所有输入框和选项文本
        length = len(self.options)

        for i in range(length):
            optionType = self.options[i]["type"]
            inputBox = self.inputBoxes[i]

            # 绘制选项文本（现代化配色）
            optionText = self.font.render(
                game.translation[optionType], True, (25, 25, 112))  # 午夜蓝
            
            # 左侧文本区域的宽度和位置
            text_area_width = self.width * 0.35
            text_area_x = self.x
            text_area_y = inputBox.rect.y
            text_area_height = inputBox.rect.height
            
            # 计算文本在区域内的居中位置
            text_x = text_area_x + (text_area_width - optionText.get_width()) / 2
            text_y = text_area_y + (text_area_height - optionText.get_height()) / 2
            
            game.screen.blit(optionText, (text_x, text_y))

            # 绘制输入框
            inputBox.draw(game.screen)
