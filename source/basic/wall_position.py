from .vector2 import *
from .wall import *


class WallPosition:
    """墙体位置类，储存墙体上某一点的相对位置"""

    def __init__(self, wall: Wall, position: Vector2) -> None:
        self.wall: Wall = wall
        self.position: Vector2 = position

        self.deltaPosition = self.position - wall.position

        self.x = wall.position.x + position.x
        self.y = wall.position.y + position.y
        
        self.id = randint(0, 100000000)

    def getPosition(self) -> Vector2:
        """获取墙体位置"""
        return self.deltaPosition + self.wall.position

    def update(self) -> None:
        """更新位置"""
        self.x = self.wall.position.x + self.deltaPosition.x
        self.y = self.wall.position.y + self.deltaPosition.y
        self.position = self.getPosition()
