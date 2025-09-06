import pygame

from ..basic import *


class SettingsButton:
    """设置按钮控件类"""

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height

        # 加载图片并转换为透明格式
        self.originalIcon = pygame.image.load("static/settings.png").convert_alpha()

        # 预设图标（初始缩放）
        self.icon: pygame.Surface = pygame.transform.smoothscale(
            self.originalIcon, (self.width, self.height)
        )

    def draw(self, game: "Game") -> None:
        """绘制设置按钮（与右侧栏一致：悬停阴影 + 白色卡片 + 悬停放大）"""
        hover: bool = self.isMouseOn()
        radius = int(self.width * 15 / 100)

        # 阴影（仅悬停时显示，与右侧栏一致）
        if hover:
            shadow_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(
                shadow_surf,
                (0, 0, 0, 50),
                pygame.Rect(0, 0, self.width, self.height),
                border_radius=radius,
            )
            game.screen.blit(shadow_surf, (self.x + 4, self.y + 4))

        # 背景卡片（纯白，无边框，与右侧栏一致）
        pygame.draw.rect(
            game.screen,
            (255, 255, 255),
            pygame.Rect(self.x, self.y, self.width, self.height),
            border_radius=radius,
        )

        # 图标（与右侧栏悬停缩放系数一致：1.08；保留基础留白）
        base_scale = 0.85
        scale_factor = 1.08 if hover else 1.0
        icon_w = int(self.width * base_scale * scale_factor)
        icon_h = int(self.height * base_scale * scale_factor)
        icon_scaled = pygame.transform.smoothscale(self.originalIcon, (icon_w, icon_h))

        icon_x = self.x + (self.width - icon_w) / 2
        icon_y = self.y + (self.height - icon_h) / 2
        game.screen.blit(icon_scaled, (icon_x, icon_y))

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
