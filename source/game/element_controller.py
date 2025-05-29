from ..basic import *
from .control_option import *
import pygame

class ElementController:
    """右键菜单"""

    def __init__(self, element: Element, position: Vector2) -> None:
        self.x: float = position.x
        self.y: float = position.y
        self.optionWidth: float = 300
        self.optionHeight: float = 50
        self.element: Element = element
        self.controlOptionsList: list[ControlOption] = []
        self.controlOptions: list[ControlOption] = []

    def control(self, game: "Game") -> None:
        """控制元素"""
        for option in self.controlOptions:
            if option.isMouseOn():
                method = eval(f"option.{option.name}")
                method(game, self.element)
                game.isElementControlling = False
                self.element.highLighted = False
                break

    def isMouseOn(self) -> bool:
        """判断鼠标是否在控制器上"""
        return self.isPosOn(Vector2(pygame.mouse.get_pos()))

    def isPosOn(self, pos: Vector2) -> bool:
        """判断指定坐标是否在控制器上"""
        return (
            self.x < pos.x < self.x + self.optionWidth
            and self.y
            < pos.y
            < self.y + self.optionHeight * len(self.controlOptionsList)
        )

    def update(self, game: "Game") -> None:
        """更新控制器"""
        options = game.elementMenu.optionsList

        for option in options:
            if option["type"] == self.element.type:
                self.controlOptionsList = option["controlOptions"]

        screenHeight = game.screen.get_height()

        if self.y + len(self.controlOptionsList) * self.optionHeight > screenHeight:
            self.y -= len(self.controlOptionsList) * self.optionHeight + 50

        currentY = self.y  # 初始 y 坐标

        for option in self.controlOptionsList:

            controlOption = ControlOption(
                option["type"],
                self.x + 30,  # x 坐标保持不变
                currentY,  # 使用当前 y 坐标
                self.optionWidth,
                self.optionHeight,
                "white",  # 颜色默认白色
            )

            self.controlOptions.append(controlOption)

            currentY += (
                self.optionHeight + 5
            )  # 更新 y 坐标，增加当前 ControlOption 的高度和间距

    def draw(self, game: "Game") -> None:
        """绘制控制器"""
        for option in self.controlOptions:
            option.draw(game)
