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
        self.originalIcon = pygame.image.load("static/settings.png").convert_alpha()

        # 预设图标（初始缩放）
        self.icon: pygame.Surface = pygame.transform.smoothscale(
            self.originalIcon, (self.width, self.height)
        )

    def draw(self, game: "Game") -> None:
        """绘制设置按钮（圆角卡片 + 阴影 + 悬停缩放）"""
        hover: bool = self.isMouseOn()

        # 阴影层
        shadow_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            (0, 0, 0, 60),  # 半透明阴影
            pygame.Rect(0, 0, self.width, self.height),
            border_radius=int(min(self.width, self.height) / 2),
        )
        game.screen.blit(shadow_surf, (self.x + 3, self.y + 3))

        # 背景卡片
        card_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg_color = (255, 255, 255, 235) if not hover else (255, 255, 255, 255)
        border_color = (100, 149, 237, 255)  # 矢车菊蓝
        pygame.draw.rect(
            card_surf,
            bg_color,
            pygame.Rect(0, 0, self.width, self.height),
            border_radius=int(min(self.width, self.height) / 2),
        )
        pygame.draw.rect(
            card_surf,
            border_color,
            pygame.Rect(0, 0, self.width, self.height),
            width=2,
            border_radius=int(min(self.width, self.height) / 2),
        )
        game.screen.blit(card_surf, (self.x, self.y))

        # 图标（悬停轻微放大）
        scale_factor = 0.85 if not hover else 0.92
        icon_w = int(self.width * scale_factor)
        icon_h = int(self.height * scale_factor)
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
