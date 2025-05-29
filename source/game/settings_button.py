from ..basic import *
import pygame


class SettingsButton:
    """设置按钮控件类"""

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height

        # 加载图片并转换为透明格式
        originalIcon = pygame.image.load("static/settings.png").convert_alpha()

        # 调整图片大小
        self.icon: pygame.Surface = pygame.transform.scale(
            originalIcon, (self.width, self.height)
        )

    def draw(self, game: "Game") -> None:
        """绘制设置按钮"""
        game.screen.blit(self.icon, (self.x, self.y))

    def isMouseOn(self) -> bool:
        """判断鼠标是否在按钮上"""
        return self.isPosOn(
            Vector2(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
        )

    def isPosOn(self, pos: Vector2) -> bool:
        """判断指定坐标是否在按钮上"""
        return (
            pos.x > self.x
            and pos.x < self.x + self.width
            and pos.y > self.y
            and pos.y < self.y + self.height
        )
