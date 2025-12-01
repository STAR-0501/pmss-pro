import time

import pygame
import json

from ..basic import *
from .input_box import *
from .option import *


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
        # 弹窗按钮区域（用于点击检测）
        self.modalOkRect: pygame.Rect | None = None

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
            text_value = str(option["value"]) if "value" in option else ""
            if option.get("type") == "electricCharge":
                try:
                    text_value = f"{float(option['value']):.1f}"
                except Exception:
                    text_value = str(option.get("value", ""))
            inputBox = InputBox(
                self.x + self.width * 0.35,
                y,
                self.width * 0.6,
                int(self.verticalSpacing * 0.65),
                option,
                self.target,
                text_value,
                int(self.verticalSpacing * 0.5 * 0.7),
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
        """更新输入框状态/处理弹窗事件"""
        # 若有 UI 弹窗，优先处理弹窗并阻断下层输入
        if getattr(game, "uiModal", None):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.modalOkRect and self.modalOkRect.collidepoint(event.pos):
                    game.uiModal = None
                    return
            if event.type == pygame.KEYDOWN and (
                event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE
            ):
                game.uiModal = None
                return
            # 其他事件直接吞掉
            return
        # 正常输入框事件
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

        try:
            for i in range(length):
                optionType = self.options[i]["type"]
                inputBox = self.inputBoxes[i]

                # 绘制选项文本（现代化配色）
                try:
                    optionText = self.font.render(
                        game.translation[optionType], True, (25, 25, 112))  # 午夜蓝
                except KeyError:
                    game.translation = json.load(open("config/translation.json", "r", encoding="utf-8"))
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
        except Exception as e:
            ...

        # 最后绘制 UI 弹窗（若存在），覆盖在最上面
        if getattr(game, "uiModal", None):
            self.drawModal(game)

    # 新增：关闭面板时一次性提交所有输入框中的值
    def commitAll(self, game: "Game") -> None:
        for box in self.inputBoxes:
            # 颜色字段尽量校验合法性，非法则忽略该项（保持原值）
            if box.option.get("type") == "color":
                try:
                    if box.text != "":
                        pygame.Color(box.text)
                    box.attrUpdate(box.target)
                except ValueError:
                    # 非法颜色输入，跳过提交
                    continue
            else:
                box.attrUpdate(box.target)

    # 新增：美化的 pygame 内置弹窗绘制
    def drawModal(self, game: "Game") -> None:
        modal = getattr(game, "uiModal", None)
        if not modal:
            return
        screen = game.screen
        sw, sh = screen.get_width(), screen.get_height()

        # 半透明遮罩
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # 弹窗尺寸与位置
        mw = min(int(sw * 0.5), 640)
        mh = min(int(sh * 0.3), 280)
        mx = (sw - mw) // 2
        my = (sh - mh) // 2

        # 阴影（深灰色半透明）
        shadow_rect = pygame.Rect(mx + 6, my + 6, mw, mh)
        shadow_surf = pygame.Surface((mw, mh), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (64, 64, 64, 80), pygame.Rect(0, 0, mw, mh), border_radius=16)
        screen.blit(shadow_surf, shadow_rect.topleft)

        # 主体
        bg = (255, 255, 255)
        border = (30, 144, 255)  # 道奇蓝
        body_rect = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(screen, bg, body_rect, border_radius=16)
        pygame.draw.rect(screen, border, body_rect, width=3, border_radius=16)

        # 标题与正文
        title = modal.get("title", "提示")
        message = modal.get("message", "")
        title_color = (25, 25, 112)  # 午夜蓝
        text_color = (25, 25, 112)
        title_font = getattr(game, "fontBig", self.font)
        msg_font = getattr(game, "fontSmall", self.font)

        title_surf = title_font.render(title, True, title_color)
        title_x = mx + (mw - title_surf.get_width()) // 2
        title_y = my + 32  # 下移标题
        screen.blit(title_surf, (title_x, title_y))

        # 文本换行渲染
        def wrap_text(txt: str, font: pygame.font.Font, max_width: int) -> list[str]:
            lines: list[str] = []
            for raw_line in txt.split("\n"):
                words = list(raw_line)
                buffer = ""
                for ch in words:
                    trial = buffer + ch
                    if font.render(trial, True, text_color).get_width() <= max_width:
                        buffer = trial
                    else:
                        if buffer:
                            lines.append(buffer)
                        buffer = ch
                lines.append(buffer)
            return lines

        text_area_w = mw - 48
        msg_lines = wrap_text(message, msg_font, text_area_w)
        ty = my + 96  # 下移正文起始位置
        for line in msg_lines:
            surf = msg_font.render(line, True, text_color)
            line_x = mx + (mw - surf.get_width()) // 2
            screen.blit(surf, (line_x, ty))
            ty += surf.get_height() + 8  # 略增行距

        # 确定按钮
        btn_w, btn_h = 120, 44
        btn_x = mx + (mw - btn_w) // 2
        btn_y = my + mh - btn_h - 18
        self.modalOkRect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        mouse_pos = pygame.mouse.get_pos()
        hovered = self.modalOkRect.collidepoint(mouse_pos)
        btn_bg = (65, 105, 225) if not hovered else (72, 118, 255)  # 皇家蓝/亮
        pygame.draw.rect(screen, btn_bg, self.modalOkRect, border_radius=12)
        pygame.draw.rect(screen, border, self.modalOkRect, width=2, border_radius=12)
        ok_surf = msg_font.render("确定", True, (255, 255, 255))
        screen.blit(
            ok_surf,
            (self.modalOkRect.centerx - ok_surf.get_width() // 2,
             self.modalOkRect.centery - ok_surf.get_height() // 2),
        )
