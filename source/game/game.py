
import json
import multiprocessing
import os
import sys
import threading
import time
import pickle
from typing import TYPE_CHECKING

import pygame

from shared_game_state import SharedGameState

from ..basic import *
from .element_controller import *
from .input_menu import *
from .menu import *
from .set_caps_lock import *
from .settings_button import *

if TYPE_CHECKING:
    from ..core.ai_thread_loop import AIThreadLoop


class Game:
    """物理运动模拟系统主游戏类"""

    def __init__(self) -> None:
        os.environ["SDL_WINDOWS_DPI_AWARENESS"] = "permonitorv2"
        pygame.init()
        self.isPaused: bool = False
        self.isElementCreating: bool = False
        self.isMoving: bool = False
        self.isScreenMoving: bool = False
        self.isMassSetting: bool = False
        self.isCircularVelocityGetting: bool = False
        self.isCircularVelocityDirectionAnticlockwise: bool = True
        self.isCtrlPressing: bool = False
        self.isEditing: bool = False
        self.isElementControlling: bool = False
        self.isPressed: bool = False
        self.isDragging: bool = False
        self.isCelestialBodyMode: bool = False
        self.isModeChangingNaturally: bool = False
        self.isChatting: bool = False
        self.icon: str = ""
        self.gameName: str = "未命名"

        try:
            with open("config/screenSize.txt", "r", encoding="utf-8") as f:
                self.screenSize: list[int, int] = [
                    int(i.replace(" ", "")) for i in f.read().split("x")
                ]

        except Exception:
            self.screenSize: list[int, int] = [0, 0]

        self.screen: pygame.Surface = pygame.display.set_mode(
            size=(self.screenSize[0], self.screenSize[1]
                  ), flags=pygame.FULLSCREEN
        )
        print(
            f"\n屏幕大小：{self.screen.get_width()} x {self.screen.get_height()}\n")
        pygame.display.set_caption("Physics Motion Simulation System Pro")
        icon: pygame.Surface = pygame.image.load(
            "static/python.png").convert_alpha()
        pygame.display.set_icon(icon)

        self.mousePos: tuple[int, int] = (0, 0)  # 鼠标屏幕坐标，而非真实坐标
        self.fontSmall: pygame.font.Font = pygame.font.Font(
            "static/HarmonyOS_Sans_SC_Medium.ttf", int(
                self.screen.get_width() / 125)
        )
        self.fontBig: pygame.font.Font = pygame.font.Font(
            "static/HarmonyOS_Sans_SC_Medium.ttf", int(
                self.screen.get_width() / 75)
        )
        self.ratio: int = 5
        self.lastRatio: int = self.ratio
        self.minLimitRatio: int = 1
        self.maxLimitRatio: int = 15
        self.x: int = self.screen.get_width() / 2 / self.ratio
        self.y: int = self.screen.get_height() / self.ratio
        self.lastX: int = self.x
        self.lastY: int = 2e7
        self.elementMenu: Menu = None
        self.exampleMenu: Menu = None
        self.currentTime: float = time.time()
        self.lastTime: float = self.currentTime
        self.lastLoadTime: float = 0  # 上次加载预设的时间，用于防止连续按键延迟叠加
        self.tipDisplayEndTime: float = 0  # 提示文字显示结束时间
        self.loadedTipText = None  # 当前显示的提示文字
        self.loadedTipRect = None  # 当前显示的提示文字位置
        self.fpsAverage: float = 0
        self.fpsMinimum: float = 0
        self.rightMove: int = 0
        self.upMove: int = 0
        self.speed: int = 1
        self.circularVelocityFactor: float = 1
        self.floor: Wall = Wall(
            [
                Vector2(0, -10),
                Vector2(self.screen.get_width(), -10),
                Vector2(self.screen.get_width(), self.screen.get_height()),
                Vector2(0, self.screen.get_height()),
            ],
            (200, 200, 200),
            True,
        )
        self.isFloorIllegal: bool = False
        self.background: str | pygame.Color = "lightgrey"
        self.settingsButton: SettingsButton = SettingsButton(0, 0, 50, 50)
        self.fpsSaver: list[float] = []
        self.tempFrames: int = 0
        
        # 多进程通信队列（用于向投影显示进程发送数据）
        self.projection_queue: multiprocessing.Queue = None
        self.shared_state = None
        self.optionsList: list[dict] = []
        self.environmentOptions: list[dict] = []
        self.elements: dict[str, list[Element | Ball | Wall | Rope]] = {}
        self.wall_positions: list[WallPosition] = []
        
        self.groundElements: dict[str, list[Element | Ball | Wall | Rope]] = {
            "all": [],
            "ball": [],
            "wall": [],
            "rope": [],
            "controlling": [],
        }

        self.celestialElements: dict[str, list[Element | Ball | Wall | Rope]] = {
            "all": [],
            "ball": [],
            "wall": [],
            "rope": [],
            "controlling": [],
        }

        self.translation: dict[str, str] = {}
        self.inputMenu: InputMenu = None

        with open("config/elementOptions.json", "r", encoding="utf-8") as f:
            self.optionsList = json.load(f)

        for i in range(len(self.optionsList)):
            self.groundElements[self.optionsList[i]["type"]] = []
            self.celestialElements[self.optionsList[i]["type"]] = []

        self.elements = self.groundElements

        with open("config/environmentOptions.json", "r", encoding="utf-8") as f:
            self.environmentOptions = json.load(f)

        self.environmentOptionsCopy = self.environmentOptions.copy()

        with open("config/translation.json", "r", encoding="utf-8") as f:
            self.translation = json.load(f)

        self.inputMenu = InputMenu(
            Vector2(self.screen.get_width() / 2, self.screen.get_height() / 2),
            self,
            self,
        )
        self.inputMenu.options = self.environmentOptions
        self.inputMenu.update(self)

        self.test()

    

    def getPresetFileByIndex(self, index: int) -> str:
        """根据索引获取按字典序排序的预设文件名"""
        try:
            default_dir = "savefile/default"
            if not os.path.exists(default_dir):
                return None
            
            # 获取所有.json文件并按字典序排序
            json_files = []
            for file in os.listdir(default_dir):
                if file.endswith('.json'):
                    json_files.append(file)
            
            json_files.sort()  # 字典序排序
            
            # 索引从1开始，转换为数组索引
            if 1 <= index <= len(json_files):
                # 返回不带.json后缀的文件名，因为loadPreset会自动添加
                filename = json_files[index - 1]
                if filename.endswith('.json'):
                    filename = filename[:-5]  # 移除.json后缀
                return f"default/{filename}"
            
            return None
        except Exception:
            return None

    def exit(self) -> None:
        """退出游戏并取消大写锁定"""
        if not self.isChatting:
            setCapsLock(False)
            self.savePreset("autosave")
            print("\n游戏退出")
            pygame.quit()
            sys.exit()

    def test(self) -> None:
        """测试方法（预留）"""
        ...

    def handleMouseWheel(self, wheel_y: int, speed: float) -> None:
        """处理鼠标滚轮缩放"""
        if wheel_y == 1 and self.ratio < self.maxLimitRatio:
            if not self.isCtrlPressing:
                bx = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                by = self.screenToReal(pygame.mouse.get_pos()[1], self.y)

                self.ratio *= speed

                nx = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                ny = self.screenToReal(pygame.mouse.get_pos()[1], self.y)

                self.x += nx - bx
                self.y += ny - by
            else:
                bx = self.screenToReal(self.screen.get_width() / 2, self.x)
                by = self.screenToReal(self.screen.get_height() / 2, self.y)

                self.ratio *= speed

                nx = self.screenToReal(self.screen.get_width() / 2, self.x)
                ny = self.screenToReal(self.screen.get_height() / 2, self.y)

                self.x += nx - bx
                self.y += ny - by
        elif wheel_y == -1 and self.ratio > self.minLimitRatio:
            if not self.isCtrlPressing:
                bx = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                by = self.screenToReal(pygame.mouse.get_pos()[1], self.y)

                self.ratio /= speed

                nx = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                ny = self.screenToReal(pygame.mouse.get_pos()[1], self.y)

                self.x += nx - bx
                self.y += ny - by
            else:
                bx = self.screenToReal(self.screen.get_width() / 2, self.x)
                by = self.screenToReal(self.screen.get_height() / 2, self.y)

                self.ratio /= speed

                nx = self.screenToReal(self.screen.get_width() / 2, self.x)
                ny = self.screenToReal(self.screen.get_height() / 2, self.y)

                self.x += nx - bx
                self.y += ny - by

    def undoLastElement(self) -> None:
        """撤销上一个添加的元素（Ctrl+Z）"""
        if len(self.elements["all"]) > 0:
            lastElement = self.elements["all"][-1]
            self.elements["all"].remove(lastElement)

            for ball in self.elements["ball"]:
                ball.displayedAcceleration = (
                    ball.acceleration
                    + (ball.displayedAcceleration - ball.acceleration)
                    * ball.displayedAccelerationFactor
                )
                ball.displayedAccelerationFactor = 1

            for option in self.elementMenu.options:
                if option.type == lastElement.type:
                    self.elements[option.type].remove(lastElement)
                    break

    def showLoadedTip(self, filename: str) -> None:
        """显示加载游戏成功提示"""
        current_time = time.time()
        if current_time - self.lastLoadTime < 0.5:
            return
            
        self.loadPreset(filename)
        self.loadedTipText = self.fontSmall.render(
            f"{self.gameName} 加载成功", True, (0, 0, 0)
        )
        self.loadedTipRect = self.loadedTipText.get_rect(
            center=(
                self.screen.get_width() / 2,
                self.screen.get_height() / 2,
            )
        )
        self.tipDisplayEndTime = current_time + 1.5  # 显示1.5秒
        self.lastLoadTime = current_time
        self.lastTime = time.time()
        self.currentTime = time.time()

  
    def savePreset(self, filename: str = "autosave", iconPath: str = None) -> None:
        """保存预设数据"""
        for elementOption in self.elementMenu.options:
            elementOption.highLighted = False

        # # 创建一个新的字典，用于存储可序列化的属性
        # serializableDict = {"gameName": f"{int(time.time())}备份"}

        # serializableDict = {               #做预设用的
        #     "gameName" : f"单摆",
        #     "icon" : "static/simplePendulum.png"
        # }

        # # freeFall flatToss idealBevel basketball easterEgg

        # # 遍历 self.__dict__，排除不可序列化的对象
        # for attr, value in self.__dict__.items():
        #     if (
        #         attr != "screen"
        #         and attr != "fpsSaver"
        #         and attr != "icon"
        #         and attr != "gameName"
        #     ):
        #         try:
        #             # 尝试序列化对象，如果成功则添加到 serializableDict 中
        #             pickle.dumps(value)
        #             serializableDict[attr] = value

        #         except (pickle.PicklingError, TypeError):
        #             # 如果序列化失败，跳过该属性
        #             ...

        wall_positions_data = []
        # print(self.elements)
        for rope in self.elements["rope"]:
            if isinstance(rope.start, WallPosition):
                wall_positions_data.append({
                    "id": rope.start.id,
                    "wall_id": rope.start.wall.id,
                    "pos": [rope.start.position.x, rope.start.position.y],
                })
                
            if isinstance(rope.end, WallPosition):
                wall_positions_data.append({
                    "id": rope.end.id,
                    "wall_id": rope.end.wall.id,
                    "pos": [rope.end.deltaPosition.x, rope.end.deltaPosition.y],
                })

        # 保存物理元素
        elements_data = {}
        for element_type, elements in self.elements.items():
            if element_type != "controlling":
                elements_data[element_type] = []
                for element in elements:
                    if hasattr(element, 'to_dict'):
                        elements_data[element_type].append(element.to_dict())
                    else:
                        # 基本元素的序列化
                        element_data = {
                            'type': element.type,
                            'position': [element.position.x, element.position.y] if hasattr(element, 'position') else None
                        }
                        


                        # 添加球体特殊属性
                        if element.type == 'ball':
                            element_data.update({
                                'id': element.id,
                                'mass': element.mass,
                                'radius': element.radius,
                                'color': str(element.color) if hasattr(element, 'color') else 'black',
                                'velocity': [element.velocity.x, element.velocity.y],
                                'acceleration': [element.acceleration.x, element.acceleration.y]
                            })
                        # 添加墙体特殊属性
                        elif element.type == 'wall':
                            element_data.update({
                                'id': getattr(element, 'id', element.id),
                                'vertexes': [[v.x, v.y] for v in getattr(element, 'vertexes', [])],
                                'isLine': getattr(element, 'isLine', False),
                                'collisionFactor': getattr(element, 'collisionFactor', 1.0),
                                'color': str(element.color) if hasattr(element, 'color') else 'blue'
                            })

                        # 添加绳索特殊属性
                        elif element.type == 'rope':
                            # 处理WallPosition的保存
                            if hasattr(element, 'start') and hasattr(element.start, 'wallPosition'):
                                element_data['start_id'] = element.start.wallPosition.id
                            if hasattr(element, 'end') and hasattr(element.end, 'wallPosition'):
                                element_data['end_id'] = element.end.wallPosition.id
                            
                            element_data.update({
                                'id': element.id,
                                'start_id': element.start.id,
                                'end_id': element.end.id,
                                'length': element.length,
                                'width': getattr(element, 'width', 1),
                                'collisionFactor': getattr(element, 'collisionFactor', 1.0),
                                'tensionStiffness': getattr(element, 'tensionStiffness', 5000.0),
                                'dampingFactor': getattr(element, 'dampingFactor', 0.2),
                                'color': str(element.color) if hasattr(element, 'color') else 'red'
                            })

                        # 添加WallPosition属性
                        elif hasattr(element, 'wallPosition'):
                            element_data['wallPosition'] = {
                                'id': element.wallPosition.id,
                                'position': [element.wallPosition.position.x, element.wallPosition.position.y],
                                'wall_id': element.wallPosition.wall.id,
                                'deltaPosition': [element.wallPosition.deltaPosition.x, element.wallPosition.deltaPosition.y]
                            }

                        # 添加弹簧特殊属性
                        elif element.type == 'spring':
                            element_data.update({
                                'id': getattr(element, 'id', element.id),
                                'start_id': element.start.id,
                                'end_id': element.end.id,
                                'restLength': getattr(element, 'restLength', getattr(element, 'length', 100)),
                                'stiffness': getattr(element, 'stiffness', getattr(element, 'k', 1)),
                                'width': getattr(element, 'width', 3),
                                'dampingFactor': getattr(element, 'dampingFactor', 0.1),
                                'color': str(element.color) if hasattr(element, 'color') else 'green'
                            })
                        # 添加轻杆特殊属性
                        elif element.type == 'rod':
                            element_data.update({
                                'id': getattr(element, 'id', id(element)),
                                'start_id': id(element.start),
                                'end_id': id(element.end),
                                'length': getattr(element, 'restLength', 100),
                                'width': getattr(element, 'width', 3),
                                'dampingFactor': getattr(element, 'dampingFactor', 0.1),
                                'stiffness': getattr(element, 'stiffness', 100000.0),
                                'color': str(element.color) if hasattr(element, 'color') else 'blue'
                            })
                        # 添加显示信息和跟随状态属性
                        element_data.update({
                            'isShowingInfo': getattr(element, 'isShowingInfo', False),
                            'infoText': getattr(element, 'infoText', None),
                            'isFollowing': getattr(element, 'isFollowing', False)
                        })
                        elements_data[element_type].append(element_data)

        data = {
            "name": filename,
            "icon": self.icon,
            "icon": iconPath,
            "attributes": {},
            "elements": elements_data,
            "wall_position": wall_positions_data
        }
        
        # 保存基本属性（排除复杂对象）
        for key, value in self.__dict__.items():
            # print(key, value)
            if isinstance(value, (int, float, str, list, tuple, dict)) and key not in ["fpsSaver", "elements", "groundElements", "celestialElements", "screen", "projection_queue", "wall_positions"]:
                data["attributes"][key] = value
                
        # print(json.dumps(data, ensure_ascii=False, indent=4))

        os.makedirs("savefile", exist_ok=True)

        # 将可序列化的字典保存到文件
        with open(f"savefile/{filename}.json", "w", encoding="utf-8") as f:
            # print(data)
            json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"\n预设数据保存成功：{filename}.json")
            f.close()


    def loadPreset(self, filename: str = "autosave") -> None:
        """加载预设，优先使用 JSON"""
        # 运行时必须保留的对象
        currentScreen = getattr(self, "screen", None)
        currentExampleMenu = getattr(self, "exampleMenu", None)
        currentElementMenu = getattr(self, "elementMenu", None)
        currentFloor = getattr(self, "floor", None)
        

        json_path = f"savefile/{filename}.json"

        try:
            # 读取数据
            if os.path.exists(json_path):
                print(f"\n正在加载预设数据：{filename}.json")
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    attributes = data.get("attributes", {})
                    self.name = data.get("name", "default")
                    self.icon = data.get("icon", "static/default.png")
                    elements_data = data.get("elements", {})
                    wall_position_data = data.get("wall_position", [])
                    
                    # 清空现有元素
                    for element_list in self.elements.values():
                        element_list.clear()
                    
                    # 恢复基本属性
                    self.__dict__.update(attributes)
                    # 确保ratio正确应用
                    if hasattr(self, 'ratio') and self.ratio > 0:
                        self.lastRatio = self.ratio
                    
                    # 恢复物理元素
                    from ..basic.ball import Ball
                    from ..basic.rod import Rod
                    from ..basic.rope import Rope
                    from ..basic.spring import Spring
                    from ..basic.vector2 import Vector2
                    from ..basic.wall import Wall
                    from ..basic.wall_position import WallPosition


                    # 重新创建球体
                    for ball_data in elements_data.get("ball", []):
                        ball = Ball(
                            Vector2(ball_data["position"][0], ball_data["position"][1]),
                            ball_data["radius"],
                            ball_data["color"],
                            ball_data["mass"],
                            Vector2(ball_data["velocity"][0], ball_data["velocity"][1]),
                            []
                        )
                        ball.acceleration = Vector2(ball_data["acceleration"][0], ball_data["acceleration"][1])
                        ball.isShowingInfo = ball_data.get("isShowingInfo", False)
                        ball.isFollowing = ball_data.get("isFollowing", False)
                        # print(ball_data["id"])
                        ball.id = ball_data["id"]
                        self.elements["ball"].append(ball)
                        self.elements["all"].append(ball)
                    
                    # 重新创建墙体（支持新旧两种格式）
                    for wall_data in elements_data.get("wall", []):
                        color = wall_data.get("color", "blue")
                        if "vertexes" in wall_data and isinstance(wall_data["vertexes"], list) and len(wall_data["vertexes"]) >= 4:
                            vertexes = [Vector2(v[0], v[1]) for v in wall_data["vertexes"]]
                            isLine = wall_data.get("isLine", False)
                            wall = Wall(vertexes, color, isLine)
                        elif "start" in wall_data and "end" in wall_data:
                            # 兼容旧数据：根据起止点构造一条极细的墙体
                            start = Vector2(wall_data["start"][0], wall_data["start"][1])
                            end = Vector2(wall_data["end"][0], wall_data["end"][1])
                            direction = end - start
                            thickness = 1.0
                            if abs(direction) == 0:
                                # 退化为一个很小的方形
                                half = thickness / 2
                                vertexes = [
                                    Vector2(start.x - half, start.y - half),
                                    Vector2(start.x + half, start.y - half),
                                    Vector2(start.x + half, start.y + half),
                                    Vector2(start.x - half, start.y + half),
                                ]
                            else:
                                normal = Vector2(-direction.y, direction.x)
                                normal.normalize()
                                offset = normal * (thickness / 2)
                                vertexes = [
                                    start + offset,
                                    end + offset,
                                    end - offset,
                                    start - offset,
                                ]
                            wall = Wall(vertexes, color, True)
                        else:
                            # 数据不完整，跳过
                            continue
                        if 'id' in wall_data:
                            wall.id = wall_data['id']
                        self.elements["wall"].append(wall)
                        self.elements["all"].append(wall)

                    # wallPosition
                    for wall_position in wall_position_data:
                        for wall in self.elements["wall"]:
                            if wall.id == wall_position["wall_id"]:
                                break
                        wallPosition = WallPosition(
                            wall,
                            Vector2(wall_position["pos"][0] + wall.position.x, wall_position["pos"][1] + wall.position.y),
                        )
                        wallPosition.id = wall_position["id"]
                        wallPosition.deltaPosition = Vector2(wall_position["pos"][0], wall_position["pos"][1])

                        self.wall_positions.append(wallPosition)
                        
                    
                    # 创建元素ID映射表
                    # element_map = {}
                    # for element in self.elements["all"]:
                    #     if hasattr(element, 'id'):
                    #         element_map[element.id] = element
                    
                    # 重新创建绳索（需要连接已创建的球体或墙体）
                    # print(self.wall_positions[0].id)
                    for rope_data in elements_data.get("rope", []):
                        start_id = rope_data.get("start_id") or rope_data.get("obj1_id")
                        end_id = rope_data.get("end_id") or rope_data.get("obj2_id")
                        
                        for element in self.elements["all"]:
                            if hasattr(element, 'id') and element.id == start_id:
                                start = element
                                # print("start", start.id)
                            if hasattr(element, 'id') and element.id == end_id:
                                end = element
                                # print("end", end.id)
                        
                        # print(start_id, end_id)
                        # print(self.wall_positions[0].id)
                        # print(start_id)
                        # print(end_id)
                        for wall_position in self.wall_positions:
                            if wall_position.id == start_id:
                                start = wall_position
                                # print("start", start.id) 
                            if wall_position.id == end_id:
                                end = wall_position
                                # print("end", end.id)

                        # print("start", start.id)
                        # print("end", end)

                        # 如果找到两个对象，创建绳索
                        if start and end:
                            rope = Rope(
                                start,
                                end,
                                rope_data.get("length", 100),
                                rope_data.get("width", 1),
                                rope_data.get("color", "red"),
                                rope_data.get("collisionFactor", 1.0),
                                rope_data.get("tensionStiffness", 5000.0),
                                rope_data.get("dampingFactor", 0.2)
                            )
                            if 'id' in rope_data:
                                rope.id = rope_data['id']
                            self.elements["rope"].append(rope)
                            self.elements["all"].append(rope)
                    
                    # 重新创建弹簧
                    for spring_data in elements_data.get("spring", []):
                        start_id = spring_data.get("start_id") or spring_data.get("obj1_id")
                        end_id = spring_data.get("end_id") or spring_data.get("obj2_id")
                        
                        # 从映射表中查找对应的对象
                        start = element_map.get(start_id)
                        end = element_map.get(end_id)
                        
                        # 如果找到两个对象，创建弹簧
                        if start and end:
                            spring = Spring(
                                start,
                                end,
                                spring_data.get("restLength", spring_data.get("length", 100)),
                                spring_data.get("stiffness", spring_data.get("k", 1)),
                                spring_data.get("width", 3),
                                spring_data.get("color", "green"),
                                spring_data.get("dampingFactor", 0.1)
                            )
                            if 'id' in spring_data:
                                spring.id = spring_data['id']
                            self.elements["spring"].append(spring)
                            self.elements["all"].append(spring)
                    
                    # 重新创建轻杆
                    for rod_data in elements_data.get("rod", []):
                        start_id = rod_data.get("start_id") or rod_data.get("obj1_id")
                        end_id = rod_data.get("end_id") or rod_data.get("obj2_id")
                        
                        # 从映射表中查找对应的对象
                        start = element_map.get(start_id)
                        end = element_map.get(end_id)
                        
                        # 如果找到两个对象，创建轻杆
                        if start and end:
                            rod = Rod(
                                start,
                                end,
                                rod_data.get("length", 100),
                                rod_data.get("width", 3),
                                rod_data.get("color", "blue"),
                                rod_data.get("dampingFactor", 0.1),
                                rod_data.get("stiffness", 100000.0)
                            )
                            if 'id' in rod_data:
                                rod.id = rod_data['id']
                            self.elements["rod"].append(rod)
                            self.elements["all"].append(rod)

            else:
                print(f"\n未找到预设：{filename}.json")
                return

            # 恢复关键对象，避免引用丢失
            if currentScreen is not None:
                self.screen = currentScreen
            if currentExampleMenu is not None:
                self.exampleMenu = currentExampleMenu
            if currentElementMenu is not None:
                self.elementMenu.x = currentElementMenu.x
                self.elementMenu.y = currentElementMenu.y
                self.elementMenu.width = currentElementMenu.width
                self.elementMenu.height = currentElementMenu.height
                for i in range(len(currentElementMenu.options)):
                    self.elementMenu.options[i].x = currentElementMenu.options[i].x
                    self.elementMenu.options[i].y = currentElementMenu.options[i].y
                    self.elementMenu.options[i].width = currentElementMenu.options[i].width
                    self.elementMenu.options[i].height = currentElementMenu.options[i].height
            if currentFloor is not None:
                self.floor = currentFloor

            # 重置部分状态与时间戳
            self.rightMove = 0
            self.upMove = 0
            self.lastTime = time.time()
            self.currentTime = time.time()
            print("\n预设数据加载成功")
        except pygame.error as e:
            print(f"加载预设失败：{e}")

    def saveGame(self, filename: str = "autosave", iconPath: str | None = None) -> None:
        """对外统一的保存接口（JSON 格式）"""
        self.savePreset(filename, iconPath)

    def loadGame(self, filename: str = "autosave") -> None:
        """对外统一的读取接口，内部调用 loadPreset"""
        self.loadPreset(filename)

    def setAttr(self, key: str, value: str) -> None:
        """设置环境属性"""
        for option in self.environmentOptions:
            if option["type"] == key:
                option["value"] = value
                break

    def realToScreen(
        self, r: float | Vector2, x: float | Vector2 = None
    ) -> float | Vector2:
        """实际坐标转屏幕坐标"""
        if x is None:
            if isinstance(r, Vector2):
                x = ZERO
            else:
                x = 0

        return (r + x) * self.ratio

    def screenToReal(
        self, r: float | Vector2, x: float | Vector2 = None
    ) -> float | Vector2:
        """屏幕坐标转实际坐标"""
        if x is None:
            if isinstance(r, Vector2):
                x = ZERO
            else:
                x = 0

        return r / self.ratio - x

    def eventLoop(self) -> None:
        """事件处理主循环"""
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.exit()

            elif event.type == pygame.ACTIVEEVENT:

                if event.gain == 0 and event.state == 2:
                    setCapsLock(False)

                elif event.gain == 1 and event.state == 1:
                    setCapsLock(True)

            if event.type == pygame.MOUSEBUTTONUP:
                self.mousePos = pygame.mouse.get_pos()

                if event.button == 1:

                    # createElement里会判定对应的按钮是否被点击，并生成对应的物体
                    for option in self.elementMenu.options:
                        option.createElement(self, Vector2(self.mousePos))

                    for option in self.exampleMenu.options:
                        option.createElement(self, Vector2(self.mousePos))

                if event.button == 3:
                    for option in self.elementMenu.options:
                        # edit里会判定对应的按钮是否被点击，并编辑对应的物体
                        option.edit(self, Vector2(self.mousePos))

            if event.type == pygame.MOUSEWHEEL:
                speed = 1.1
                self.handleMouseWheel(event.y, speed)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mousePos = pygame.mouse.get_pos()

                if (
                    event.button == 1
                    and not self.elementMenu.isMouseOn()
                    and not self.isElementCreating
                    and not self.isElementControlling
                    and not self.isEditing
                ):
                    self.isMoving = True
                    self.isScreenMoving = True

                    for element in self.elements["all"]:
                        if element.isMouseOn(self):
                            self.elements["controlling"].append(element)
                            self.isScreenMoving = False

                if event.button == 3 and not self.elementMenu.isMouseOn():
                    self.isElementControlling = True
                    for element in self.elements["all"]:
                        if element.isMouseOn(self):
                            element.highLighted = True
                            self.update()
                            pygame.display.update()
                            elementController = ElementController(
                                element, Vector2(self.mousePos)
                            )
                            while self.isElementControlling:
                                self.updateFPS()
                                elementController.update(self)
                                elementController.draw(self)

                                for event in pygame.event.get():

                                    if event.type == pygame.QUIT:
                                        self.exit()

                                    elif event.type == pygame.ACTIVEEVENT:

                                        if event.gain == 0 and event.state == 2:
                                            setCapsLock(False)

                                        elif event.gain == 1 and event.state == 1:
                                            setCapsLock(True)

                                    if event.type == pygame.KEYDOWN:

                                        if (
                                            event.key == pygame.K_z
                                            and self.isCtrlPressing
                                            and len(self.elements["all"]) > 0
                                        ):
                                            self.undoLastElement()

                                        if event.key == pygame.K_g:
                                            self.savePreset("manualsave")

                                        if event.key == pygame.K_l:
                                            self.loadPreset("autosave")

                                        if event.key == pygame.K_k:
                                            self.loadPreset("manualsave")

                                        if pygame.K_1 <= event.key <= pygame.K_9:
                                            preset_file = self.getPresetFileByIndex(event.key - pygame.K_0)
                                            if preset_file:
                                                self.showLoadedTip(preset_file)

                                        if event.key == pygame.K_r:
                                            self.elements["all"].clear()
                                            for option in self.elementMenu.options:
                                                self.elements[option.type].clear(
                                                )
                                            self.isElementControlling = False

                                        if (
                                            event.key == pygame.K_LCTRL
                                            or event.key == pygame.K_RCTRL
                                        ):
                                            self.isCtrlPressing = True

                                        if event.key == pygame.K_ESCAPE:
                                            self.isElementControlling = False

                                    if event.type == pygame.MOUSEBUTTONDOWN:

                                        if (
                                            not elementController.isMouseOn()
                                            or element.isMouseOn(self)
                                        ):
                                            self.isElementControlling = False
                                            element.highLighted = False

                                        if event.button == 1 or event.button == 3:
                                            elementController.control(self)
                                            self.isElementControlling = False

                                pygame.display.update()
                    self.isElementControlling = False

            if event.type == pygame.MOUSEMOTION:
                if self.isScreenMoving:

                    for element in self.elements["ball"]:
                        element.highLighted = False
                        element.isFollowing = False

                    self.x += self.screenToReal(
                        pygame.mouse.get_pos()[0] - self.mousePos[0]
                    )

                    if (
                        not self.isFloorIllegal
                        or self.screenToReal(
                            pygame.mouse.get_pos()[1] - self.mousePos[1]
                        )
                        > 0
                    ):
                        self.y += self.screenToReal(
                            pygame.mouse.get_pos()[1] - self.mousePos[1]
                        )

                    self.mousePos = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEBUTTONUP:

                if event.button == 1:

                    if self.settingsButton.isMouseOn():
                        self.openEditor(self.inputMenu)

                    self.isMoving = False
                    self.isScreenMoving = False
                    self.elements["controlling"].clear()

                if event.button == 2:
                    for element in self.elements["all"]:
                        if element.isMouseOn(self):
                            element.copy(self)
                            break

            if event.type == pygame.KEYDOWN:

                if (
                    event.key == pygame.K_z
                    and self.isCtrlPressing
                    and len(self.elements["all"]) > 0
                ):
                    self.undoLastElement()

                if event.key == pygame.K_SPACE:
                    self.isPaused = not self.isPaused

                if event.key == pygame.K_r:
                    self.elements["all"].clear()
                    for option in self.elementMenu.options:
                        self.elements[option.type].clear()

                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self.isCtrlPressing = True

                if event.key == pygame.K_m:
                    self.openEditor(self.inputMenu)

                if event.key == pygame.K_g:
                    self.savePreset("manualsave")

                if event.key == pygame.K_l:
                    self.loadPreset("autosave")

                if event.key == pygame.K_k:
                    self.loadPreset("manualsave")

                if pygame.K_1 <= event.key <= pygame.K_9:
                    # 防止连续按键时延迟叠加
                    current_time = time.time()
                    if current_time - self.lastLoadTime < 0.5:
                        continue
                    
                    preset_file = self.getPresetFileByIndex(event.key - pygame.K_0)
                    if preset_file:
                        self.loadPreset(preset_file)
                        self.loadedTipText = self.fontSmall.render(
                            f"{self.gameName} 加载成功", True, (0, 0, 0)
                        )
                        self.loadedTipRect = self.loadedTipText.get_rect(
                            center=(
                                self.screen.get_width() / 2,
                                self.screen.get_height() / 2,
                            )
                        )
                        self.tipDisplayEndTime = current_time + 1.5  # 显示1.5秒
                        self.lastLoadTime = current_time
                    self.lastTime = time.time()
                    self.currentTime = time.time()

                if event.key == pygame.K_p:
                    if self.isCelestialBodyMode:
                        for option in self.environmentOptions:

                            if option["type"] == "mode":
                                option["value"] = "0"

                            if option["type"] == "gravity":
                                option["value"] = "1"
                        # self.GroundSurfaceMode()
                    else:
                        for option in self.environmentOptions:

                            if option["type"] == "mode":
                                option["value"] = "1"

                            if option["type"] == "gravity":
                                option["value"] = "0"
                        # self.CelestialBodyMode()

                if event.key == pygame.K_ESCAPE:
                    for element in self.elements["ball"]:
                        element.highLighted = False
                        element.isFollowing = False

                # 测试 !!!
                if event.key == pygame.K_t:
                    rope = Rope(
                        self.elements["ball"][-2],
                        self.elements["ball"][-1],
                        self.elements["ball"][-2]
                        .getPosition()
                        .distance(self.elements["ball"][-1].getPosition()),
                        1,
                        "red",
                    )
                    # rope = Rope(
                    #     self.elements["ball"][-1],
                    #     WallPosition(self.elements["wall"][-1], ZERO),
                    #     self.elements["ball"][-1]
                    #     .getPosition()
                    #     .distance(WallPosition(self.elements["wall"][-1], ZERO)),
                    #     1,
                    #     "red",
                    # )
                    self.elements["all"].append(rope)
                    self.elements["rope"].append(rope)

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self.isCtrlPressing = False

            self.screenMove(event)

    def openEditor(self, inputMenu) -> None:
        """打开参数编辑器"""
        # 确保每次打开编辑器时，inputMenu.options都反映environmentOptions的最新状态
        # 使用深拷贝，避免直接修改environmentOptions
        # import copy
        # inputMenu.options = copy.deepcopy(self.environmentOptions)
        inputMenu.update(self)
        self.isEditing = True
        inputMenu.update(self)
        _editor_bg_snapshot = self.screen.copy()
        while self.isEditing:
            if _editor_bg_snapshot is not None:
                self.screen.blit(_editor_bg_snapshot, (0, 0))
            inputMenu.draw(self)
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()
                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.KEYDOWN:

                    if (
                        event.key == pygame.K_z
                        and self.isCtrlPressing
                        and len(self.elements["all"]) > 0
                    ):
                        self.undoLastElement()

                    if (
                        event.key == pygame.K_m
                        or event.key == pygame.K_ESCAPE
                        or event.key == pygame.K_RETURN
                    ):
                        # 在关闭面板前提交所有输入框的当前值
                        try:
                            inputMenu.commitAll(self)
                            # 将修改后的值更新回environmentOptions
                            # self.environmentOptions = copy.deepcopy(inputMenu.options)
                        except Exception:
                            ...
                        self.isEditing = False

                inputMenu.updateBoxes(event, self)
        # 兜底：若由输入框内部关闭编辑状态，退出循环后也再次提交一次
        try:
            inputMenu.commitAll(self)
            # 将修改后的值更新回environmentOptions
            # self.environmentOptions = copy.deepcopy(inputMenu.options)
        except Exception:
            ...
        self.updateFPS()

    def screenMove(self, event: pygame.event.Event) -> None:
        """处理屏幕移动控制"""
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_a:
                self.rightMove = 1

            if event.key == pygame.K_d:
                self.rightMove = -1

            if event.key == pygame.K_w:
                self.upMove = 1

            if event.key == pygame.K_s:
                if not self.isFloorIllegal:
                    self.upMove = -1

            if event.key == pygame.K_LEFT:
                if self.speed > 0.1:
                    self.speed -= 0.1

            if event.key == pygame.K_RIGHT:
                self.speed += 0.1

        if event.type == pygame.KEYUP:

            if event.key == pygame.K_a:
                self.rightMove = 0

            if event.key == pygame.K_d:
                self.rightMove = 0

            if event.key == pygame.K_w:
                self.upMove = 0

            if event.key == pygame.K_s:
                self.upMove = 0

    def updateScreen(self) -> None:
        """更新屏幕状态"""
        for option in self.environmentOptions:
            if option["type"] == "mode" and option["value"] != "":
                mode = float(option["value"])

                if mode == 0:
                    self.GroundSurfaceMode()
                elif mode == 1:
                    self.CelestialBodyMode()
            elif option["value"] == "":
                option["value"] = "0"

        self.x += self.rightMove
        self.y += self.upMove
        if (
            self.realToScreen(self.floor.vertexes[0].y, self.y)
            < self.screen.get_height() * 2 / 3
            and not self.isCelestialBodyMode
        ):
            self.isFloorIllegal = True
        else:
            self.isFloorIllegal = False

        # 恢复原版渲染逻辑
        self.renderOriginalGame()

    def renderOriginalGame(self) -> None:
        """渲染原版游戏画面"""
        # 清空屏幕
        self.screen.fill(self.background)
        
        # 绘制设置按钮
        self.settingsButton.draw(self)
        
        # 绘制所有物理元素
        for element in self.elements["all"]:
            element.draw(self)
        
        # 绘制地板（如果不是天体模式且地板合法）
        if not self.isCelestialBodyMode and not self.isFloorIllegal:
            self.floor.draw(self)
        
        # 绘制加载提示文字（如果在显示时间内）
        current_time = time.time()
        if (self.loadedTipText is not None and 
            self.loadedTipRect is not None and 
            current_time < self.tipDisplayEndTime):
            self.screen.blit(self.loadedTipText, self.loadedTipRect)
        elif current_time >= self.tipDisplayEndTime:
            # 清除过期的提示文字
            self.loadedTipText = None
            self.loadedTipRect = None
            
        # 如果有投影队列，发送当前画面数据到投影进程
        if self.projection_queue is not None:
            try:
                # 将surface转换为可序列化的格式
                screen_copy = self.screen.copy()
                surface_string = pygame.image.tostring(screen_copy, 'RGB')
                surface_size = screen_copy.get_size()
                surface_data = {
                    'data': surface_string,
                    'size': surface_size
                }
                
                if not self.projection_queue.full():
                    self.projection_queue.put_nowait(surface_data)
            except Exception as e:
                pass  # 忽略队列错误，继续游戏运行
    
    def setProjectionQueue(self, queue: multiprocessing.Queue) -> None:
        """设置投影显示队列"""
        self.projection_queue = queue

    def set_shared_state(self, state: SharedGameState) -> None:
        self.shared_state = state

    def updateMenu(self) -> None:
        """更新菜单界面"""
        width, height = self.screen.get_size()
        if self.elementMenu is None:
            with open("config/elementOptions.json", "r", encoding="utf-8") as filenames:
                self.elementMenu = Menu(
                    Vector2(width * 97 / 100, 0), json.load(filenames)
                )
        self.elementMenu.draw(game=self)

        if self.exampleMenu is None:
            examples = []
            for dirpath, dirnames, filenames in os.walk("savefile/default"):
                for file in filenames:

                    try:
                        with open(os.path.join(dirpath, file), "r", encoding="utf-8") as tempFile:
                            data = json.load(tempFile)

                        # 尝试从attributes中获取gameName，如果没有则使用顶层的gameName
                        game_name = data.get("attributes", {}).get("gameName") or data.get("gameName", data.get("name", "未命名"))

                        example = {
                            "name": game_name,
                            "type": "example",
                            "attrs": [
                                {"type": "path", "value": "default/" + file},
                                {"type": "icon", "value": data["icon"]},
                            ],
                        }

                        examples.append(example)

                    except KeyError:
                        with open(os.path.join(dirpath, file), "r", encoding="utf-8") as tempFile:
                            data = json.load(tempFile)

                        example = {
                            "name": os.path.basename(dirpath),
                            "type": "example",
                            "attrs": [{"type": "path", "value": "default/" + file}],
                        }

                        examples.append(example)
                        continue

            self.exampleMenu = Menu(ZERO, examples)

        self.exampleMenu.draw(game=self)

        if self.speed != 0:
            if (
                self.fpsAverage / abs(self.speed) ** 0.5 < 60
                or self.fpsMinimum / abs(self.speed) ** 0.5 < 30
            ):
                fpsTextColor = "red"
            elif self.fpsMinimum / abs(self.speed) ** 0.5 < 60:
                fpsTextColor = "darkorange"
            else:
                fpsTextColor = "darkgreen"
        else:
            fpsTextColor = "darkgreen"

        fpsText = self.fontSmall.render(
            f"fps = {self.fpsAverage: .0f} / {self.fpsMinimum: .0f} ",
            True,
            fpsTextColor,
        )
        fpsTextRect = fpsText.get_rect()
        fpsTextRect.x = self.screen.get_width() - fpsText.get_width()
        fpsTextRect.y = 0
        self.screen.blit(fpsText, fpsTextRect)

        if not self.isCelestialBodyMode:
            if len(self.elements["all"]) > 50:
                objectCountTextColor = "red"
            elif len(self.elements["all"]) > 30:
                objectCountTextColor = "darkorange"
            else:
                objectCountTextColor = "black"
        else:
            if len(self.elements["all"]) > 25:
                objectCountTextColor = "red"
            elif len(self.elements["all"]) > 15:
                objectCountTextColor = "darkorange"
            else:
                objectCountTextColor = "black"

        objectCountText = self.fontSmall.render(
            f"物体数量 = {len(self.elements["all"])} ", True, objectCountTextColor
        )
        objectCountTextRect = objectCountText.get_rect()
        objectCountTextRect.x = self.screen.get_width() - objectCountText.get_width()
        objectCountTextRect.y = fpsText.get_height()
        self.screen.blit(objectCountText, objectCountTextRect)

        mousePosText = self.fontSmall.render(
            "鼠标位置 = ("
            f" {int(self.screenToReal(pygame.mouse.get_pos()[0] / 10, self.x))},"
            f" {-int(self.screenToReal(pygame.mouse.get_pos()[1] / 10, self.y))} ) ",
            True,
            "black",
        )
        mousePosTextRect = mousePosText.get_rect()
        mousePosTextRect.x = self.screen.get_width() - mousePosText.get_width()
        mousePosTextRect.y = fpsText.get_height() + objectCountText.get_height()
        self.screen.blit(mousePosText, mousePosTextRect)

        ratioText = self.fontSmall.render(
            f"缩放比例 = {self.ratio: .1f}x ", True, "black"
        )
        ratioTextRect = ratioText.get_rect()
        ratioTextRect.x = self.screen.get_width() - ratioText.get_width()
        ratioTextRect.y = (
            fpsText.get_height()
            + objectCountText.get_height()
            + mousePosText.get_height()
        )
        self.screen.blit(ratioText, ratioTextRect)

        speedText = self.fontSmall.render(
            f"倍速 = {self.speed: .1f}x ", True, "black")
        speedTextRect = speedText.get_rect()
        speedTextRect.x = self.screen.get_width() - speedText.get_width()
        speedTextRect.y = (
            fpsText.get_height()
            + objectCountText.get_height()
            + mousePosText.get_height()
            + ratioText.get_height()
        )
        self.screen.blit(speedText, speedTextRect)

        pauseText = self.fontSmall.render(f"已暂停 ", True, "red")
        pauseTextRect = pauseText.get_rect()
        pauseTextRect.x = self.screen.get_width() - pauseText.get_width()
        pauseTextRect.y = (
            fpsText.get_height()
            + objectCountText.get_height()
            + mousePosText.get_height()
            + ratioText.get_height()
            + speedText.get_height()
        )
        if self.isPaused and self.tempFrames == 0:
            self.screen.blit(pauseText, pauseTextRect)

        x, y = pygame.mouse.get_pos()
        for option in self.exampleMenu.options:
            if option.isMouseOn():
                option.highLighted = True
                nameText = self.fontSmall.render(option.name, True, (0, 0, 0))
                nameTextRect = nameText.get_rect(
                    center=(x + nameText.get_width(), y))
                self.screen.blit(nameText, nameTextRect)
            else:
                option.highLighted = False

        for option in self.elementMenu.options:
            if option.isMouseOn():
                option.highLighted = True
                nameText = self.fontSmall.render(option.name, True, (0, 0, 0))
                nameTextRect = nameText.get_rect(
                    center=(x - nameText.get_width(), y))
                self.screen.blit(nameText, nameTextRect)
            else:
                if not option.selected:
                    option.highLighted = False

    def updateElements(self) -> None:
        """更新所有物理元素状态"""
        for element in self.groundElements["all"]:
            if element.position.y <= -1.5e7:
                self.groundElements["all"].remove(element)
                self.groundElements[element.type].remove(element)
                self.celestialElements["all"].append(element)
                self.celestialElements[element.type].append(element)

        for element in self.celestialElements["all"]:
            if element.position.y >= -1.5e7:
                self.groundElements["all"].append(element)
                self.groundElements[element.type].append(element)
                self.celestialElements["all"].remove(element)
                self.celestialElements[element.type].remove(element)

        deltaTime = self.currentTime - self.lastTime
        for element in self.elements["all"]:
            element.draw(self)
            # element.update(...) 为了实现电场力效果挪到了下面，bug待发现
            # if not self.isPaused or self.tempFrames > 0:
            #     element.update(deltaTime * self.speed)

        for ball in self.elements["ball"]:

            if ball.isFollowing:

                try:
                    self.elements["controlling"].remove(ball)
                except ValueError:
                    ...

                ball.highLighted = True
                ball.follow(self)

                followingTipsText = self.fontBig.render(f"视角跟随中", True, "blue")
                followingTipsTextRect = followingTipsText.get_rect()
                followingTipsTextRect.x = self.screen.get_width() / 2
                followingTipsTextRect.y = self.screen.get_height() / 50
                self.screen.blit(followingTipsText, followingTipsTextRect)

                massTipsText = self.fontBig.render(
                    f"质量：{ball.mass: .1f}", True, "darkgreen"
                )
                massTipsTextRect = massTipsText.get_rect()
                massTipsTextRect.x = self.screen.get_width() / 2
                massTipsTextRect.y = (
                    self.screen.get_height() / 50 + followingTipsText.get_height()
                )
                self.screen.blit(massTipsText, massTipsTextRect)

                radiusTipsText = self.fontBig.render(
                    f"半径：{ball.radius: .1f}", True, "darkgreen"
                )
                radiusTipsTextRect = radiusTipsText.get_rect()
                radiusTipsTextRect.x = self.screen.get_width() / 2
                radiusTipsTextRect.y = (
                    self.screen.get_height() / 50
                    + followingTipsText.get_height()
                    + massTipsText.get_height()
                )
                self.screen.blit(radiusTipsText, radiusTipsTextRect)
                
                electricChargeTipsText = self.fontBig.render(
                    f"电荷：{ball.electricCharge: .1f}", True, "darkgreen"
                )
                electricChargeTipsTextRect = electricChargeTipsText.get_rect()
                electricChargeTipsTextRect.x = self.screen.get_width() / 2
                electricChargeTipsTextRect.y = (
                    self.screen.get_height() / 50
                    + followingTipsText.get_height()
                    + massTipsText.get_height()
                    + radiusTipsText.get_height()
                )
                self.screen.blit(electricChargeTipsText, electricChargeTipsTextRect)

                ballPos = ball.position
                tempOption = Option(ZERO, ZERO, "temp", [], self.elementMenu)

                acceleration = (
                    ball.acceleration
                    + (ball.displayedAcceleration - ball.acceleration)
                    * ball.displayedAccelerationFactor
                )
                accelerationPosition = (
                    ballPos
                    + acceleration.copy().normalize() * abs(acceleration) ** 0.5 * 2
                )
                tempOption.drawArrow(
                    self,
                    (
                        self.realToScreen(ballPos.x, self.x),
                        self.realToScreen(ballPos.y, self.y),
                    ),
                    (
                        self.realToScreen(accelerationPosition.x, self.x),
                        self.realToScreen(accelerationPosition.y, self.y),
                    ),
                    "red",
                )
                accelerationTipsText = self.fontBig.render(
                    f"加速度：{abs(acceleration) / 10: .1f} m/s²", True, "red"
                )
                accelerationTipsTextRect = accelerationTipsText.get_rect()
                accelerationTipsTextRect.x = self.realToScreen(
                    accelerationPosition.x, self.x
                )
                accelerationTipsTextRect.y = self.realToScreen(
                    accelerationPosition.y, self.y
                )
                self.screen.blit(accelerationTipsText,
                                 accelerationTipsTextRect)

                velocity = (
                    ball.velocity
                    + (ball.displayedVelocity - ball.velocity)
                    * ball.displayedVelocityFactor
                )
                velocityPosition = (
                    ballPos + velocity.copy().normalize() * abs(velocity) ** 0.5 * 2
                )
                tempOption.drawArrow(
                    self,
                    (
                        self.realToScreen(ballPos.x, self.x),
                        self.realToScreen(ballPos.y, self.y),
                    ),
                    (
                        self.realToScreen(velocityPosition.x, self.x),
                        self.realToScreen(velocityPosition.y, self.y),
                    ),
                    "blue",
                )
                velocityTipsText = self.fontBig.render(
                    f"速度：{abs(velocity) / 10: .1f} m/s", True, "blue"
                )
                velocityTipsTextRect = velocityTipsText.get_rect()
                velocityTipsTextRect.x = self.realToScreen(
                    velocityPosition.x, self.x)
                velocityTipsTextRect.y = self.realToScreen(
                    velocityPosition.y, self.y)
                self.screen.blit(velocityTipsText, velocityTipsTextRect)

            if ball.isShowingInfo:

                ball.highLighted = True

                ballPos = ball.position
                massTipsText = self.fontSmall.render(
                    f"质量：{ball.mass: .1f}", True, "darkgreen"
                )
                massTipsTextRect = massTipsText.get_rect()
                massTipsTextRect.x = self.realToScreen(ballPos.x, self.x)
                massTipsTextRect.y = (
                    self.realToScreen(ballPos.y, self.y) +
                    massTipsText.get_height()
                )
                self.screen.blit(massTipsText, massTipsTextRect)
                
                electricChargeTipsText = self.fontSmall.render(
                    f"电荷：{ball.electricCharge: .1f}", True, "darkgreen"
                )
                electricChargeTipsTextRect = electricChargeTipsText.get_rect()
                electricChargeTipsTextRect.x = self.realToScreen(ballPos.x, self.x)
                electricChargeTipsTextRect.y = (
                    self.realToScreen(ballPos.y, self.y) +
                    massTipsText.get_height() +
                    electricChargeTipsText.get_height()
                )
                self.screen.blit(electricChargeTipsText, electricChargeTipsTextRect)

                tempOption = Option(ZERO, ZERO, "temp", [], self.elementMenu)

                acceleration = (
                    ball.acceleration
                    + (ball.displayedAcceleration - ball.acceleration)
                    * ball.displayedAccelerationFactor
                )
                accelerationPosition = (
                    ballPos + acceleration.copy().normalize() * abs(acceleration) ** 0.5
                )
                tempOption.drawArrow(
                    self,
                    (
                        self.realToScreen(ballPos.x, self.x),
                        self.realToScreen(ballPos.y, self.y),
                    ),
                    (
                        self.realToScreen(accelerationPosition.x, self.x),
                        self.realToScreen(accelerationPosition.y, self.y),
                    ),
                    "red",
                )
                accelerationTipsText = self.fontSmall.render(
                    f"加速度：{abs(acceleration) / 10: .1f} m/s²", True, "red"
                )
                accelerationTipsTextRect = accelerationTipsText.get_rect()
                accelerationTipsTextRect.x = self.realToScreen(
                    accelerationPosition.x, self.x
                )
                accelerationTipsTextRect.y = self.realToScreen(
                    accelerationPosition.y, self.y
                )
                self.screen.blit(accelerationTipsText,
                                 accelerationTipsTextRect)

                velocity = (
                    ball.velocity
                    + (ball.displayedVelocity - ball.velocity)
                    * ball.displayedVelocityFactor
                )
                velocityPosition = (
                    ballPos + velocity.copy().normalize() * abs(velocity) ** 0.5
                )
                tempOption.drawArrow(
                    self,
                    (
                        self.realToScreen(ballPos.x, self.x),
                        self.realToScreen(ballPos.y, self.y),
                    ),
                    (
                        self.realToScreen(velocityPosition.x, self.x),
                        self.realToScreen(velocityPosition.y, self.y),
                    ),
                    "blue",
                )
                velocityTipsText = self.fontSmall.render(
                    f"速度：{abs(velocity) / 10: .1f} m/s", True, "blue"
                )
                velocityTipsTextRect = velocityTipsText.get_rect()
                velocityTipsTextRect.x = self.realToScreen(
                    velocityPosition.x, self.x)
                velocityTipsTextRect.y = self.realToScreen(
                    velocityPosition.y, self.y)
                self.screen.blit(velocityTipsText, velocityTipsTextRect)

        for ball in self.elements["ball"]:
            ball.resetForce(True)

        for ball1 in self.elements["ball"]:
            try:
                for ball2 in self.elements["ball"]:
                    if ball1 != ball2:

                        if ball1.isCollidedByBall(ball2):
                            if self.isCelestialBodyMode:

                                newBall = ball1.merge(ball2, self)

                                if ball1.isFollowing or ball2.isFollowing:
                                    newBall.isFollowing = True

                                if (
                                    ball1 in self.elements["controlling"]
                                    and ball1.mass >= ball2.mass
                                ) or (
                                    ball2 in self.elements["controlling"]
                                    and ball2.mass >= ball1.mass
                                ):
                                    self.elements["controlling"].clear()
                                    self.elements["controlling"].append(
                                        newBall)
                                    newBall.highLighted = True

                                self.elements["all"].remove(ball1)
                                self.elements["ball"].remove(ball1)
                                self.elements["all"].remove(ball2)
                                self.elements["ball"].remove(ball2)
                                self.elements["all"].append(newBall)
                                self.elements["ball"].append(newBall)

                                for ball in self.elements["ball"]:
                                    ball.displayedAcceleration = (
                                        ball.acceleration
                                        + (
                                            ball.displayedAcceleration
                                            - ball.acceleration
                                        )
                                        * ball.displayedAccelerationFactor
                                    )
                                    ball.displayedAccelerationFactor = 1
                            else:
                                ball1.reboundByBall(ball2)

                        if ball1.gravitation and ball2.gravitation:
                            ball1.gravitate(ball2)
                        if ball1.electricCharge and ball2.electricCharge:
                            ball1.electricForce(ball2)
                            # print(ball1.acceleration.toTuple())
                            # ball1.update(deltaTime * self.speed)

            except ValueError as e:
                ...

            for wall in self.elements["wall"]:
                if wall.isPosOn(self, ball1.position):
                    ball1.reboundByWall(wall)

            if not self.isCelestialBodyMode:
                for line in self.floor.lines:
                    if ball1.isCollidedByLine(line):
                        ball1.reboundByLine(line)
                if self.floor.isPosOn(self, ball1.position):
                    ball1.reboundByWall(self.floor)

            for option in self.environmentOptions:

                if option["type"] == "gravity":
                    ball1.gravity = float(option["value"])

                if option["type"] == "airResistance":
                    ball1.airResistance = float(option["value"])

                if option["type"] == "collisionFactor":
                    ball1.collisionFactor = float(option["value"])
                    for wall in self.elements["wall"]:
                        wall.collisionFactor = float(option["value"])
                    self.floor.collisionFactor = float(option["value"])
        
        for element in self.elements["all"]:
            # element.draw(self)
            if not self.isPaused or self.tempFrames > 0:
                element.update(deltaTime * self.speed)
        
        for wall in self.elements["wall"]:
            for ball in self.elements["ball"]:
                wall.checkVertexCollision(ball)

        for wall in self.elements["wall"]:
            for line in wall.lines:
                for ball in self.elements["ball"]:
                    if ball.isCollidedByLine(line) and not wall.isPosOn(
                        self, ball.position
                    ):
                        ball.reboundByLine(line)

        if not self.isCelestialBodyMode:
            self.floor.position.x = self.screenToReal(
                self.screen.get_width() / 2, self.x
            )
            self.floor.update(deltaTime)
            self.floor.draw(self)

        if self.isMoving and not self.isElementCreating:
            for element in self.elements["controlling"]:

                pos = pygame.mouse.get_pos()
                element.highLighted = True

                try:
                    element.velocity = ZERO
                except Exception as e:
                    ...

                allowToPlace = True
                for element2 in self.elements["all"]:
                    if element2.isMouseOn(self) and element2 != element:
                        allowToPlace = False
                        break

                if allowToPlace:
                    element.position.x = self.screenToReal(pos[0], self.x)
                    element.position.y = self.screenToReal(pos[1], self.y)

                # element.update(deltaTime * self.speed)

        self.updateFPS()

    def updateFPS(self) -> None:
        """更新帧率"""
        self.lastTime = self.currentTime
        self.currentTime = time.time()
        self.fpsSaver.append(self.currentTime - self.lastTime)
        if sum(self.fpsSaver) > 0:
            self.fpsAverage = len(self.fpsSaver) / sum(self.fpsSaver)
            self.fpsMinimum = 1 / max(self.fpsSaver)
        if sum(self.fpsSaver) >= 1:
            del self.fpsSaver[0]

    def update(self) -> None:
        """主更新循环"""
        self.eventLoop()
        self.updateScreen()

        # 即使在暂停状态下也要更新绳子的位置
        for rope in self.elements["rope"]:
            rope.calculateForce()  # 确保绳子两端位置正确

        # 更新弹簧力，确保在球更新之前计算力
        for spring in self.elements["spring"]:
            spring.calculateForce()

        self.updateElements()
        self.update_shared_state()
        self.updateMenu()
        if self.tempFrames > 0:
            self.tempFrames -= 1

    def findMaximumGravitationBall(self, ball: Ball) -> Ball | None:
        """寻找给予指定球最大引力的球"""
        if ball is None:
            return

        result = None
        # minDistance = float("inf")
        maxGravitation = 0

        for ball2 in self.elements["ball"]:
            # if ball2.mass > ball.mass and ball.position.distance(ball2.position) < minDistance:
            #     result = ball2
            #     minDistance = ball.position.distance(ball2.position)

            distance = ball.position.distance(ball2.position)

            if gravityFactor * ball.mass * ball2.mass / (distance**2 + 1e-6) > maxGravitation:
                result = ball2
                maxGravitation = gravityFactor * ball.mass * \
                    ball2.mass / (distance**2 + 1e-6)

        return result

    def CelestialBodyMode(self) -> None:
        """切换天体模式"""
        if not self.isCelestialBodyMode and not self.isModeChangingNaturally:
            self.minLimitRatio = 0.01
            self.maxLimitRatio = 10

            r = self.ratio
            self.ratio = self.lastRatio
            self.lastRatio = r

            x = self.x
            self.x = self.lastX
            self.lastX = x

            y = self.y
            self.y = self.lastY
            self.lastY = y

        if self.y - self.screenToReal(self.screen.get_height()) / 2 < 1.5e7:
            self.isModeChangingNaturally = True
            for option in self.environmentOptions:

                if option["type"] == "mode":
                    option["value"] = "0"

                if option["type"] == "gravity":
                    option["value"] = "1"
        else:
            self.isModeChangingNaturally = False
            self.isCelestialBodyMode = True
            self.elements = self.celestialElements

            self.background = "darkgrey"
            self.environmentOptionsCopy = self.environmentOptions.copy()
            for option in self.environmentOptions:

                if option["type"] == "gravity":
                    option["value"] = "0"

                if option["type"] == "airResistance":
                    option["value"] = "1"

                if option["type"] == "mode":
                    option["value"] = 1

            for ball in self.elements["ball"]:
                ball.gravitation = True

    def GroundSurfaceMode(self) -> None:
        """切换地表模式"""
        if self.isCelestialBodyMode and not self.isModeChangingNaturally:
            self.minLimitRatio = 1
            self.maxLimitRatio = 15

            r = self.ratio
            self.ratio = self.lastRatio
            self.lastRatio = r

            x = self.x
            self.x = self.lastX
            self.lastX = x

            y = self.y
            self.y = self.lastY
            self.lastY = y

        if self.y - self.screenToReal(self.screen.get_height()) / 2 >= 1.5e7:
            self.isModeChangingNaturally = True
            for option in self.environmentOptions:

                if option["type"] == "mode":
                    option["value"] = "1"

                if option["type"] == "gravity":
                    option["value"] = "0"
        else:
            self.isModeChangingNaturally = False
            self.isCelestialBodyMode = False
            self.elements = self.groundElements
            self.background = "lightgrey"
            self.environmentOptions = self.environmentOptionsCopy.copy()

            for ball in self.elements["ball"]:
                ball.gravitation = False
                ball.naturalForces.clear()

    def update_shared_state(self):
        if self.shared_state is None:
            return

        balls_data = [
            {
                'x': ball.position.x,
                'y': ball.position.y,
                'radius': ball.radius,
                'mass': ball.mass,
                'color': ball.color
            }
            for ball in self.elements['ball']
        ]

        walls_data = [
            {
                'vertices': [(v.x, v.y) for v in wall.vertexes],
                'color': wall.color
            }
            for wall in self.elements['wall']
        ]

        if not self.isCelestialBodyMode and not self.isFloorIllegal:
            floor_data = {
                'vertices': [(v.x, v.y) for v in self.floor.vertexes],
                'color': self.floor.color
            }
            walls_data.append(floor_data)

        self.shared_state.update_balls(balls_data)
        self.shared_state.update_walls(walls_data)
        self.shared_state.update_view_state(
            self.x, self.y, self.ratio, str(self.background) if isinstance(self.background, pygame.Color) else self.background
        )
        self.shared_state.set_celestial_mode(self.isCelestialBodyMode)
        self.shared_state.increment_frame()
