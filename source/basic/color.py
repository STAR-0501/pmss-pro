from __future__ import annotations

import pygame

# Type alias for RGB color tuples
ColorType = tuple[int, int, int]


def colorStringToTuple(color: str) -> ColorType:
    """将颜色字符串转换为RGB元组。

    支持两种格式：
    - 颜色名称: 'red', 'blue', 'lightgrey' 等
    - 十六进制: '#FF0000', '#00FF00' 等

    Args:
        color: 颜色字符串。

    Returns:
        (R, G, B) 元组，取值范围 0-255。
        无效颜色名称返回黑色 (0, 0, 0)。
    """
    if not color.startswith("#"):
        try:
            color_obj = pygame.Color(color.lower())
            return (color_obj.r, color_obj.g, color_obj.b)
        except ValueError:
            return (0, 0, 0)

    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


def colorTupleToString(color: ColorType) -> str:
    """将RGB元组转换为十六进制颜色字符串。

    Args:
        color: (R, G, B) 元组。

    Returns:
        格式为 '#RRGGBB' 的颜色字符串。
    """
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def colorMiddle(
    color1: ColorType | str,
    color2: ColorType | str,
    factor: float = 0.5,
) -> ColorType:
    """计算两种颜色的混合（平均）颜色。

    Args:
        color1: 第一种颜色（RGB元组或颜色字符串）。
        color2: 第二种颜色（RGB元组或颜色字符串）。
        factor: 混合因子，0.0 表示完全使用 color2，1.0 表示完全使用 color1。

    Returns:
        混合后的 (R, G, B) 元组。
    """
    if isinstance(color1, str):
        color1 = colorStringToTuple(color1)

    if isinstance(color2, str):
        color2 = colorStringToTuple(color2)

    return (
        int(color1[0] * factor + color2[0] * (1 - factor)),
        int(color1[1] * factor + color2[1] * (1 - factor)),
        int(color1[2] * factor + color2[2] * (1 - factor)),
    )


def colorOpposite(color: ColorType) -> ColorType:
    """计算RGB颜色的反色。

    Args:
        color: (R, G, B) 元组。

    Returns:
        反色 (R', G', B') 元组，每个分量为 255 - 原分量。
    """
    return (255 - color[0], 255 - color[1], 255 - color[2])


def colorSuitable(color1: ColorType | str, color2: ColorType | str) -> ColorType:
    """计算与两种颜色的对比色都较合适的颜色。

    等价于取 colorMiddle 的反色。

    Args:
        color1: 第一种颜色（RGB元组或颜色字符串）。
        color2: 第二种颜色（RGB元组或颜色字符串）。

    Returns:
        合适对比的 (R, G, B) 元组。
    """
    return colorOpposite(colorMiddle(color1, color2))


# Predefined common colors as RGB tuples
COLOR_BLACK: ColorType = (0, 0, 0)
COLOR_WHITE: ColorType = (255, 255, 255)
COLOR_RED: ColorType = (255, 0, 0)
COLOR_GREEN: ColorType = (0, 255, 0)
COLOR_BLUE: ColorType = (0, 0, 255)
COLOR_GREY: ColorType = (128, 128, 128)
COLOR_LIGHTGREY: ColorType = (211, 211, 211)
