from typing import Self


class Vector2:
    """二维向量类，提供基本向量运算和几何操作方法"""

    def __init__(self, x: float | tuple[float, float], y: float = None) -> None:

        if y is None:
            self.x: float = x[0]
            self.y: float = x[1]

        else:
            self.x: float = x
            self.y: float = y

    def __add__(self, other: Self) -> Self:
        """向量加法"""
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Self) -> Self:
        """向量减法"""
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, number: float) -> Self:
        """向量数乘"""
        return Vector2(self.x * number, self.y * number)

    def __rmul__(self, number: float) -> Self:
        """向量数乘 (反向)
        
        实现标量在左侧的乘法，例如: 3 * vector
        """
        return self.__mul__(number)

    def __truediv__(self, number: float) -> Self:
        """向量数除"""
        return Vector2(self.x / number, self.y / number)

    def __neg__(self) -> Self:
        """向量取反"""
        return Vector2(-self.x, -self.y)

    def __abs__(self) -> float:
        """向量长度"""
        return (self.x**2 + self.y**2) ** 0.5

    def magnitude(self) -> float:
        """返回向量长度"""
        return abs(self)

    def zero(self) -> Self:
        """将向量置零"""
        self.x = 0
        self.y = 0
        return self

    def normalize(self) -> Self:
        """向量单位化"""
        length = abs(self)

        if length != 0:
            self.x /= length
            self.y /= length

        return self

    def dot(self, other: Self) -> float:
        """向量点积运算"""
        return self.x * other.x + self.y * other.y

    def distance(self, other: Self) -> float:
        """计算两点间欧氏距离"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def copy(self) -> Self:
        """返回向量副本"""
        return Vector2(self.x, self.y)

    def project(self, other: Self) -> Self:
        """计算当前向量在另一向量上的投影"""
        dot = self.x * other.x + self.y * other.y
        length = other.x**2 + other.y**2

        if length != 0:
            scalar = dot / length
        else:
            scalar = 0

        return Vector2(other.x * scalar, other.y * scalar)

    def projectVertical(self, other: Self) -> Self:
        """计算当前向量在垂直方向上的投影"""
        dot = self.x * other.x + self.y * other.y
        length = other.x**2 + other.y**2

        if length != 0:
            scalar = dot / length
        else:
            scalar = 0

        return Vector2(self.x - other.x * scalar, self.y - other.y * scalar)

    def vertical(self) -> Self:
        """返回当前向量的垂直向量"""
        return Vector2(-self.y, self.x)

    def toTuple(self) -> tuple[float, float]:
        """转换为元组形式"""
        return (self.x, self.y)


ZERO = Vector2(0, 0)


def triangleArea(p1: Vector2, p2: Vector2, p3: Vector2) -> float:
    """计算三角形面积"""
    return abs((p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y)) / 2)
