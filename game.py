from basic import *
from ai import *
from tkinter import messagebox
import pygame
import copy
import os
import sys
import time
import json
import ctypes
import pickle

def setCapsLock(state=True) -> None:
    """
    设置或取消CapsLock状态
    state=True: 开启大写
    state=False: 关闭大写
    """
    VK_CAPITAL = 0x14
    current = ctypes.windll.user32.GetKeyState(VK_CAPITAL)

    if (current & 0xFFFF) != int(state):
        ctypes.windll.user32.keybd_event(VK_CAPITAL, 0, 0x1, 0)  # 按下
        ctypes.windll.user32.keybd_event(VK_CAPITAL, 0, 0x3, 0)  # 释放

class Game:
    """物理运动模拟系统主游戏类"""
    def __init__(self) -> None:
        pygame.init()
        self.isPaused = False
        self.isElementCreating = False
        self.isMoving = False
        self.isScreenMoving = False
        self.isMassSetting = False
        self.isCircularVelocityGetting = False
        self.isCircularVelocityDirectionAnticlockwise = True
        self.isCtrlPressing = False
        self.isEditing = False
        self.isElementControlling = False
        self.isPressed = False
        self.isDragging = False
        self.isCelestialBodyMode = False
        self.isModeChangingNaturally = False
        self.icon = ""

        self.screen = pygame.display.set_mode()
        pygame.display.set_caption("Physics Motion Simulation System Beta")
        icon = pygame.image.load("static/icon.png").convert_alpha()
        pygame.display.set_icon(icon)

        self.mousePos = (0, 0)   # 鼠标屏幕坐标，而非真实坐标
        self.fontSmall = pygame.font.Font("static/HarmonyOS_Sans_SC_Medium.ttf", int(self.screen.get_width()/125))
        self.fontBig = pygame.font.Font("static/HarmonyOS_Sans_SC_Medium.ttf", int(self.screen.get_width()/75))
        self.ratio = 5
        self.lastRatio = self.ratio
        self.minLimitRatio = 1
        self.maxLimitRatio = 15
        self.x = self.screen.get_width()/2 / self.ratio
        self.y = self.screen.get_height() / self.ratio
        self.lastX = self.x
        self.lastY = 2e+7
        self.elementMenu : Menu = None
        self.exampleMenu : Menu = None
        self.currentTime = time.time()
        self.lastTime = self.currentTime
        self.fpsAverage = 0
        self.fpsMinimum = 0
        self.rightMove = 0
        self.upMove = 0
        self.speed = 1
        self.circularVelocityFactor = 1
        self.floor = Wall([Vector2(0, -10), Vector2(self.screen.get_width(), -10), Vector2(self.screen.get_width(), self.screen.get_height()), Vector2(0, self.screen.get_height())], (200, 200, 200), True)
        self.isFloorIllegal = False
        self.background = "lightgrey"
        self.settingsButton = SettingsButton(0, 0, 50, 50)
        self.fpsSaver = []
        self.tempFrames = 0

        self.groundElements = {
            "all": [], 
            "controlling": []
        }

        self.celestialElements = {
            "all": [], 
            "controlling": []
        }

        with open("config/elementOptions.json", "r", encoding="utf-8") as f:
            self.optionsList = json.load(f)

        for i in range(len(self.optionsList)):
            self.groundElements[self.optionsList[i]["type"]] = []
            self.celestialElements[self.optionsList[i]["type"]] = []

        self.elements = self.groundElements

        self.environmentOptions = []

        with open("config/environmentOptions.json", "r", encoding="utf-8") as f:
            self.environmentOptions = json.load(f)

        self.environmentOptionsCopy = self.environmentOptions.copy()

        with open("config/translation.json", "r", encoding="utf-8") as f:
            self.translation = json.load(f)

        self.inputMenu = InputMenu(Vector2(self.screen.get_width()/2, self.screen.get_height()/2), self, self)
        self.inputMenu.options = self.environmentOptions
        self.inputMenu.update(self)

        self.test()

    def exit(self) -> None:
        """退出游戏并取消大写锁定"""
        setCapsLock(False)
        self.saveGame("autosave")
        print("游戏退出")
        pygame.quit()
        sys.exit()

    def test(self) -> None:
        """测试方法（预留）"""
        self.y = 1.5e+7
        ...

    def saveGame(self, filename="autosave") -> None:
        """保存游戏数据"""
        for elementOption in self.elementMenu.options:
            elementOption.highLighted = False

        # 创建一个新的字典，用于存储可序列化的属性
        # serializableDict = {
        #     "gameName" : f"{int(time.time())}备份"
        # }
        
        serializableDict = {               #做预设用的
            "gameName" : f"彩蛋",
            "icon" : "static/easterEgg.png"
        }

        # freeFall flatToss idealBevel basketball  easterEgg

        # 遍历 self.__dict__，排除不可序列化的对象
        for attr, value in self.__dict__.items():
            if attr != "screen" and attr != "fpsSaver" and attr != "icon" and attr != "gameName":
                try:
                    # 尝试序列化对象，如果成功则添加到 serializableDict 中
                    pickle.dumps(value)
                    serializableDict[attr] = value

                except (pickle.PicklingError, TypeError):
                    # 如果序列化失败，跳过该属性
                    ...

        os.makedirs("savefile", exist_ok=True)

        # 将可序列化的字典保存到文件
        with open(f"savefile/{filename}.pkl", "wb") as f:
            pickle.dump(serializableDict, f)
            print(f"\n游戏数据保存成功：{filename}.pkl")
            f.close()

    def loadGame(self, filename="autosave") -> None:
        """加载游戏数据"""
        # 保存当前的 screen 属性
        currentScreen = getattr(self, "screen", None)
        currentExampleMenu = getattr(self, "exampleMenu", None)
        currentElementMenu = getattr(self, "elementMenu", None)

        try:

            if filename == "" and os.path.exists("savefile/autosave.pkl"):
                filename = "autosave"

            print(f"正在加载游戏数据：{filename}.pkl")

            with open(f"savefile/{filename}.pkl", "rb") as f:
                # 加载序列化的字典
                serializableDict = pickle.load(f)

                # 更新 self.__dict__，只更新可序列化的属性
                self.__dict__.update(serializableDict)

                # 恢复 screen 属性
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
                
                # 恢复坐标系统相关参数
                self.x = serializableDict.get("x", self.screen.get_width()/2 / self.ratio)
                self.y = serializableDict.get("y", self.screen.get_height() / self.ratio)
                self.ratio = serializableDict.get("ratio", 5)
                
                # 重置移动控制状态
                self.rightMove = 0
                self.upMove = 0
                            
                self.lastTime = time.time()
                self.currentTime = time.time()
                print("游戏数据加载成功")
                f.close()

        except FileNotFoundError:
            ...

        except IndexError:
            ...

        except PermissionError:
            ...

    def setAttr(self, name, value) -> None:
        """设置环境属性"""
        for option in self.environmentOptions:
            if option["type"] == name:
                option["value"] = value
                break

    def realToScreen(self, r : float | Vector2, x : float | Vector2 = None) -> float | Vector2:
        """实际坐标转屏幕坐标"""
        if x is None:
            if isinstance(r, Vector2):
                x = ZERO
            else:
                x = 0

        return (r + x) * self.ratio

    def screenToReal(self, r : float | Vector2, x : float | Vector2 = None) -> float | Vector2:
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
                        option.edit(self, Vector2(self.mousePos))  # edit里会判定对应的按钮是否被点击，并编辑对应的物体

            if event.type == pygame.MOUSEWHEEL:
                speed = 1.1
                
                if event.y == 1 and self.ratio < self.maxLimitRatio:
                    if not self.isCtrlPressing:

                        bx = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                        by = self.screenToReal(pygame.mouse.get_pos()[1], self.y)

                        self.ratio *= speed

                        nx = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                        ny = self.screenToReal(pygame.mouse.get_pos()[1], self.y)

                        self.x += nx - bx
                        self.y += ny - by

                    else:

                        bx = self.screenToReal(self.screen.get_width()/2, self.x)
                        by = self.screenToReal(self.screen.get_height()/2, self.y)

                        self.ratio *= speed

                        nx = self.screenToReal(self.screen.get_width()/2, self.x)
                        ny = self.screenToReal(self.screen.get_height()/2, self.y)

                        self.x += nx - bx
                        self.y += ny - by

                elif event.y == -1 and self.ratio > self.minLimitRatio:
                    if not self.isCtrlPressing:

                        bx = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                        by = self.screenToReal(pygame.mouse.get_pos()[1], self.y)

                        self.ratio /= speed

                        nx = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                        ny = self.screenToReal(pygame.mouse.get_pos()[1], self.y)

                        self.x += nx - bx
                        self.y += ny - by

                    else:

                        bx = self.screenToReal(self.screen.get_width()/2, self.x)
                        by = self.screenToReal(self.screen.get_height()/2, self.y)

                        self.ratio /= speed

                        nx = self.screenToReal(self.screen.get_width()/2, self.x)
                        ny = self.screenToReal(self.screen.get_height()/2, self.y)
                        
                        self.x += nx - bx
                        self.y += ny - by

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mousePos = pygame.mouse.get_pos()
                
                if event.button == 1 and not self.elementMenu.isMouseOn() and not self.isElementCreating and not self.isElementControlling and not self.isEditing:
                    self.isMoving = True
                    self.isScreenMoving = True

                    for element in self.elements["all"]:
                        if(element.isMouseOn(self)):
                            self.elements["controlling"].append(element)
                            self.isScreenMoving = False

                if event.button == 3 and not self.elementMenu.isMouseOn():
                    self.isElementControlling = True
                    for element in self.elements["all"]:
                        if(element.isMouseOn(self)):
                            element.highLighted = True
                            self.update()
                            pygame.display.update()
                            elementController = ElementController(element, Vector2(self.mousePos))
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
                                        
                                        if event.key == pygame.K_z and self.isCtrlPressing and len(self.elements["all"]) > 0:
                                            lastElement = self.elements["all"][-1]
                                            self.elements["all"].remove(lastElement)

                                            for ball in self.elements["ball"]:
                                                ball.displayedAcceleration = ball.acceleration + (ball.displayedAcceleration - ball.acceleration) * ball.displayedAccelerationFactor
                                                ball.displayedAccelerationFactor = 1

                                            for option in self.elementMenu.options:
                                                if option.type == lastElement.type:
                                                    self.elements[option.type].remove(lastElement)
                                                    break

                                        if event.key == pygame.K_g:
                                            self.saveGame("manualsave")

                                        if event.key == pygame.K_l:
                                            self.loadGame("autosave")

                                        if event.key == pygame.K_k:
                                            self.loadGame("manualsave")

                                        if pygame.K_1 <= event.key <= pygame.K_9:
                                            self.loadGame(f"default/{str(event.key - pygame.K_0)}")
                                            loadedTipText = self.fontSmall.render(f"{self.gameName}加载成功", True, (0, 0, 0))
                                            loadedTipRect = loadedTipText.get_rect(center=(self.screen.get_width()/2, self.screen.get_height()/2))
                                            
                                            self.update()
                                            self.screen.blit(loadedTipText, loadedTipRect)
                                            pygame.display.update()
                                            time.sleep(0.5)
                                            self.lastTime = time.time()
                                            self.currentTime = time.time()

                                        if event.key == pygame.K_r:
                                            self.elements["all"].clear()
                                            for option in self.elementMenu.options:
                                                self.elements[option.type].clear()
                                            self.isElementControlling = False

                                        if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                                            self.isCtrlPressing = True

                                        if event.key == pygame.K_ESCAPE:
                                            self.isElementControlling = False

                                    if event.type == pygame.MOUSEBUTTONDOWN:

                                        if not elementController.isMouseOn() or element.isMouseOn(self):
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

                    self.x += self.screenToReal(pygame.mouse.get_pos()[0] - self.mousePos[0])
                    
                    if not self.isFloorIllegal or self.screenToReal(pygame.mouse.get_pos()[1] - self.mousePos[1]) > 0:
                        self.y += self.screenToReal(pygame.mouse.get_pos()[1] - self.mousePos[1])

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
                        if(element.isMouseOn(self)):
                            element.copy(self)
                            break

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_z and self.isCtrlPressing and len(self.elements["all"]) > 0:
                    lastElement = self.elements["all"][-1]
                    self.elements["all"].remove(lastElement)
                    
                    for ball in self.elements["ball"]:
                        ball.displayedAcceleration = ball.acceleration + (ball.displayedAcceleration - ball.acceleration) * ball.displayedAccelerationFactor
                        ball.displayedAccelerationFactor = 1

                    for option in self.elementMenu.options:
                        if option.type == lastElement.type:
                            self.elements[option.type].remove(lastElement)
                            break

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
                    self.saveGame("manualsave")

                if event.key == pygame.K_l:
                    self.loadGame("autosave")
                
                if event.key == pygame.K_k:
                    self.loadGame("manualsave")

                if pygame.K_1 <= event.key <= pygame.K_9:
                    self.loadGame(f"default/{str(event.key - pygame.K_0)}")
                    loadedTipText = self.fontSmall.render(f"{self.gameName}加载成功", True, (0, 0, 0))
                    loadedTipRect = loadedTipText.get_rect(center=(self.screen.get_width()/2, self.screen.get_height()/2))
                    
                    self.update()
                    self.screen.blit(loadedTipText, loadedTipRect)
                    pygame.display.update()
                    time.sleep(0.5)
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

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self.isCtrlPressing = False

            self.screenMove(event)

    def openEditor(self, inputMenu) -> None:
        """打开参数编辑器"""
        inputMenu.update(self)
        self.isEditing = True
        inputMenu.update(self)
        while self.isEditing:
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

                    if event.key == pygame.K_z and self.isCtrlPressing and len(self.elements["all"]) > 0:
                        lastElement = self.elements["all"][-1]
                        self.elements["all"].remove(lastElement)
                        
                        for ball in self.elements["ball"]:
                            ball.displayedAcceleration = ball.acceleration + (ball.displayedAcceleration - ball.acceleration) * ball.displayedAccelerationFactor
                            ball.displayedAccelerationFactor = 1

                        for option in self.elementMenu.options:
                            if option.type == lastElement.type:
                                self.elements[option.type].remove(lastElement)
                                break

                    if event.key == pygame.K_m or event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        self.isEditing = False

                inputMenu.updateBoxes(event, self)
        self.updateFPS()

    def screenMove(self, event) -> None:
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
        if self.realToScreen(self.floor.vertexes[0].y, self.y) < self.screen.get_height()*2/3 and not self.isCelestialBodyMode:
            self.isFloorIllegal = True
        else:
            self.isFloorIllegal = False

        self.screen.fill(self.background)
        self.settingsButton.draw(self)

    def updateMenu(self) -> None:
        """更新菜单界面"""
        width, height = self.screen.get_size()
        if self.elementMenu == None:
            with open("config/elementOptions.json", "r", encoding="utf-8") as filenames:
                self.elementMenu = Menu(Vector2(width*97/100, 0), json.load(filenames))
        self.elementMenu.draw(game=self)

        if self.exampleMenu == None:
            examples = []
            for dirpath, dirnames, filenames in os.walk("savefile/default"):
                for file in filenames:

                    try:
                        tempFile = open(os.path.join(dirpath, file), "rb")
                        data = pickle.load(tempFile)
                        tempFile.close()

                        example = {
                            "name": data["gameName"], 
                            "type": "example", 
                            "attrs": [
                                {
                                    "type": "path", 
                                    "value": "default/"+file
                                }, 
                                {
                                    "type": "icon", 
                                    "value": data["icon"]
                                }
                            ]
                        }

                        examples.append(example)

                    except KeyError:
                        tempFile = open(os.path.join(dirpath, file), "rb")
                        data = pickle.load(tempFile)
                        tempFile.close()

                        example = {
                            "name": os.path.basename(dirpath), 
                            "type": "example", 
                            "attrs": [
                                {
                                "type": "path", 
                                "value": "default/"+file
                                }
                            ]
                        }

                        examples.append(example)
                        continue

            self.exampleMenu = Menu(ZERO, examples)
            

        self.exampleMenu.draw(game=self)


        if self.speed != 0:
            if self.fpsAverage / abs(self.speed) ** 0.5 < 60 or self.fpsMinimum / abs(self.speed) ** 0.5 < 30:
                fpsTextColor = "red"
            elif self.fpsMinimum / abs(self.speed) ** 0.5 < 60:
                fpsTextColor = "darkorange"
            else:
                fpsTextColor = "darkgreen"
        else:
            fpsTextColor = "darkgreen"
            
        fpsText = self.fontSmall.render(f"fps = {self.fpsAverage: .0f} / {self.fpsMinimum: .0f} ", True, fpsTextColor)
        fpsTextRect =  fpsText.get_rect()
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

        objectCountText = self.fontSmall.render(f"物体数量 = {len(self.elements["all"])} ", True, objectCountTextColor)
        objectCountTextRect =  objectCountText.get_rect()
        objectCountTextRect.x = self.screen.get_width() - objectCountText.get_width()
        objectCountTextRect.y = fpsText.get_height()
        self.screen.blit(objectCountText, objectCountTextRect)

        mousePosText = self.fontSmall.render(f"鼠标位置 = ( {int(self.screenToReal(pygame.mouse.get_pos()[0]/10, self.x))}, {-int(self.screenToReal(pygame.mouse.get_pos()[1]/10, self.y))} ) ", True, "black")
        mousePosTextRect =  mousePosText.get_rect()
        mousePosTextRect.x = self.screen.get_width() - mousePosText.get_width()
        mousePosTextRect.y = fpsText.get_height() + objectCountText.get_height()
        self.screen.blit(mousePosText, mousePosTextRect)

        ratioText = self.fontSmall.render(f"缩放比例 = {self.ratio: .1f}x ", True, "black")
        ratioTextRect =  ratioText.get_rect()
        ratioTextRect.x = self.screen.get_width() - ratioText.get_width()        
        ratioTextRect.y = fpsText.get_height() + objectCountText.get_height() + mousePosText.get_height()
        self.screen.blit(ratioText, ratioTextRect)

        speedText = self.fontSmall.render(f"倍速 = {self.speed: .1f}x ", True, "black") 
        speedTextRect =  speedText.get_rect()
        speedTextRect.x = self.screen.get_width() - speedText.get_width()
        speedTextRect.y = fpsText.get_height() + objectCountText.get_height() + mousePosText.get_height() + ratioText.get_height()
        self.screen.blit(speedText, speedTextRect)

        pauseText = self.fontSmall.render(f"已暂停 ", True, "red")
        pauseTextRect =  pauseText.get_rect()
        pauseTextRect.x = self.screen.get_width() - pauseText.get_width()
        pauseTextRect.y = fpsText.get_height() + objectCountText.get_height() + mousePosText.get_height() + ratioText.get_height() + speedText.get_height()
        if self.isPaused and self.tempFrames == 0:
            self.screen.blit(pauseText, pauseTextRect)

        x, y = pygame.mouse.get_pos()
        for option in self.exampleMenu.options:
            if option.isMouseOn():
                option.highLighted = True
                nameText = self.fontSmall.render(option.name, True, (0, 0, 0))
                nameTextRect = nameText.get_rect(center=(x + nameText.get_width(), y))
                self.screen.blit(nameText, nameTextRect)
            else:
                option.highLighted = False

        for option in self.elementMenu.options:
            if option.isMouseOn():
                option.highLighted = True
                nameText = self.fontSmall.render(option.name, True, (0, 0, 0))
                nameTextRect = nameText.get_rect(center=(x - nameText.get_width(), y))
                self.screen.blit(nameText, nameTextRect)
            else:
                if not option.selected:
                    option.highLighted = False

    def updateElements(self):
        """更新所有物理元素状态"""
        for element in self.groundElements["all"]:
            if element.position.y <= -1.5e+7:
                self.groundElements["all"].remove(element)
                self.groundElements[element.type].remove(element)
                self.celestialElements["all"].append(element)
                self.celestialElements[element.type].append(element)

        for element in self.celestialElements["all"]:
            if element.position.y >= -1.5e+7:
                self.groundElements["all"].append(element)
                self.groundElements[element.type].append(element)
                self.celestialElements["all"].remove(element)
                self.celestialElements[element.type].remove(element)    

        deltaTime = self.currentTime - self.lastTime
        for element1 in self.elements["all"]:
            element1.draw(self)
            if not self.isPaused or self.tempFrames > 0:
                element1.update(deltaTime * self.speed)

        for ball1 in self.elements["ball"]:

            if ball1.isFollowing:

                try:
                    self.elements["controlling"].remove(ball1)
                except ValueError:
                    ...

                ball1.highLighted = True
                ball1.follow(self)

                followingTipsText = self.fontBig.render(f"视角跟随中", True, "blue")
                followingTipsTextRect =  followingTipsText.get_rect()
                followingTipsTextRect.x = self.screen.get_width()/2
                followingTipsTextRect.y = self.screen.get_height()/50
                self.screen.blit(followingTipsText, followingTipsTextRect)

                massTipsText = self.fontBig.render(f"质量：{ball1.mass: .1f}", True, "darkgreen")
                massTipsTextRect =  massTipsText.get_rect()
                massTipsTextRect.x = self.screen.get_width()/2
                massTipsTextRect.y = self.screen.get_height()/50 + followingTipsText.get_height()
                self.screen.blit(massTipsText, massTipsTextRect)

                radiusTipsText = self.fontBig.render(f"半径：{ball1.radius: .1f}", True, "darkgreen")
                radiusTipsTextRect =  radiusTipsText.get_rect()
                radiusTipsTextRect.x = self.screen.get_width()/2
                radiusTipsTextRect.y = self.screen.get_height()/50 + followingTipsText.get_height() + massTipsText.get_height()
                self.screen.blit(radiusTipsText, radiusTipsTextRect)

                ballPos = ball1.position
                tempOption = Option(ZERO, Vector2(0, 0), "temp", [], self.elementMenu)

                acceleration = ball1.acceleration + (ball1.displayedAcceleration - ball1.acceleration) * ball1.displayedAccelerationFactor
                accelerationPosition = ballPos + acceleration.copy().normalize() * abs(acceleration) ** 0.5 * 2
                tempOption.drawArrow(self, (self.realToScreen(ballPos.x, self.x), self.realToScreen(ballPos.y, self.y)), (self.realToScreen(accelerationPosition.x, self.x), self.realToScreen(accelerationPosition.y, self.y)), "red")
                accelerationTipsText = self.fontBig.render(f"加速度：{abs(acceleration)/10: .1f} m/s²", True, "red")
                accelerationTipsTextRect =  accelerationTipsText.get_rect()
                accelerationTipsTextRect.x = self.realToScreen(accelerationPosition.x, self.x)
                accelerationTipsTextRect.y = self.realToScreen(accelerationPosition.y, self.y)
                self.screen.blit(accelerationTipsText, accelerationTipsTextRect)

                velocity = ball1.velocity + (ball1.displayedVelocity - ball1.velocity) * ball1.displayedVelocityFactor
                velocityPosition = ballPos + velocity.copy().normalize() * abs(velocity) ** 0.5 * 2
                tempOption.drawArrow(self, (self.realToScreen(ballPos.x, self.x), self.realToScreen(ballPos.y, self.y)), (self.realToScreen(velocityPosition.x, self.x), self.realToScreen(velocityPosition.y, self.y)), "blue")
                velocityTipsText = self.fontBig.render(f"速度：{abs(velocity)/10: .1f} m/s", True, "blue")
                velocityTipsTextRect =  velocityTipsText.get_rect()
                velocityTipsTextRect.x = self.realToScreen(velocityPosition.x, self.x)
                velocityTipsTextRect.y = self.realToScreen(velocityPosition.y, self.y)
                self.screen.blit(velocityTipsText, velocityTipsTextRect)

            if ball1.isShowingInfo:

                ball1.highLighted = True

                ballPos = ball1.position
                massTipsText = self.fontSmall.render(f"质量：{ball1.mass: .1f}", True, "darkgreen")
                massTipsTextRect =  massTipsText.get_rect()
                massTipsTextRect.x = self.realToScreen(ballPos.x, self.x)
                massTipsTextRect.y = self.realToScreen(ballPos.y, self.y) + massTipsText.get_height()
                self.screen.blit(massTipsText, massTipsTextRect)

                tempOption = Option(Vector2(0, 0), Vector2(0, 0), "temp", [], self.elementMenu)

                acceleration = ball1.acceleration + (ball1.displayedAcceleration - ball1.acceleration) * ball1.displayedAccelerationFactor
                accelerationPosition = ballPos + acceleration.copy().normalize() * abs(acceleration) ** 0.5
                tempOption.drawArrow(self, (self.realToScreen(ballPos.x, self.x), self.realToScreen(ballPos.y, self.y)), (self.realToScreen(accelerationPosition.x, self.x), self.realToScreen(accelerationPosition.y, self.y)), "red")
                accelerationTipsText = self.fontSmall.render(f"加速度：{abs(acceleration)/10: .1f} m/s²", True, "red")
                accelerationTipsTextRect =  accelerationTipsText.get_rect()
                accelerationTipsTextRect.x = self.realToScreen(accelerationPosition.x, self.x)
                accelerationTipsTextRect.y = self.realToScreen(accelerationPosition.y, self.y)
                self.screen.blit(accelerationTipsText, accelerationTipsTextRect)

                velocity = ball1.velocity + (ball1.displayedVelocity - ball1.velocity) * ball1.displayedVelocityFactor
                velocityPosition = ballPos + velocity.copy().normalize() * abs(velocity) ** 0.5
                tempOption.drawArrow(self, (self.realToScreen(ballPos.x, self.x), self.realToScreen(ballPos.y, self.y)), (self.realToScreen(velocityPosition.x, self.x), self.realToScreen(velocityPosition.y, self.y)), "blue")
                velocityTipsText = self.fontSmall.render(f"速度：{abs(velocity)/10: .1f} m/s", True, "blue")
                velocityTipsTextRect =  velocityTipsText.get_rect()
                velocityTipsTextRect.x = self.realToScreen(velocityPosition.x, self.x)
                velocityTipsTextRect.y = self.realToScreen(velocityPosition.y, self.y)
                self.screen.blit(velocityTipsText, velocityTipsTextRect)

            ball1.resetForce(True)

            try:
                for ball2 in self.elements["ball"]:
                    if ball1 != ball2:

                        if ball1.isCollidedByBall(ball2):
                            if self.isCelestialBodyMode:

                                newBall = ball1.merge(ball2, self)

                                if ball1.isFollowing or ball2.isFollowing:
                                    newBall.isFollowing = True

                                if (ball1 in self.elements["controlling"] and ball1.mass >= ball2.mass) or (ball2 in self.elements["controlling"] and ball2.mass >= ball1.mass):
                                    self.elements["controlling"].clear()
                                    self.elements["controlling"].append(newBall)
                                    newBall.highLighted = True

                                self.elements["all"].remove(ball1)
                                self.elements["ball"].remove(ball1)
                                self.elements["all"].remove(ball2)
                                self.elements["ball"].remove(ball2)
                                self.elements["all"].append(newBall)
                                self.elements["ball"].append(newBall)

                                for ball in self.elements["ball"]:
                                    ball.displayedAcceleration = ball.acceleration + (ball.displayedAcceleration - ball.acceleration) * ball.displayedAccelerationFactor
                                    ball.displayedAccelerationFactor = 1
                            else:
                                ball1.reboundByBall(ball2)

                        if ball1.gravitation and ball2.gravitation:
                            ball1.gravitate(ball2)
                            
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
            for ball in self.elements["ball"]:
                wall.checkVertexCollision(ball)

        for wall in self.elements["wall"]:
            for line in wall.lines:
                for ball in self.elements["ball"]:
                    if ball.isCollidedByLine(line) and not wall.isPosOn(self, ball.position):
                        ball.reboundByLine(line)

        if not self.isCelestialBodyMode:
            self.floor.position.x = self.screenToReal(self.screen.get_width()/2, self.x)
            self.floor.update(deltaTime)
            self.floor.draw(self)

        if self.isMoving and not self.isElementCreating:
            for element1 in self.elements["controlling"]:

                pos = pygame.mouse.get_pos()
                element1.highLighted = True

                try:
                    element1.velocity = Vector2(0, 0)
                except Exception as e:
                    ...

                allowToPlace = True
                for element2 in self.elements["all"]:
                    if element2.isMouseOn(self) and element2!= element1:
                        allowToPlace = False
                        break

                if allowToPlace:
                    element1.position.x = self.screenToReal(pos[0], self.x)
                    element1.position.y = self.screenToReal(pos[1], self.y)

                element1.update(deltaTime)

        self.updateFPS()

    def updateFPS(self) -> None:
        """更新帧率"""
        self.lastTime = self.currentTime
        self.currentTime = time.time()
        self.fpsSaver.append(self.currentTime - self.lastTime)
        self.fpsAverage = len(self.fpsSaver) / sum(self.fpsSaver)
        self.fpsMinimum = 1 / max(self.fpsSaver)
        if sum(self.fpsSaver) >= 1:
            del self.fpsSaver[0]

    def update(self) -> None:
        """主更新循环"""
        self.eventLoop()
        self.updateScreen()
        self.updateElements()
        self.updateMenu()
        if self.tempFrames > 0:
            self.tempFrames -= 1

    def findMaximumGravitationBall(self, ball : Ball) -> Ball | None:
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

            if G * ball.mass * ball2.mass / (distance ** 2 + 1e-6) > maxGravitation:
                result = ball2
                maxGravitation = G * ball.mass * ball2.mass / (distance ** 2 + 1e-6)

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

        if self.y - self.screenToReal(self.screen.get_height())/2 < 1.5e+7:
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

        if self.y - self.screenToReal(self.screen.get_height())/2 >= 1.5e+7:
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

class Menu:
    def __init__(self, pos : Vector2, optionsList = []) -> None:
        width, height = pygame.display.get_surface().get_size()
        self.width = width*3/100
        self.height = height*80/100

        self.x = pos.x
        self.y = pos.y + (height - self.height)/2

        self.optionsList = optionsList

        self.options = []
        for i in range(len(self.optionsList)):
            option = Option(Vector2(self.x+self.width*1/10, self.y+self.width*1/10+i*self.width*9/10), Vector2(self.width*8/10, self.width*8/10), self.optionsList[i]["type"], self.optionsList[i]["attrs"], self)
            option.name = self.optionsList[i]["name"]
            self.options.append(option)

    def isMouseOn(self) -> bool:
        """判断鼠标是否在菜单区域"""
        pos = Vector2(pygame.mouse.get_pos())
        return self.isPosOn(pos)

    def isPosOn(self, pos: Vector2) -> bool:
        """判断指定位置是否在菜单区域"""
        return pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.height  

    def draw(self, game : Game) -> None:
        """绘制菜单界面"""
        pygame.draw.rect(game.screen, (220, 220, 220), (self.x, self.y, self.width, self.height), border_radius=int(self.width*15/100))
        for option in self.options:
            option.draw(game)

class Option:
    """菜单选项类"""
    def __init__(self, pos : Vector2, size : Vector2, type: str, attrs_ : list, menu : Menu) -> None:
        self.x = pos.x
        self.y = pos.y
        self.width = size.x
        self.height = size.y
        self.type = type
        self.pos = pos
        self.name = ""
        self.creationPoints = []
        self.isAbsorption = False
        self.attrs = {}
        self.selected = False
        self.highLighted = False
        self.attrs_ = attrs_
        for attr in self.attrs_:
            self.attrs[attr["type"]] = attr["value"]
                
    def drawArrow(self, game : Game, startPos : tuple[float, float], endPos : tuple[float, float], color : pygame.Color) -> None:
        """绘制箭头（坐标参数用tuple而不是Vector2）"""
        pygame.draw.line(game.screen, color, startPos, endPos, 3)

        # 计算箭头的方向
        dx = endPos[0] - startPos[0]
        dy = endPos[1] - startPos[1]
        angle = math.atan2(dy, dx)

        # 箭头的大小
        arrowLength = 15
        arrowAngle = math.pi / 6  # 30度

        # 计算箭头的两个端点
        arrowPoint1 = (
            endPos[0] - arrowLength * math.cos(angle - arrowAngle), 
            endPos[1] - arrowLength * math.sin(angle - arrowAngle)
        )

        arrowPoint2 = (
            endPos[0] - arrowLength * math.cos(angle + arrowAngle), 
            endPos[1] - arrowLength * math.sin(angle + arrowAngle)
        )

        # 绘制箭头
        pygame.draw.polygon(game.screen, color, [endPos, arrowPoint1, arrowPoint2])

    def isMouseOn(self) -> bool:
        """判断鼠标是否在选项区域"""
        pos = pygame.mouse.get_pos()
        return self.isPosOn(Vector2(pos))

    def isPosOn(self, pos : Vector2) -> bool:
        """判断指定位置是否在选项区域"""
        return pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.height  

    def ballCreate(self, game : Game) -> None:
        """创建球体"""
        game.isScreenMoving = False
        game.isMoving = False
        game.isElementCreating = True
        game.isDragging = False
        game.circularVelocityFactor = 1
        radius = float(self.attrs["radius"])
        color = self.attrs["color"]
        mass = float(self.attrs["mass"])
        ball = None
        self.selected = True
        self.highLighted = True
        coordinator = Coordinator(0, 0, 200, game)
        self.additionVelocity = ZERO

        while game.isElementCreating:

            game.isElementCreating = True
            mousePosition = pygame.mouse.get_pos()
            game.update()

            maximumGravitationBall = game.findMaximumGravitationBall(ball)
            if maximumGravitationBall is not None:
                maximumGravitationBallCopy = copy.deepcopy(maximumGravitationBall)
                maximumGravitationBallCopy.velocity = ZERO

            if game.isCelestialBodyMode and game.isCircularVelocityGetting and maximumGravitationBall is not None:

                if 0 <= game.circularVelocityFactor <= 1:
                    circularVelocityFactorColor = colorMiddle("green", "yellow", game.circularVelocityFactor)
                elif 1 <= game.circularVelocityFactor <= 2**0.5:
                    circularVelocityFactorColor = colorMiddle("yellow", "green", (game.circularVelocityFactor - 1) / (2**0.5 - 1))
                elif 2**0.5 <= game.circularVelocityFactor <= 2:
                    circularVelocityFactorColor = colorMiddle("red", "yellow", (game.circularVelocityFactor - 2**0.5))
                else:
                    circularVelocityFactorColor = "red"

                pygame.draw.circle(game.screen, circularVelocityFactorColor, game.realToScreen(maximumGravitationBall.position, Vector2(game.x, game.y)).toTuple(), game.realToScreen(ball.position.distance(maximumGravitationBall.position)), 3)
                velocity = ball.getCircularVelocity(maximumGravitationBallCopy, game.circularVelocityFactor * (1 if game.isCircularVelocityDirectionAnticlockwise else -1))
                self.drawArrow(game, mousePosition, game.realToScreen(ball.position + velocity.copy().normalize() * abs(velocity) ** 0.5 * 2, Vector2(game.x, game.y)).toTuple(), circularVelocityFactorColor)
                
                if game.circularVelocityFactor != 1:
                    circularVelocityFactorText = game.fontSmall.render(f"{game.circularVelocityFactor: .1f}x", True, circularVelocityFactorColor)
                    circularVelocityFactorRect =  circularVelocityFactorText.get_rect()
                    circularVelocityFactorRect.x = pygame.mouse.get_pos()[0] + game.fontSmall.get_height()
                    circularVelocityFactorRect.y = pygame.mouse.get_pos()[1] - game.fontSmall.get_height() - game.realToScreen(ball.radius)
                    game.screen.blit(circularVelocityFactorText, circularVelocityFactorRect)

            if not game.isDragging:

                ball = Ball(Vector2(game.screenToReal(mousePosition[0], game.x), game.screenToReal(mousePosition[1], game.y)), radius, color, mass, ZERO, [ZERO], True)
                self.creationPoints = [ball.position, ball.position]
                ball.draw(game)
                radiusText = game.fontSmall.render(f"半径 = {radius}", True, colorSuitable(ball.color, game.background))
                radiusTextRect =  radiusText.get_rect()
                radiusTextRect.x = mousePosition[0]
                radiusTextRect.y = mousePosition[1]
                game.screen.blit(radiusText, radiusTextRect)

                massText = game.fontSmall.render(f"质量 = {mass: .1f}", True, colorSuitable(ball.color, game.background))
                massTextRect =  massText.get_rect()
                massTextRect.x = mousePosition[0]
                massTextRect.y = mousePosition[1] + radiusText.get_height()
                game.screen.blit(massText, massTextRect)

            if game.isDragging:

                if not game.isCelestialBodyMode or not game.isCircularVelocityGetting:
                    startPos = (game.realToScreen(ball.position.x, game.x), game.realToScreen(ball.position.y, game.y))
                    endPos = (game.realToScreen(self.creationPoints[1].x, game.x), game.realToScreen(self.creationPoints[1].y, game.y))

                    self.creationPoints[1] = Vector2(game.screenToReal(mousePosition[0], game.x), game.screenToReal(mousePosition[1], game.y))

                    if coordinator.isMouseOn():
                        self.drawArrow(game, startPos, endPos, "yellow")
                    else:
                        self.drawArrow(game, startPos, endPos, "blue")

                    ball.draw(game)
                    coordinator.position = ball.position
                    self.additionVelocity = (self.creationPoints[1] - self.creationPoints[0]) * 2
                    coordinator.update(game)
                    coordinator.draw(game, self)

                else:
                    ball.position = Vector2(game.screenToReal(mousePosition[0], game.x), game.screenToReal(mousePosition[1], game.y))
                    ball.draw(game)
                    coordinator.position = ball.position
                    coordinator.update(game)
                    coordinator.draw(game, self)

            pygame.display.update()
            for event in pygame.event.get():

                game.isPressed = False
                if event.type == pygame.MOUSEBUTTONDOWN:

                    if event.button == 1:
                        allowToPlace = True
                        game.isDragging = True

                        for element in game.elements["all"]:
                            if element.isMouseOn(game):
                                allowToPlace = False
                                break
                            
                        if not game.elementMenu.isMouseOn() and allowToPlace:
                            ball = Ball(Vector2(game.screenToReal(mousePosition[0], game.x), game.screenToReal(mousePosition[1], game.y)), radius, color, mass, ZERO, [ZERO])
                    
                    elif event.button == 3 and game.isCelestialBodyMode and game.isCircularVelocityGetting:
                        game.isCircularVelocityDirectionAnticlockwise = not game.isCircularVelocityDirectionAnticlockwise

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:

                    if self.isMouseOn():
                        self.highLighted = False
                        self.selected = False
                        game.isElementCreating = False
                        break

                    elif game.elementMenu.isMouseOn():
                        for option in game.elementMenu.options:
                            if option.isMouseOn() and not option.selected:
                                game.isElementCreating = False
                                self.highLighted = False
                                self.selected = False
                                option.createElement(game, Vector2(mousePosition[0], mousePosition[1]))
                                break

                    elif not game.elementMenu.isMouseOn() or game.isDragging:
                        game.isDragging = False
                        ball = Ball(ball.position, radius, color, mass, Vector2(game.screenToReal(mousePosition[0], game.x) - ball.position.x, game.screenToReal(mousePosition[1], game.y) - ball.position.y) * 2, [], gravitation=game.isCelestialBodyMode)
                        maximumGravitationBall = game.findMaximumGravitationBall(ball)
                        if maximumGravitationBall is not None:
                            maximumGravitationBallCopy = copy.deepcopy(maximumGravitationBall)
                            maximumGravitationBallCopy.velocity = ZERO

                        if maximumGravitationBall is not None and game.isCelestialBodyMode and game.isCircularVelocityGetting:
                            ball.velocity = ball.getCircularVelocity(maximumGravitationBall, game.circularVelocityFactor * (1 if game.isCircularVelocityDirectionAnticlockwise else -1))

                        game.elements["all"].append(ball)
                        game.elements["ball"].append(ball)

                        for ball in game.elements["ball"]:
                            ball.displayedAcceleration = ball.acceleration + (ball.displayedAcceleration - ball.acceleration) * ball.displayedAccelerationFactor
                            ball.displayedAccelerationFactor = 1

                    else:
                        for option in game.elementMenu.options:
                            if option.isMouseOn():
                                game.isElementCreating = False
                                self.highLighted = False
                                self.selected = False
                                method = eval(f"option.{option.type}Create")
                                method(game)
                                break

                if event.type == pygame.MOUSEWHEEL and not game.isDragging:
                    
                    if not game.isCelestialBodyMode or not game.isCircularVelocityGetting:

                        if event.y == 1:
                            if game.isMassSetting:
                                mass += 0.1
                            else:
                                radius += 1

                        if event.y == -1:
                            if game.isMassSetting and mass > 0.2:
                                mass -= 0.1
                            elif radius > 1:
                                radius -= 1

                    else:

                        if event.y == 1:
                            game.circularVelocityFactor += 0.1

                        if event.y == -1:
                            game.circularVelocityFactor -= 0.1

                            if game.circularVelocityFactor < 0:
                                game.circularVelocityFactor = 0

                if event.type == pygame.KEYUP:

                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        game.isMassSetting = False

                    if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                        game.isCircularVelocityGetting = False
                        game.circularVelocityFactor = 1

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:
                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)
                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_z and game.isCtrlPressing and len(self.elements["all"]) > 0:
                        lastElement = game.elements["all"][-1]
                        game.elements["all"].remove(lastElement)
                        
                        for ball in self.elements["ball"]:
                            ball.displayedAcceleration = ball.acceleration + (ball.displayedAcceleration - ball.acceleration) * ball.displayedAccelerationFactor
                            ball.displayedAccelerationFactor = 1

                        for option in game.elementMenu.options:
                            if option.type == lastElement.type:
                                game.elements[option.type].remove(lastElement)
                                break

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.loadGame(f"default/{str(event.key - pygame.K_0)}")
                        loadedTipText = game.fontSmall.render(f"{game.gameName}加载成功", True, (0, 0, 0))
                        loadedTipRect = loadedTipText.get_rect(center=(game.screen.get_width()/2, game.screen.get_height()/2))
                       
                        game.update() 
                        game.screen.blit(loadedTipText, loadedTipRect)
                        pygame.display.update()
                        time.sleep(0.5)
                        game.lastTime = time.time()
                        game.currentTime = time.time()

                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        game.isMassSetting = True

                    if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                        game.isCircularVelocityGetting = True

                    if event.key == pygame.K_SPACE:
                        game.isPaused = not game.isPaused

                    if event.key == pygame.K_r:
                        game.elements["all"].clear()

                        for option in game.elementMenu.options:
                            game.elements[option.type].clear()

                    if event.key == pygame.K_ESCAPE:
                        game.isElementCreating = False
                        self.highLighted = False
                        self.selected = False
                        break

                    if event.key == pygame.K_p:

                        if game.isCelestialBodyMode:
                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "0"
                                    
                                if option["type"] == "gravity":
                                    option["value"] = "1"
                            game.GroundSurfaceMode()

                        else:
                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "0"

                                if option["type"] == "gravity":
                                    option["value"] = "1"

                            game.CelestialBodyMode()

                game.screenMove(event)

    def wallCreate(self, game : Game) -> None:
        """创建墙体"""
        game.isElementCreating = True
        self.highLighted = True
        self.selected = True
        clickNum = 0
        coordinator = Coordinator(0, 0, 0, game)

        while game.isElementCreating:
            game.isElementCreating = True
            game.update()

            if clickNum%4 == 3:
                self.creationPoints[3] = Vector2(self.creationPoints[0].x + (self.creationPoints[2].x - self.creationPoints[1].x), self.creationPoints[0].y + (self.creationPoints[2].y - self.creationPoints[1].y))
                wall = Wall(self.creationPoints, self.attrs["color"])
                game.elements["all"].append(wall)
                game.elements["wall"].append(wall)
                clickNum = 0

            if clickNum%4 == 2:
                pygame.draw.line(game.screen, self.attrs["color"], (game.realToScreen(self.creationPoints[0].x, game.x), game.realToScreen(self.creationPoints[0].y, game.y)), (game.realToScreen(self.creationPoints[1].x, game.x), game.realToScreen(self.creationPoints[1].y, game.y)))

                pos = pygame.mouse.get_pos()
                pos = Vector2(game.screenToReal(pos[0], game.x), game.screenToReal(pos[1], game.y))
                line1 = self.creationPoints[0] - self.creationPoints[1]
                line2 = pos - self.creationPoints[1]
                line3 = line2.projectVertical(line1)
                self.creationPoints[2] = self.creationPoints[1] + line3
                self.creationPoints[3] = Vector2(self.creationPoints[0].x + (self.creationPoints[2].x - self.creationPoints[1].x), self.creationPoints[0].y + (self.creationPoints[2].y - self.creationPoints[1].y))                        
                pygame.draw.polygon(game.screen, self.attrs["color"], [(game.realToScreen(self.creationPoints[0].x, game.x), game.realToScreen(self.creationPoints[0].y, game.y)), (game.realToScreen(self.creationPoints[1].x, game.x), game.realToScreen(self.creationPoints[1].y, game.y)), (game.realToScreen(self.creationPoints[2].x, game.x), game.realToScreen(self.creationPoints[2].y, game.y)), (game.realToScreen(self.creationPoints[3].x, game.x), game.realToScreen(self.creationPoints[3].y, game.y))])
                pygame.display.update()

            if clickNum%4 == 1:
                coordinator.width = 200
                coordinator.update(game)
                coordinator.draw(game, self)

                if coordinator.isMouseOn():
                    pygame.draw.line(game.screen, "yellow", (game.realToScreen(self.creationPoints[0].x, game.x), game.realToScreen(self.creationPoints[0].y, game.y)), (game.realToScreen(self.creationPoints[1].x, game.x), game.realToScreen(self.creationPoints[1].y, game.y)))
                else:
                    pygame.draw.line(game.screen, self.attrs["color"], (game.realToScreen(self.creationPoints[0].x, game.x), game.realToScreen(self.creationPoints[0].y, game.y)), pygame.mouse.get_pos())      
                
                pygame.display.update()

            if clickNum%4 == 0:
                coordinator.position = Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y))  
                coordinator.width = 10
                coordinator.update(game)
                coordinator.draw(game, self)
                pygame.display.update()

            for event in pygame.event.get():
                game.isPressed = False

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:

                        if not game.elementMenu.isMouseOn():
                            allowToPlace = True

                            for element in game.elements["ball"]:
                                if element.isMouseOn(game):
                                    allowToPlace = False
                                    break

                            if allowToPlace:

                                if clickNum%4 == 2:
                                    clickNum += 1

                                if clickNum%4 == 1:

                                    if not self.isAbsorption:
                                        self.creationPoints[1] = Vector2(game.screenToReal(event.pos[0], game.x), game.screenToReal(event.pos[1], game.y))
                                        self.isAbsorption = False
                                        
                                    else:
                                        self.isAbsorption = False
                                    clickNum += 1

                                if clickNum%4 == 0:
                                    self.creationPoints = [Vector2(game.screenToReal(event.pos[0], game.x), game.screenToReal(event.pos[1], game.y)) for i in range(4)]
                                    clickNum += 1

                        if self.isMouseOn():
                            self.highLighted = False
                            self.selected = False
                            game.isElementCreating = False
                            break

                        for option in game.elementMenu.options:
                            if option.isMouseOn():
                                game.isElementCreating = False
                                self.highLighted = False
                                self.selected = False
                                method = eval(f"option.{option.type}Create")
                                method(game)
                                break

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z and game.isCtrlPressing and len(self.elements["all"]) > 0:
                        lastElement = game.elements["all"][-1]
                        game.elements["all"].remove(lastElement)
                        
                        for ball in self.elements["ball"]:
                            ball.displayedAcceleration = ball.acceleration + (ball.displayedAcceleration - ball.acceleration) * ball.displayedAccelerationFactor
                            ball.displayedAccelerationFactor = 1

                        for option in game.elementMenu.options:
                            if option.type == lastElement.type:
                                game.elements[option.type].remove(lastElement)
                                break
                            
                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.loadGame(f"default/{str(event.key - pygame.K_0)}")
                        loadedTipText = game.fontSmall.render(f"{game.gameName}加载成功", True, (0, 0, 0))
                        loadedTipRect = loadedTipText.get_rect(center=(game.screen.get_width()/2, game.screen.get_height()/2))
                        
                        game.update()
                        game.screen.blit(loadedTipText, loadedTipRect)
                        pygame.display.update()
                        time.sleep(0.5)
                        game.lastTime = time.time()
                        game.currentTime = time.time()

                    if event.key == pygame.K_SPACE:
                        game.isPaused = not game.isPaused
                        
                    if event.key == pygame.K_r:
                        game.elements["all"].clear()
                        for option in game.elementMenu.options:
                            game.elements[option.type].clear()

                    if event.key == pygame.K_ESCAPE:
                        game.isElementCreating = False
                        self.highLighted = False
                        self.selected = False
                        break

                    if event.key == pygame.K_p:
                        if game.isCelestialBodyMode:
                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "0"

                                if option["type"] == "gravity":
                                    option["value"] = "1"
                                    
                            game.GroundSurfaceMode()

                            for option in game.environmentOptions:

                                if option["type"] == "mode":
                                    option["value"] = "1"

                                if option["type"] == "gravity":
                                    option["value"] = "0"

                            game.CelestialBodyMode()

                game.screenMove(event)

    def exampleCreate(self, game : Game) -> None:
        attrs = copy.deepcopy(self.attrs)
        attrs["path"] = attrs["path"].replace(".pkl", "")
        game.loadGame(attrs["path"])
        loadedTipText = game.fontSmall.render(f"{game.gameName}加载成功", True, (0, 0, 0))
        loadedTipRect = loadedTipText.get_rect(center=(game.screen.get_width()/2, game.screen.get_height()/2))
        
        game.update()
        game.screen.blit(loadedTipText, loadedTipRect)
        pygame.display.update()
        time.sleep(0.5)
        game.lastTime = time.time()
        game.currentTime = time.time()

    def elementEdit(self, game : Game, attrs : list) -> None:
        """打开编辑元素属性框"""
        inputMenu = InputMenu(Vector2(game.screen.get_width()/2, game.screen.get_height()/2), game, self)
        
        # 从元素实例获取实时属性值
        updated_attrs = []
        for attr in self.attrs_:

            # 创建属性字典的深拷贝
            newAttr = copy.deepcopy(attr)

            # 用当前元素的实际属性值更新
            newAttr["value"] = str(self.attrs[attr["type"]]) 
            updated_attrs.append(newAttr)
        
        inputMenu.options = updated_attrs  # 使用更新后的属性列表
        game.openEditor(inputMenu)

    def setAttr(self, name, value) -> None:
        """设置元素属性"""
        for atr in self.attrs_:
           if atr["type"] == name:
                atr["value"] = value

        self.attrs[name] = value

    def draw(self, game : Game) -> None:
        """绘制选项界面"""
        if self.highLighted:
            pygame.draw.rect(game.screen, "yellow", (self.x-3, self.y-3, self.width+6, self.height+6), border_radius=int(self.width*15/100))
        
        pygame.draw.rect(game.screen, (255, 255, 255), (self.x, self.y, self.width, self.height), border_radius=int(self.width*15/100))
        
        if self.type == "ball":
            pygame.draw.circle(game.screen, self.attrs["color"], (self.x+self.width/2, self.y+self.height/2), self.width/3)
        
        if self.type == "wall":
            pygame.draw.rect(game.screen, self.attrs["color"], (self.x+self.width/10, self.y+self.height/10, self.width*8/10, self.height*8/10))

        if self.type == "example":

            try:
                icon = pygame.image.load(self.attrs["icon"]).convert_alpha()

                # 调整图片大小以适应给定的宽度和高度
                scaled_icon = pygame.transform.scale(icon, (self.width, self.height))

                # 计算图片的中心位置
                icon_x = self.x + self.width / 2 - scaled_icon.get_width() / 2
                icon_y = self.y + self.height / 2 - scaled_icon.get_height() / 2

                # 绘制调整大小后的图片
                game.screen.blit(scaled_icon, (icon_x, icon_y))

            except KeyError:
                ...

            except FileNotFoundError:
                ...
            
    def createElement(self, game: Game, pos: Vector2):
        """创建元素对象"""
        x = pos.x
        y = pos.y

        if x > self.x and x < self.x + self.width and y > self.y and y < self.y + self.height:
            method = eval(f"self.{self.type}Create")
            method(game)

    def edit(self, game : Game, pos: Vector2) -> None:
        """编辑元素属性"""
        x = pos.x
        y = pos.y

        if x > self.x and x < self.x + self.width and y > self.y and y < self.y + self.height:
            self.elementEdit(game, list(self.attrs.keys()))

class SettingsButton:
    """设置按钮控件类"""
    def __init__(self, x, y, width, height) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # 加载图片并转换为透明格式
        originalIcon = pygame.image.load("static/settings.png").convert_alpha()
        
        # 调整图片大小
        self.icon = pygame.transform.scale(originalIcon, (self.width, self.height))

    def draw(self, game: Game) -> None:
        """绘制设置按钮"""
        game.screen.blit(self.icon, (self.x, self.y))

    def isMouseOn(self) -> bool:
        """判断鼠标是否在按钮上"""
        return self.isPosOn(Vector2(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]))

    def isPosOn(self, pos: Vector2) -> bool:
        """判断指定坐标是否在按钮上"""
        return pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.height

class InputBox:
    """输入框控件类"""
    def __init__(self, x, y, width, height, option, target, text="") -> None:
        self.rect = pygame.Rect(x, y, width-100, height)
        self.colorInactive = pygame.Color("lightskyblue3")
        self.colorActive = pygame.Color("dodgerblue2")
        self.color = self.colorInactive
        self.text = text
        self.font = pygame.font.Font(None, int(height))
        self.textSurface = self.font.render(self.text, True, self.color)
        self.active = False
        self.cursorVisible = True
        self.cursorTimer = 0
        self.option = option
        self.target = target
        self.active = False
        self.isColorError = False

        if self.option["type"] != "color":
            self.min = float(self.option["min"])
            self.max = float(self.option["max"])

    def handleEvent(self, event, game : Game) -> None:
        """处理输入事件"""

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 如果点击了输入框区域，激活输入框
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.colorActive if self.active else self.colorInactive

        if event.type == pygame.KEYDOWN:

            if self.active:

                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:

                    if not self.isColorError:
                        game.isEditing = False
                        self.attrUpdate(self.target)

                    else:
                        messagebox.showerror("错误", "您输入的颜色不合法!!!\n请输入合法的颜色编号或名称!")
                        game.isEditing = True

                else:

                    if self.option["type"] != "color":

                        if event.key == pygame.K_BACKSPACE:
                            self.text = self.text[: -1]

                        if event.unicode.isdigit() or event.unicode == "." or event.unicode == "-":

                            try:
                                self.text += event.unicode

                                if float(self.text) < self.min:
                                    self.text = str(self.min)

                                elif float(self.text) > self.max:
                                    self.text = str(self.max)

                            except ValueError:
                                self.text = self.text[: -1]

                    else:

                        if event.key == pygame.K_BACKSPACE:
                            self.text = self.text[: -1]

                        if event.unicode.isalnum() or event.unicode == "#":
                            self.text += event.unicode

                        self.isColorError = False

                        try:

                            if len(self.text) != 0 and self.text[0] == "#":
                                self.text = self.text[0: 7]

                            pygame.Color(self.text)
                            self.attrUpdate(self.target)

                        except ValueError:
                            self.isColorError = True
                        
            game.lastTime = game.currentTime
            game.currentTime = time.time()
            self.textSurface = self.font.render(self.text, True, self.color)

    def attrUpdate(self, target) -> None:
        """更新目标属性"""
        if self.text == "":
            target.setAttr(self.option["type"], self.option["min"])
        else:
            target.setAttr(self.option["type"], self.text)

    def update(self) -> None:
        """更新输入框状态"""

        # 更新光标状态
        self.cursorTimer += 1

        if self.cursorTimer >= 30:
            self.cursorVisible = not self.cursorVisible
            self.cursorTimer = 0

    def draw(self, screen) -> None:
        """绘制输入框"""

        # 绘制输入框和文本
        screen.blit(self.textSurface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

        # 渲染光标
        if self.active and self.cursorVisible:
            cursorPos = self.font.render(self.text, True, self.color).get_width() + self.rect.x + 5
            pygame.draw.line(screen, self.color, (cursorPos, self.rect.y + 5), (cursorPos, self.rect.y + 27), 2)

class InputMenu(Element):
    """输入菜单界面类"""
    def __init__(self, position: Vector2, game: Game, target) -> None:
        # 每个输入框的垂直间距
        self.verticalSpacing = 100
        self.position = position
        self.width = game.screen.get_width()/3
        self.height = 0
        self.x = position.x - self.width/2
        self.y = position.y - self.height/2
        self.commitFunction = ""
        self.font = pygame.font.Font("static/HarmonyOS_Sans_SC_Medium.ttf", int(self.verticalSpacing/6))
        self.options = []
        self.inputBoxes = []
        self.target = target

    def update(self, game: Game) -> None:
        """更新输入菜单布局"""
        # game.isPaused = False
        game.tempFrames = 1
        length = len(self.options)
        self.height = 0
        self.inputBoxes.clear()

        for i in range(length):
            option = self.options[i]
            # 计算每个输入框的y坐标
            y = self.y + 10 + i * self.verticalSpacing 
            inputBox = InputBox(self.x + self.width*3/10, y, self.width - self.width*3/10, self.verticalSpacing/3, option, self.target , str(option["value"]))
            self.height += self.verticalSpacing  # 更新InputMenu的高度
            self.inputBoxes.append(inputBox)

        self.x = self.position.x - self.width/2
        self.y = self.position.y - self.height/2
        game.lastTime = game.currentTime
        game.currentTime = time.time()

    def updateBoxes(self, event, game) -> None:
        """更新输入框状态"""
        for box in self.inputBoxes:
            box.handleEvent(event, game)

    def draw(self, game: Game) -> None:
        """绘制输入菜单"""
        pygame.draw.rect(game.screen, (255, 255, 255), (self.x, self.y, self.width, self.height), border_radius=int(self.width*2/100))

        # 绘制所有输入框和选项文本
        length = len(self.options)

        for i in range(length):
            optionType = self.options[i]["type"]
            inputBox = self.inputBoxes[i]

            # 绘制选项文本
            optionText = self.font.render(game.translation[optionType], True, (0, 0, 0))
            game.screen.blit(optionText, (self.x , inputBox.rect.y))

            # 绘制输入框
            inputBox.draw(game.screen)

class ControlOption:
    """控制选项类"""
    def __init__(self, name, x, y, width, height, color) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def attrEditor(self, game: Game, target) -> None:
        """打开属性编辑器"""
        inputMenu = InputMenu(Vector2(game.screen.get_width()/2, game.screen.get_height()/2), game, target)

        for option in game.elementMenu.optionsList:
            if option["type"] == target.type:
                inputMenu.options = target.attrs
                inputMenu.target = target

        game.openEditor(inputMenu)

    def copy(self, game: Game, target) -> None:
        """复制目标"""
        target.copy(game)

    def delete(self, game: Game, target: Element) -> None:
        """删除目标"""
        for type in game.elements.keys():
            if target in game.elements[type]:
                game.elements[type].remove(target)
        
        for ball in game.elements["ball"]:
            ball.displayedAcceleration = ball.acceleration + (ball.displayedAcceleration - ball.acceleration) * ball.displayedAccelerationFactor
            ball.displayedAccelerationFactor = 1

    def follow(self, game: Game, target: Element) -> None:
        """视角跟随目标"""
        target.isShowingInfo = False
        target.isFollowing = not target.isFollowing

        for element in game.elements["all"]:
            if element is not target:
                element.isFollowing = False

    def showInfo(self, game: Game, target: Element):
        """显示目标信息"""
        target.isFollowing = False
        target.isShowingInfo = not target.isShowingInfo

    def addVelocity(self, game: Game, target: Element) -> None:
        """添加速度"""
        tempOption = Option(ZERO, Vector2(0, 0), "temp", [], game.elementMenu)
        isAdding = True
        target.highLighted = True
        game.update()
        game.isPaused = True

        coordinator = Coordinator(0, 0, 200, game)
        coordinator.position = target.position
        coordinator.update(game)
        tempOption.creationPoints = [target.position, target.position]
        self.additionVelocity = tempOption.creationPoints[1] - tempOption.creationPoints[0]
        originVelocity = target.velocity
        originAcceleration = target.acceleration

        while isAdding:
            target.position = tempOption.creationPoints[0]
            startPos = game.realToScreen(target.position, Vector2(game.x, game.y)).toTuple()
            endPos = game.realToScreen(tempOption.creationPoints[1], Vector2(game.x, game.y)).toTuple()
            target.velocity = originVelocity
            target.acceleration = originAcceleration

            game.update()
            pos = pygame.mouse.get_pos()
            tempOption.creationPoints[1] = game.screenToReal(Vector2(pos), Vector2(game.x, game.y))

            if coordinator.isMouseOn():
                tempOption.drawArrow(game, startPos, endPos, "yellow")
            else:
                tempOption.drawArrow(game, startPos, endPos, "blue")

            coordinator.update(game)
            coordinator.draw(game, tempOption, str(round(abs(self.additionVelocity)/10))+"m/s")
            self.additionVelocity = tempOption.creationPoints[1] - tempOption.creationPoints[0]

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    target.displayedVelocity = target.velocity + (target.displayedVelocity - target.velocity) * target.displayedVelocityFactor
                    target.displayedVelocityFactor = 1
                    target.velocity += tempOption.creationPoints[1] - tempOption.creationPoints[0]
                    isAdding = False
                    target.highLighted = False

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_g:
                        game.saveGame("autosave")

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.loadGame(f"default/{str(event.key - pygame.K_0)}")
                        loadedTipText = game.fontSmall.render(f"{game.gameName}加载成功", True, (0, 0, 0))
                        loadedTipRect = loadedTipText.get_rect(center=(game.screen.get_width()/2, game.screen.get_height()/2))
                        
                        game.update()
                        game.screen.blit(loadedTipText, loadedTipRect)
                        pygame.display.update()
                        time.sleep(0.5)
                        game.lastTime = time.time()
                        game.currentTime = time.time()

                    if event.key == pygame.K_ESCAPE:
                        isAdding = False
                        target.highLighted = False

            game.lastTime = game.currentTime
            game.currentTime = time.time()
            pygame.display.update()
        
        game.isPaused = False

    def clearVelocity(self, game: Game, target: Element) -> None:
        """清除速度"""
        target.displayedVelocity = target.velocity
        target.displayedVelocityFactor = 1
        target.velocity = ZERO

    def addForce(self, game: Game, target: Element) -> None:
        """添加力"""
        tempOption = Option(ZERO, Vector2(0, 0), "temp", [], game.elementMenu)
        isAdding = True
        target.highLighted = True
        game.update()
        game.isPaused = True

        coordinator = Coordinator(0, 0, 200, game)
        coordinator.position = target.position
        coordinator.update(game)
        tempOption.creationPoints = [target.position, target.position]
        self.additionForce = tempOption.creationPoints[1] - tempOption.creationPoints[0]
        originVelocity = target.velocity
        originAcceleration = target.acceleration

        while isAdding:
            target.position = tempOption.creationPoints[0]
            startPos = game.realToScreen(target.position, Vector2(game.x, game.y)).toTuple()
            endPos = game.realToScreen(tempOption.creationPoints[1], Vector2(game.x, game.y)).toTuple()
            target.velocity = originVelocity
            target.acceleration = originAcceleration

            game.update()
            pos = pygame.mouse.get_pos()
            tempOption.creationPoints[1] = Vector2(game.screenToReal(pos[0], game.x), game.screenToReal(pos[1], game.y))

            if coordinator.isMouseOn():
                tempOption.drawArrow(game, startPos, endPos, "yellow")
            else:
                tempOption.drawArrow(game, startPos, endPos, "red")

            coordinator.update(game)
            coordinator.draw(game, tempOption, str(round(abs(self.additionForce))/10)+"N")
            self.additionForce = tempOption.creationPoints[1] - tempOption.creationPoints[0]

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    game.exit()

                elif event.type == pygame.ACTIVEEVENT:

                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)

                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    target.displayedAcceleration = target.acceleration + (target.displayedAcceleration - target.acceleration) * target.displayedAccelerationFactor
                    target.displayedAccelerationFactor = 1
                    target.force(self.additionForce)
                    isAdding = False
                    target.highLighted = False

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_g:
                        game.saveGame("manualsave")

                    if event.key == pygame.K_l:
                        game.loadGame("autosave")

                    if event.key == pygame.K_k:
                        game.loadGame("manualsave")

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.loadGame(f"default/{str(event.key - pygame.K_0)}")
                        loadedTipText = game.fontSmall.render(f"{game.gameName}加载成功", True, (0, 0, 0))
                        loadedTipRect = loadedTipText.get_rect(center=(game.screen.get_width()/2, game.screen.get_height()/2))
                        game.screen.blit(loadedTipText, loadedTipRect)
                        game.update()
                        pygame.display.update()
                        time.sleep(0.5)
                        game.lastTime = time.time()
                        game.currentTime = time.time()

                    if event.key == pygame.K_ESCAPE:
                        isAdding = False
                        target.highLighted = False

            game.lastTime = game.currentTime
            game.currentTime = time.time()
            pygame.display.update()
        
        game.isPaused = False

    def clearForce(self, game: Game, target: Element) -> None:
        """清除所有外力"""
        target.displayedAcceleration = target.acceleration
        target.displayedAccelerationFactor = 1
        target.artificialForces.clear()

    def isMouseOn(self) -> bool:
        """判断鼠标是否在控件上"""
        return self.isPosOn(Vector2(pygame.mouse.get_pos()))

    def isPosOn(self, pos: Vector2) -> bool:
        """判断指定坐标是否在控件上"""
        return self.x < pos.x < self.x + self.width and self.y < pos.y < self.y + self.height

    def draw(self, game: Game) -> None:
        """绘制控件"""
        pygame.draw.rect(game.screen, self.color, (self.x, self.y, self.width, self.height), border_radius=int(self.width*2/100))
        text = game.translation[self.name]
        textSurface = game.fontSmall.render(text, True, (0, 0, 0))
        game.screen.blit(textSurface, (self.x + self.width/2 - textSurface.get_width()/2, self.y + self.height/2 - textSurface.get_height()/2))

class ElementController:
    """元素控制器类"""
    def __init__(self, element: Element, position: Vector2) -> None:
        self.x = position.x
        self.y = position.y
        self.optionWidth = 300
        self.optionHeight = 50
        self.element = element
        self.controlOptionsList = []
        self.controlOptions = []

    def control(self, game: Game) -> None:
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
        return self.x < pos.x < self.x + self.optionWidth and self.y < pos.y < self.y + self.optionHeight * len(self.controlOptionsList)

    def update(self, game: Game) -> None:
        """更新控制器"""
        options = game.elementMenu.optionsList

        for option in options:
            if option["type"] == self.element.type:
                self.controlOptionsList = option["controlOptions"]

        screenHeight = game.screen.get_height()

        if self.y + len(self.controlOptionsList)*self.optionHeight > screenHeight:
                self.y -= len(self.controlOptionsList)*self.optionHeight + 50   

        currentY = self.y  # 初始 y 坐标

        for option in self.controlOptionsList:

            controlOption = ControlOption(
                    option["type"], 
                    self.x + 30, # x 坐标保持不变
                    currentY, # 使用当前 y 坐标
                    self.optionWidth, 
                    self.optionHeight, 
                    "white"  # 颜色默认白色
                )

            self.controlOptions.append(controlOption)

            currentY += self.optionHeight + 5  # 更新 y 坐标，增加当前 ControlOption 的高度和间距

    def draw(self, game: Game) -> None:
        """绘制控制器"""
        for option in self.controlOptions:
            option.draw(game)
            