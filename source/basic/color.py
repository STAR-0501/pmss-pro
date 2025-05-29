import pygame


def colorStringToTuple(color: str) -> tuple[int, int, int]:
    """颜色字符串转RGB元组"""

    # 如果是颜色名称格式，先转换为pygame颜色对象获取RGB值
    if not color.startswith("#"):

        try:
            color_ = pygame.Color(color.lower())
            return (color_.r, color_.g, color_.b)

        except ValueError:
            # 如果颜色名称无效，返回默认黑色
            return (0, 0, 0)

    # 处理十六进制字符串格式
    return tuple(int(color[i: i + 2], 16) for i in (1, 3, 5))


def colorTupleToString(color: tuple[int, int, int]) -> str:
    """RGB元组转颜色字符串"""
    return "#%02x%02x%02x" % color


def colorMiddle(
    color1: tuple[int, int, int] | str,
    color2: tuple[int, int, int] | str,
    factor: float = 0.5,
) -> tuple[int, int, int]:
    """计算平均颜色"""

    if isinstance(color1, str):
        color1 = colorStringToTuple(color1)

    if isinstance(color2, str):
        color2 = colorStringToTuple(color2)

    return (
        int(color1[0] * factor + color2[0] * (1 - factor)),
        int(color1[1] * factor + color2[1] * (1 - factor)),
        int(color1[2] * factor + color2[2] * (1 - factor)),
    )


def colorOpposite(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """计算反转颜色"""
    return (255 - color[0], 255 - color[1], 255 - color[2])


def colorSuitable(
    color1: tuple[int, int, int] | str, color2: tuple[int, int, int] | str
) -> tuple[int, int, int]:
    """计算合适颜色"""
    return colorOpposite(colorMiddle(color1, color2))
