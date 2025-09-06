import pygame

from ..basic import *
from .option import *


class Menu:
    def __init__(self, pos: Vector2, optionsList: list = []) -> None:
        width, height = pygame.display.get_surface().get_size()
        self.width: float = width * 3 / 100
        self.height: float = height * 80 / 100

        self.x: float = pos.x
        self.y: float = pos.y + (height - self.height) / 2

        self.optionsList: list = optionsList

        self.options: list = []
        for i in range(len(self.optionsList)):
            option = Option(
                Vector2(
                    self.x + self.width * 1 / 10,
                    self.y + self.width * 1 / 10 + i * self.width * 9 / 10,
                ),
                Vector2(self.width * 8 / 10, self.width * 8 / 10),
                self.optionsList[i]["type"],
                self.optionsList[i]["attrs"],
                self,
            )
            option.name = self.optionsList[i]["name"]
            self.options.append(option)

    def isMouseOn(self) -> bool:
        """判断鼠标是否在菜单区域"""
        pos = Vector2(pygame.mouse.get_pos())
        return self.isPosOn(pos)

    def isPosOn(self, pos: Vector2) -> bool:
        """判断指定位置是否在菜单区域"""
        return (
            pos.x > self.x
            and pos.x < self.x + self.width
            and pos.y > self.y
            and pos.y < self.y + self.height
        )

    def draw(self, game: "Game") -> None:
        """绘制菜单界面（圆角卡片 + 阴影 + 统一配色）"""
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        radius = int(self.width * 15 / 100)

        # 阴影
        shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 50), shadow.get_rect(), border_radius=radius)
        game.screen.blit(shadow, (rect.x + 4, rect.y + 4))

        # 背景卡片
        pygame.draw.rect(game.screen, (250, 250, 252), rect, border_radius=radius)
        # 边框
        pygame.draw.rect(game.screen, (100, 149, 237), rect, width=2, border_radius=radius)

        # 选项
        for option in self.options:
            option.draw(game)
