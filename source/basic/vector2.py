from __future__ import annotations

import math


class Vector2:
    """二维向量类，提供基本向量运算和几何操作方法"""

    def __init__(self, x: 'Vector2 | tuple | float | int',
                 y: float | int | None = None) -> None:
        if isinstance(x, Vector2):
            self.x = float(x.x)
            self.y = float(x.y)
        elif y is None:
            self.x = float(x[0])  # type: ignore[arg-type]
            self.y = float(x[1])  # type: ignore[arg-type]
        else:
            self.x = float(x)  # type: ignore[arg-type]
            self.y = float(y)

    @classmethod
    def from_tuple(cls, t: tuple[float, float] | tuple[int, int]) -> 'Vector2':
        """从元组创建Vector2"""
        return cls(float(t[0]), float(t[1]))

    def __add__(self, other: 'Vector2') -> 'Vector2':
        """向量加法"""
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2') -> 'Vector2':
        """向量减法"""
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, number: float) -> 'Vector2':
        """向量数乘"""
        return Vector2(self.x * number, self.y * number)

    def __rmul__(self, number: float) -> 'Vector2':
        """向量数乘 (反向)

        实现标量在左侧的乘法，例如: 3 * vector
        """
        return self.__mul__(number)

    def __truediv__(self, number: float) -> 'Vector2':
        """向量数除"""
        return Vector2(self.x / number, self.y / number)

    def __neg__(self) -> 'Vector2':
        """向量取反"""
        return Vector2(-self.x, -self.y)

    def __abs__(self) -> float:
        """向量长度"""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def __eq__(self, other: object) -> bool:
        """向量相等比较"""
        if not isinstance(other, Vector2):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __ne__(self, other: object) -> bool:
        """向量不等比较"""
        if not isinstance(other, Vector2):
            return NotImplemented
        return self.x != other.x or self.y != other.y

    def __repr__(self) -> str:
        return f"Vector2({self.x:.4f}, {self.y:.4f})"

    def __getitem__(self, index: int) -> float:
        """支持索引访问: v[0] == v.x, v[1] == v.y"""
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        raise IndexError("Vector2 index out of range")

    def magnitude(self) -> float:
        """返回向量长度"""
        return abs(self)

    def magnitude_squared(self) -> float:
        """返回向量长度的平方（避免开平方，用于性能敏感的比较）"""
        return self.x * self.x + self.y * self.y

    def zero(self) -> 'Vector2':
        """将向量置零"""
        self.x = 0.0
        self.y = 0.0
        return self

    def normalize(self) -> 'Vector2':
        """向量单位化（原地修改）"""
        length = abs(self)
        if length != 0:
            self.x /= length
            self.y /= length
        return self

    def normalized(self) -> 'Vector2':
        """返回单位化副本（不修改原向量）"""
        length = abs(self)
        if length == 0:
            return Vector2(0, 0)
        return Vector2(self.x / length, self.y / length)

    def dot(self, other: 'Vector2') -> float:
        """向量点积运算"""
        return self.x * other.x + self.y * other.y

    def cross(self, other: 'Vector2') -> float:
        """二维向量叉积运算（返回标量：z分量）

        计算 self × other 的叉积，结果为正表示 other 在 self 的逆时针方向。
        """
        return self.x * other.y - self.y * other.x

    def distance(self, other: 'Vector2') -> float:
        """计算两点间欧氏距离"""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def distance_squared(self, other: 'Vector2') -> float:
        """计算两点间欧氏距离的平方（避免开平方，用于比较操作）"""
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def copy(self) -> 'Vector2':
        """返回向量副本"""
        return Vector2(self.x, self.y)

    def project(self, other: 'Vector2') -> 'Vector2':
        """计算当前向量在另一向量上的投影"""
        length_sq = other.x * other.x + other.y * other.y
        if length_sq == 0:
            return Vector2(0, 0)
        dot = self.x * other.x + self.y * other.y
        scalar = dot / length_sq
        return Vector2(other.x * scalar, other.y * scalar)

    def projectVertical(self, other: 'Vector2') -> 'Vector2':
        """计算当前向量在垂直方向上的投影"""
        length_sq = other.x * other.x + other.y * other.y
        if length_sq == 0:
            return Vector2(0, 0)
        dot = self.x * other.x + self.y * other.y
        scalar = dot / length_sq
        return Vector2(self.x - other.x * scalar, self.y - other.y * scalar)

    def vertical(self) -> 'Vector2':
        """返回当前向量的垂直向量"""
        return Vector2(-self.y, self.x)

    def lerp(self, target: 'Vector2', t: float) -> 'Vector2':
        """线性插值"""
        return Vector2(
            self.x + (target.x - self.x) * t,
            self.y + (target.y - self.y) * t,
        )

    def toTuple(self) -> tuple[float, float]:
        """转换为浮点数元组"""
        return (self.x, self.y)

    def toIntTuple(self) -> tuple[int, int]:
        """转换为整数元组（用于屏幕坐标等场景）"""
        return (int(self.x), int(self.y))

    @staticmethod
    def from_angle(angle_rad: float, length: float = 1.0) -> 'Vector2':
        """从角度和长度创建向量"""
        return Vector2(math.cos(angle_rad) * length, math.sin(angle_rad) * length)


ZERO = Vector2(0, 0)


def triangleArea(p1: Vector2, p2: Vector2, p3: Vector2) -> float:
    """计算三角形面积"""
    return abs((p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y)) / 2)
