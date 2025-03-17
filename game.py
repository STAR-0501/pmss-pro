import os
from basic import *
from tkinter import messagebox
import pygame
import sys, time, json, ctypes, pickle

def setCapsLock(state=True):
    """
    state=True: 开启大写
    state=False: 关闭大写
    """
    VK_CAPITAL = 0x14
    current = ctypes.windll.user32.GetKeyState(VK_CAPITAL)
    if (current & 0xFFFF) != int(state):
        ctypes.windll.user32.keybd_event(VK_CAPITAL, 0, 0x1, 0)  # 按下
        ctypes.windll.user32.keybd_event(VK_CAPITAL, 0, 0x3, 0)  # 释放

# 物理运动模拟系统主游戏类
class Game:
    # 初始化游戏引擎和系统设置
    def __init__(self):
        pygame.init()
        self.isPaused = False
        self.isElementCreating = False
        self.isMoving = False
        self.isScreenMoving = False
        self.isMassSetting = False
        self.isCtrlPressing = False
        self.isEditing = False
        self.isElementControlling = False
        self.isPressed = False
        self.isDragging = False
        self.isCelestialBodyMode = False
        self.isModeChangingNaturally = False

        self.screen = pygame.display.set_mode()
        pygame.display.set_caption("Physics Motion Simulation System Beta")
        icon = pygame.image.load("static/icon.png").convert_alpha()
        pygame.display.set_icon(icon)

        self.pos = (0,0)   # 鼠标屏幕坐标，而非真实坐标
        self.font = pygame.font.Font("static/HarmonyOS_Sans_SC_Medium.ttf", int(self.screen.get_width()/130))
        self.ratio = 5
        self.x = self.screen.get_width()/2 / self.ratio
        self.y = self.screen.get_height() / self.ratio
        self.menu : Menu = None
        self.currentTime = time.time()
        self.lastTime = self.currentTime
        self.fpsAverage = 0
        self.fpsMinimum = 0
        self.rightMove = 0
        self.upMove = 0
        self.speed = 1
        self.floor = Wall([Vector2(0,-10), Vector2(self.screen.get_width(), -10), Vector2(self.screen.get_width(), self.screen.get_height()), Vector2(0, self.screen.get_height())], (200,200,200))
        self.isFloorIllegal = False
        self.background = "lightgrey"
        self.settingsButton = SettingsButton(0, 0, 50, 50)
        self.fpsSaver = []

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

    # 退出游戏并恢复输入法设置
    def exit(self):
        setCapsLock(False)
        self.saveGame()
        print("游戏退出")
        pygame.quit()
        sys.exit()

    # 测试方法（预留）
    def test(self):
        ...

    def saveGame(self):
        # 创建一个新的字典，用于存储可序列化的属性
        serializable_dict = {}
        
        # 遍历 self.__dict__，排除不可序列化的对象
        for attr, value in self.__dict__.items():
            if attr != "screen":
                try:
                    # 尝试序列化对象，如果成功则添加到 serializable_dict 中
                    pickle.dumps(value)
                    serializable_dict[attr] = value
                except (pickle.PicklingError, TypeError):
                    # 如果序列化失败，跳过该属性
                    ...
        os.makedirs("savefile", exist_ok=True)
        # 将可序列化的字典保存到文件
        with open(f"savefile/{int(self.currentTime)}.pkl", "wb") as f:
            pickle.dump(serializable_dict, f)
            print("游戏数据保存成功")
            f.close()

    def loadGame(self, gameFile=""):
        # 保存当前的 screen 属性
        current_screen = getattr(self, 'screen', None)
        if gameFile == "":
            gameFile = os.listdir("savefile")[-2]

        print(f"正在加载游戏数据：{gameFile}")
        try:
            with open(f"savefile/{gameFile}", "rb") as f:
                # 加载序列化的字典
                serializable_dict = pickle.load(f)
                
                # 更新 self.__dict__，只更新可序列化的属性
                self.__dict__.update(serializable_dict)
                
                # 恢复 screen 属性
                if current_screen is not None:
                    self.screen = current_screen
                self.lastTime = time.time()
                self.currentTime = time.time()
                print("游戏数据加载成功")
                f.close()
        except FileNotFoundError:
            ...


    # 颜色字符串转RGB元组
    def colorStringToTuple(self, color: str) -> tuple[int, int, int]:
        # 如果是颜色名称格式，先转换为pygame颜色对象获取RGB值
        if not color.startswith('#'):
            try:
                c = pygame.Color(color.lower())
                return (c.r, c.g, c.b)
            except ValueError:
                # 如果颜色名称无效，返回默认黑色
                return (0, 0, 0)
        
        # 处理十六进制字符串格式
        return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))


    # 设置环境属性
    def setAttr(self, name, value):
        for option in self.environmentOptions:
            if option["type"] == name:
                option["value"] = value
                break

    # 实际坐标转屏幕坐标
    def realToScreen(self, r, x=0):
        return (r + x) * self.ratio

    # 屏幕坐标转实际坐标
    def screenToReal(self, r, x=0):
       return r / self.ratio - x

    # 事件处理主循环
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_o:
                    
                    print(self.isScreenMoving)

            if event.type == pygame.QUIT:
                self.exit()
            elif event.type == pygame.ACTIVEEVENT:
                if event.gain == 0 and event.state == 2:
                    setCapsLock(False)
                elif event.gain == 1 and event.state == 1:
                    setCapsLock(True)
            if event.type == pygame.MOUSEBUTTONUP:
                self.pos = pygame.mouse.get_pos()
                if event.button == 1:
                    for option in self.menu.options:
                        option.createElement(self, Vector2(self.pos))  # createElement里会判定对应的按钮是否被点击，并生成对应的物体
                if event.button == 3:
                    for option in self.menu.options:
                        option.edit(self, Vector2(self.pos))  # edit里会判定对应的按钮是否被点击，并编辑对应的物体



            if event.type == pygame.MOUSEWHEEL:
                speed = 0.5
                if event.y == 1 and self.ratio < 15:
                    if not self.isCtrlPressing:
                        b_x = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                        b_y = self.screenToReal(pygame.mouse.get_pos()[1], self.y)
                        self.ratio += speed
                        n_x = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                        n_y = self.screenToReal(pygame.mouse.get_pos()[1], self.y)
                        self.x += (n_x - b_x)
                        self.y += (n_y - b_y)
                    else:
                        b_x = self.screenToReal(self.screen.get_width()/2, self.x)
                        b_y = self.screenToReal(self.screen.get_height()/2, self.y)
                        self.ratio += speed
                        n_x = self.screenToReal(self.screen.get_width()/2, self.x)
                        n_y = self.screenToReal(self.screen.get_height()/2, self.y)
                        self.x += (n_x - b_x)
                        self.y += (n_y - b_y)

                elif event.y == -1 and self.ratio > 1:
                    if not self.isCtrlPressing:
                        b_x = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                        b_y = self.screenToReal(pygame.mouse.get_pos()[1], self.y)
                        self.ratio -= speed
                        n_x = self.screenToReal(pygame.mouse.get_pos()[0], self.x)
                        n_y = self.screenToReal(pygame.mouse.get_pos()[1], self.y)
                        self.x += (n_x - b_x)
                        self.y += (n_y - b_y)
                    else:
                        b_x = self.screenToReal(self.screen.get_width()/2, self.x)
                        b_y = self.screenToReal(self.screen.get_height()/2, self.y)
                        self.ratio -= speed
                        n_x = self.screenToReal(self.screen.get_width()/2, self.x)
                        n_y = self.screenToReal(self.screen.get_height()/2, self.y)
                        self.x += (n_x - b_x)
                        self.y += (n_y - b_y)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.pos = pygame.mouse.get_pos()
                if event.button == 1 and not self.menu.isMouseOn() and not self.isElementCreating and not self.isElementControlling and not self.isEditing:
                    self.isMoving = True
                    self.isScreenMoving = True
                    
                    for element in self.elements["all"]:
                        if(element.isMouseOn(self)):
                            self.elements["controlling"].append(element)
                            self.isScreenMoving = False

                
                if event.button == 3 and not self.menu.isMouseOn():
                    self.isElementControlling = True
                    for element in self.elements["all"]:
                        if(element.isMouseOn(self)):
                            element.highLighted = True
                            self.update()
                            pygame.display.update()
                            elementController = ElementController(element, Vector2(self.pos))
                            while self.isElementControlling:   
                                self.update_fps()
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
                                        if event.key == pygame.K_z and self.isCtrlPressing:
                                            lastElement = self.elements["all"][-1]
                                            self.elements["all"].remove(lastElement)
                                            for option in self.menu.options:
                                                if option.type == lastElement.type:
                                                    self.elements[option.type].remove(lastElement)
                                                    break
                                            
                                        if event.key == pygame.K_g:
                                            self.saveGame()
                                        if event.key == pygame.K_l:
                                            self.loadGame()
                                        if pygame.K_1 <= event.key <= pygame.K_9:
                                            self.loadGame(f"default/{str(event.key - pygame.K_0)}.pkl")

                                        if event.key == pygame.K_r:
                                            self.elements["all"] = []
                                            for option in self.menu.options:
                                                self.elements[option.type] = []
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
                            
            if event.type == pygame.MOUSEMOTION:
                if self.isScreenMoving:
                    for element in self.elements["ball"]:
                        element.highLighted = False
                        element.isFollowing = False
                    self.x += self.screenToReal(pygame.mouse.get_pos()[0] - self.pos[0])
                    if not self.isFloorIllegal or self.screenToReal(pygame.mouse.get_pos()[1] - self.pos[1]) > 0:
                        self.y += self.screenToReal(pygame.mouse.get_pos()[1] - self.pos[1])
                    self.pos = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.settingsButton.isMouseOn():
                        self.openEditor(self.inputMenu)

                    self.isMoving = False
                    self.isScreenMoving = False
                    self.elements["controlling"] = []

                if event.button == 2:
                    for element in self.elements["all"]:
                        if(element.isMouseOn(self)):
                            element.copy(self)
                            break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and self.isCtrlPressing:
                    lastElement = self.elements["all"][-1]
                    self.elements["all"].remove(lastElement)
                    for option in self.menu.options:
                        if option.type == lastElement.type:
                            self.elements[option.type].remove(lastElement)
                            break
                if event.key == pygame.K_SPACE:
                    self.isPaused = not self.isPaused
                if event.key == pygame.K_r:
                    self.elements["all"] = []
                    for option in self.menu.options:
                        self.elements[option.type] = []
                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self.isCtrlPressing = True
                if event.key == pygame.K_m:
                    self.openEditor(self.inputMenu)
                if event.key == pygame.K_g:
                    self.saveGame()
                if event.key == pygame.K_l:
                    self.loadGame()
                if pygame.K_1 <= event.key <= pygame.K_9:
                    self.loadGame(f"default/{str(event.key - pygame.K_0)}.pkl")
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
                    

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    self.isCtrlPressing = False

            self.screenMove(event)
            
    # 打开参数编辑器
    def openEditor(self, inputMenu):
        inputMenu.update(self)
        self.isEditing = True
        inputMenu.update(self)
        while self.isEditing:
            inputMenu.draw(self)
            pygame.display.update()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.exit()
                elif e.type == pygame.ACTIVEEVENT:
                    if e.gain == 0 and e.state == 2:
                        setCapsLock(False)
                    elif e.gain == 1 and e.state == 1:
                        setCapsLock(True)
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_z and self.isCtrlPressing:
                        lastElement = self.elements["all"][-1]
                        self.elements["all"].remove(lastElement)
                        for option in self.menu.options:
                            if option.type == lastElement.type:
                                self.elements[option.type].remove(lastElement)
                                break
                    if e.key == pygame.K_m or e.key == pygame.K_ESCAPE or e.key == pygame.K_RETURN:
                        self.isEditing = False
                inputMenu.updateBoxes(e, self)
        self.update_fps()

    # 处理屏幕移动控制
    def screenMove(self, event):
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

    # 更新屏幕状态
    def update_screen(self):
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

    # 更新菜单界面
    def update_menu(self):
        w, h = self.screen.get_size()
        if self.menu == None:
            self.menu = Menu(Vector2(w, h))
        self.menu.draw(game=self)

        if self.speed != 0:
            if self.fpsAverage / abs(self.speed) ** 0.5 < 60 or self.fpsMinimum / abs(self.speed) ** 0.5 < 30:
                fpsTextColor = "red"
            elif self.fpsMinimum / abs(self.speed) ** 0.5 < 60:
                fpsTextColor = "darkorange"
            else:
                fpsTextColor = "darkgreen"
        else:
            fpsTextColor = "darkgreen"
        fpsText = self.font.render(f"fps = {self.fpsAverage:.0f} / {self.fpsMinimum:.0f}", True, fpsTextColor)
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
        objectCountText = self.font.render(f"物体数量 = {len(self.elements['all'])}", True, objectCountTextColor)
        objectCountTextRect =  objectCountText.get_rect()
        objectCountTextRect.x = self.screen.get_width() - objectCountText.get_width()
        objectCountTextRect.y = fpsText.get_height()
        self.screen.blit(objectCountText, objectCountTextRect)

        mousePosText = self.font.render(f"鼠标位置 = ({int(self.screenToReal(pygame.mouse.get_pos()[0], self.x))},{int(self.screenToReal(pygame.mouse.get_pos()[1], self.y))})", True, "black")
        mousePosTextRect =  mousePosText.get_rect()
        mousePosTextRect.x = self.screen.get_width() - mousePosText.get_width()
        mousePosTextRect.y = fpsText.get_height() + objectCountText.get_height()
        self.screen.blit(mousePosText, mousePosTextRect)

        ratioText = self.font.render(f"缩放比例 = {self.ratio}x", True, "black")
        ratioTextRect =  ratioText.get_rect()
        ratioTextRect.x = self.screen.get_width() - ratioText.get_width()        
        ratioTextRect.y = fpsText.get_height() + objectCountText.get_height() + mousePosText.get_height()
        self.screen.blit(ratioText, ratioTextRect)

        speedText = self.font.render(f"倍速 = {self.speed:.1f}x", True, "black") 
        speedTextRect =  speedText.get_rect()
        speedTextRect.x = self.screen.get_width() - speedText.get_width()
        speedTextRect.y = fpsText.get_height() + objectCountText.get_height() + mousePosText.get_height() + ratioText.get_height()
        self.screen.blit(speedText, speedTextRect)

        pauseText = self.font.render(f"已暂停", True, "red")
        pauseTextRect =  pauseText.get_rect()
        pauseTextRect.x = self.screen.get_width() - pauseText.get_width()
        pauseTextRect.y = fpsText.get_height() + objectCountText.get_height() + mousePosText.get_height() + ratioText.get_height() + speedText.get_height()
        if self.isPaused:
            self.screen.blit(pauseText, pauseTextRect)

    # 更新所有物理元素状态
    def update_elements(self):
        for element in self.groundElements["all"]:
            if element.position.y <= -150000:
                self.groundElements["all"].remove(element)
                self.groundElements[element.type].remove(element)
                self.celestialElements["all"].append(element)
                self.celestialElements[element.type].append(element)
        
        for element in self.celestialElements["all"]:
            if element.position.y >= -150000:
                self.groundElements["all"].append(element)
                self.groundElements[element.type].append(element)
                self.celestialElements["all"].remove(element)
                self.celestialElements[element.type].remove(element)    
        
        dt = self.currentTime - self.lastTime
        for element1 in self.elements["all"]:
            element1.draw(self)
            if not self.isPaused:
                element1.update(dt * self.speed)

        for ball in self.elements["ball"]:
            ball.resetForce(True)
            
        for ball1 in self.elements["ball"]:
            if ball1.isFollowing:
                try:
                    self.elements["controlling"].remove(ball1)
                except ValueError:
                    ...
                ball1.highLighted = True
                ball1.follow(self)
                font = pygame.font.Font("static/HarmonyOS_Sans_SC_Medium.ttf", 20)
                followingTipsText = font.render(f"视角跟随中", True, "blue")
                followingTipsTextRect =  followingTipsText.get_rect()
                followingTipsTextRect.x = self.screen.get_width()/2
                followingTipsTextRect.y = 20
                self.screen.blit(followingTipsText, followingTipsTextRect)

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
                wall.check_vertex_collision(ball)
        for wall in self.elements["wall"]:
            for line in wall.lines:
                for ball in self.elements["ball"]:
                    if ball.isCollidedByLine(line) and not wall.isPosOn(self, ball.position):
                        ball.reboundByLine(line)

        if not self.isCelestialBodyMode:
            self.floor.position.x = self.screenToReal(self.screen.get_width()/2,self.x)
            self.floor.update(dt)
            self.floor.draw(self)
        

        if self.isMoving and not self.isElementCreating:
            for element1 in self.elements["controlling"]:
                pos = pygame.mouse.get_pos()
                element1.highLighted = True
                try:
                    element1.velocity = Vector2(0,0)
                except Exception as e:
                    ...
                allowToPlace = True
                for element2 in self.elements["all"]:
                    if element2.isMouseOn(self) and element2!= element1:
                        allowToPlace = False
                        break
                if allowToPlace:
                    element1.position.x = self.screenToReal(pos[0],self.x)
                    element1.position.y = self.screenToReal(pos[1],self.y)
                element1.update(dt)
        self.update_fps()

    def update_fps(self):
        self.lastTime = self.currentTime
        self.currentTime = time.time()
        self.fpsSaver.append(self.currentTime - self.lastTime)
        self.fpsAverage = len(self.fpsSaver) / sum(self.fpsSaver)
        self.fpsMinimum = 1 / max(self.fpsSaver)
        if sum(self.fpsSaver) >= 1:
            del self.fpsSaver[0]

    # 主更新循环
    def update(self):
        self.event_loop()
        self.update_screen()
        self.update_elements()
        self.update_menu()

    def findNearestHeavyBall(self, ball : Ball) -> Ball | None:
        result = None
        minDis = float('inf')
        for ball2 in self.elements["ball"]:
            if ball2.mass > ball.mass and ball.position.distance(ball2.position) < minDis:
                result = ball2
                minDis = ball.position.distance(ball2.position)
        return result
    
    def CelestialBodyMode(self):
        if not self.isCelestialBodyMode and not self.isModeChangingNaturally:
            self.y = 200000
        if self.y - self.screenToReal(self.screen.get_height())/2 < 150000:
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

    def GroundSurfaceMode(self):
        if self.isCelestialBodyMode and not self.isModeChangingNaturally:
            self.y = self.screen.get_height()/self.ratio
        if self.y - self.screenToReal(self.screen.get_height())/2 >= 150000:
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

# 游戏菜单界面类
class Menu:
    def __init__(self, size : Vector2):
        self.width = size.x*3/100
        self.height = size.y*80/100

        self.x=size.x-self.width
        self.y=(size.y-self.height)/2
        
        with open("config/elementOptions.json", "r", encoding="utf-8") as f:
            self.optionsList = json.load(f)
            
        self.options = []
        for i in range(len(self.optionsList)):
            option = Option(Vector2(self.x+self.width*1/10, self.y+self.width*1/10+i*self.width*9/10), Vector2(self.width*8/10, self.width*8/10), self.optionsList[i]["type"], self)
            self.options.append(option)

    # 判断鼠标是否在菜单区域
    def isMouseOn(self):    
        pos = Vector2(pygame.mouse.get_pos())
        return self.isPosOn(pos)

    def isPosOn(self, pos:Vector2):
        return pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.height  

    # 绘制菜单界面
    def draw(self, game : Game):
        pygame.draw.rect(game.screen, (220, 220, 220), (self.x, self.y, self.width, self.height),border_radius=int(self.width*15/100))
        for option in self.options:
            option.draw(game)
 

# 菜单选项类
class Option:
    def __init__(self, pos : Vector2, size : Vector2, type: str, menu : Menu):
        self.x = pos.x
        self.y = pos.y
        self.width = size.x
        self.height = size.y
        self.type = type
        self.pos = pos
        self.creationPoints = []
        self.isAbsorption = False
        self.attrs = {}
        self.highLighted = False
        
    
        for option in menu.optionsList:
            if option["type"] == self.type:
                self.name = option["name"]
                self.attrs_ = option["attrs"]
                for attr in self.attrs_:
                    self.attrs[attr["type"]] = attr["value"]

    def drawArrow(self, game, start_pos, end_pos, color):
        pygame.draw.line(game.screen, color, start_pos, end_pos, 3)

        # 计算箭头的方向
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        angle = math.atan2(dy, dx)
        
        # 箭头的大小
        arrow_length = 15
        arrow_angle = math.pi / 6  # 30度

        # 计算箭头的两个端点
        arrow_point1 = (
            end_pos[0] - arrow_length * math.cos(angle - arrow_angle),
            end_pos[1] - arrow_length * math.sin(angle - arrow_angle)
        )
        arrow_point2 = (
            end_pos[0] - arrow_length * math.cos(angle + arrow_angle),
            end_pos[1] - arrow_length * math.sin(angle + arrow_angle)
        )

        # 绘制箭头
        pygame.draw.polygon(game.screen, color, [end_pos, arrow_point1, arrow_point2])

    # 判断鼠标是否在选项区域
    def isMouseOn(self):
        pos = pygame.mouse.get_pos()
        return self.isPosOn(Vector2(pos))

    def isPosOn(self, pos : Vector2):
        return pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.height  
    

    # 创建球体元素
    def ballCreate(self, game : Game):
        game.isScreenMoving = False
        game.isMoving = False
        game.isElementCreating = True
        game.isDragging = False
        radius = float(self.attrs["radius"])
        color = self.attrs["color"]
        mass = float(self.attrs["mass"])
        self.highLighted = True
        coordinator = Coordinator(0, 0, 200, game)
        self.additionVelocity = Vector2(0, 0)
        while game.isElementCreating:
            game.isElementCreating = True
            pos = pygame.mouse.get_pos()
            game.update()
                
            if not game.isDragging:
                
                ball = Ball(Vector2(game.screenToReal(pos[0], game.x), game.screenToReal(pos[1], game.y)), radius, color, mass, Vector2(0, 0), [Vector2(0, 0)], True)
                self.creationPoints = [ball.position, ball.position]
                ball.draw(game)
                radiusText = game.font.render(f"半径 = {radius}", True, colorSuitable(ball.color, game.background))
                radiusTextRect =  radiusText.get_rect()
                radiusTextRect.x = pos[0]
                radiusTextRect.y = pos[1]
                game.screen.blit(radiusText, radiusTextRect)

                massText = game.font.render(f"质量 = {mass: .1f}", True, colorSuitable(ball.color, game.background))
                massTextRect =  massText.get_rect()
                massTextRect.x = pos[0]
                massTextRect.y = pos[1] + radiusText.get_height()
                game.screen.blit(massText, massTextRect)

            if game.isDragging:
                start_pos = (game.realToScreen(ball.position.x, game.x), game.realToScreen(ball.position.y, game.y))
                end_pos = (game.realToScreen(self.creationPoints[1].x, game.x), game.realToScreen(self.creationPoints[1].y, game.y))
    
                self.creationPoints[1] = Vector2(game.screenToReal(pos[0], game.x), game.screenToReal(pos[1], game.y))
                
                if coordinator.isMouseOn():
                    self.drawArrow(game, start_pos, end_pos, "yellow")
                else:
                    self.drawArrow(game, start_pos, end_pos, "red")
                ball.draw(game)
                coordinator.position = ball.position
                self.additionVelocity = (self.creationPoints[1] - self.creationPoints[0]) * 2
                coordinator.update(game)
                coordinator.draw(game, self)

            pygame.display.update()
            for event in pygame.event.get():

                game.isPressed = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    allowToPlace = True
                    game.isDragging = True
                    for element in game.elements["all"]:
                        if element.isMouseOn(game):
                            allowToPlace = False
                            break
                    if not game.menu.isMouseOn() and allowToPlace:
                        ball = Ball(Vector2(game.screenToReal(pos[0], game.x), game.screenToReal(pos[1], game.y)), radius, color, mass, Vector2(0, 0), [Vector2(0, 0)])

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.isMouseOn():
                        self.highLighted = False
                        game.isElementCreating = False
                        break

                    elif not game.menu.isMouseOn() or game.isDragging:
                        game.isDragging = False
                        ball = Ball(ball.position, radius, color, mass, Vector2(game.screenToReal(pos[0], game.x) - ball.position.x, game.screenToReal(pos[1], game.y) - ball.position.y) * 2, [], gravitation=game.isCelestialBodyMode)
                        if game.findNearestHeavyBall(ball) is not None and game.isCelestialBodyMode:
                            ball.getCircularVelocity(game.findNearestHeavyBall(ball))
                        game.elements["all"].append(ball)
                        game.elements["ball"].append(ball)

                    for option in game.menu.options:
                        if option.isMouseOn():
                            game.isElementCreating = False
                            self.highLighted = False
                            option.createElement(game, Vector2(pos[0], pos[1]))
                            break

                if event.type == pygame.MOUSEWHEEL and not game.isDragging:
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
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        game.isMassSetting = False

                if event.type == pygame.QUIT:
                    game.exit()
                elif event.type == pygame.ACTIVEEVENT:
                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)
                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z and game.isCtrlPressing:
                        lastElement = game.elements["all"][-1]
                        game.elements["all"].remove(lastElement)
                        for option in game.menu.options:
                            if option.type == lastElement.type:
                                game.elements[option.type].remove(lastElement)
                                break
                    if event.key == pygame.K_g:
                        game.saveGame()
                    if event.key == pygame.K_l:
                        game.loadGame()
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.loadGame(f"default/{str(event.key - pygame.K_0)}.pkl")
                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        game.isMassSetting = True
                    if event.key == pygame.K_SPACE:
                        game.isPaused = not game.isPaused
                    if event.key == pygame.K_r:
                        game.elements["all"] = []
                        for option in game.menu.options:
                            game.elements[option.type] = []
                    if event.key == pygame.K_ESCAPE:
                        game.isElementCreating = False
                        self.highLighted = False
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

    # 创建墙体元素
    def wallCreate(self, game : Game):
        game.isElementCreating = True
        self.highLighted = True
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
                coordinator.w = 200
                coordinator.update(game)
                coordinator.draw(game, self)
                if coordinator.isMouseOn():
                    pygame.draw.line(game.screen, "yellow", (game.realToScreen(self.creationPoints[0].x, game.x), game.realToScreen(self.creationPoints[0].y, game.y)), (game.realToScreen(self.creationPoints[1].x, game.x), game.realToScreen(self.creationPoints[1].y, game.y)))
                else:
                    pygame.draw.line(game.screen, self.attrs["color"], (game.realToScreen(self.creationPoints[0].x, game.x), game.realToScreen(self.creationPoints[0].y, game.y)), pygame.mouse.get_pos())      
                pygame.display.update()
            if clickNum%4 == 0:
                coordinator.position = Vector2(game.screenToReal(pygame.mouse.get_pos()[0], game.x), game.screenToReal(pygame.mouse.get_pos()[1], game.y))  
                coordinator.w = 10
                coordinator.update(game)
                coordinator.draw(game, self)
                pygame.display.update()


            for event in pygame.event.get():
                
                game.isPressed = False
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        if not game.menu.isMouseOn():
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
                            game.isElementCreating = False
                            break
                        for option in game.menu.options:
                            if option.isMouseOn():
                                game.isElementCreating = False
                                self.highLighted = False
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
                    if event.key == pygame.K_z and game.isCtrlPressing:
                        lastElement = game.elements["all"][-1]
                        game.elements["all"].remove(lastElement)
                        for option in game.menu.options:
                            if option.type == lastElement.type:
                                game.elements[option.type].remove(lastElement)
                                break
                    if event.key == pygame.K_g:
                        game.saveGame()
                    if event.key == pygame.K_l:
                        game.loadGame()
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.loadGame(f"default/{str(event.key - pygame.K_0)}.pkl")
                    if event.key == pygame.K_SPACE:
                        game.isPaused = not game.isPaused
                    if event.key == pygame.K_r:
                        game.elements["all"] = []
                        for option in game.menu.options:
                            game.elements[option.type] = []
                    if event.key == pygame.K_ESCAPE:
                        game.isElementCreating = False
                        self.highLighted = False
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

    # 编辑元素属性
    def elementEdit(self, game : Game, attrs : list):
        inputMenu = InputMenu(Vector2(game.screen.get_width()/2, game.screen.get_height()/2), game, self)
        
        inputMenu.options = self.attrs_
        game.openEditor(inputMenu)

    def setAttr(self, name, value):
        for atr in self.attrs_:     
           if atr["type"] == name:
                atr["value"] = value
        self.attrs[name] = value

    # 绘制选项界面
    def draw(self, game : Game):
        if self.highLighted:
            pygame.draw.rect(game.screen, "yellow", (self.x-3, self.y-3, self.width+6, self.height+6),border_radius=int(self.width*15/100))
        pygame.draw.rect(game.screen, (255, 255, 255), (self.x, self.y, self.width, self.height),border_radius=int(self.width*15/100))
        if self.type == "ball":
            pygame.draw.circle(game.screen, self.attrs["color"], (self.x+self.width/2, self.y+self.height/2), self.width/3)
        if self.type == "wall":
            pygame.draw.rect(game.screen, self.attrs["color"], (self.x+self.width/10, self.y+self.height/10, self.width*8/10, self.height*8/10))


    # 创建元素对象
    def createElement(self, game: Game, pos: Vector2):
        x = pos.x
        y = pos.y
        if x > self.x and x < self.x + self.width and y > self.y and y < self.y + self.height:
            method = eval(f"self.{self.type}Create")
            method(game)

    # 编辑元素属性
    def edit(self, game : Game, pos: Vector2):
        x = pos.x
        y = pos.y
        if x > self.x and x < self.x + self.width and y > self.y and y < self.y + self.height:
            self.elementEdit(game, list(self.attrs.keys()))

class SettingsButton:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        # 加载图片并转换为透明格式
        original_icon = pygame.image.load("static/settings.png").convert_alpha()
        # 调整图片大小
        self.icon = pygame.transform.scale(original_icon, (self.width, self.height))


    def draw(self, game: Game):
        game.screen.blit(self.icon, (self.x, self.y))

    def isMouseOn(self):
        return self.isPosOn(Vector2(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]))

    def isPosOn(self, pos: Vector2):
        return pos.x > self.x and pos.x < self.x + self.width and pos.y > self.y and pos.y < self.y + self.height
            

# 输入框控件类
class InputBox:
    def __init__(self, x, y, width, height, option, target, text=''):
        self.rect = pygame.Rect(x, y, width-100, height)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = text
        self.font = pygame.font.Font(None, int(height))
        self.txt_surface = self.font.render(self.text, True, self.color)
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.option = option
        self.target = target
        self.active = False
        self.isColorError = False
        self.cursor_pos = len(text)  # 新增光标位置
        self.backspace_pressed = False  # 新增退格长按状态
        self.backspace_last_time = 0    # 新增退格计时器
        if self.option["type"] != "color":
            self.min = float(self.option["min"])
            self.max = float(self.option["max"])

    # 处理输入事件
    def handle_event(self, event, game : Game):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
            
        if event.type == pygame.KEYDOWN:
            if self.active:
                # 处理方向键移动光标
                if event.key == pygame.K_LEFT:
                    if self.cursor_pos > 0:
                        self.cursor_pos -= 1
                elif event.key == pygame.K_RIGHT:
                    if self.cursor_pos < len(self.text):
                        self.cursor_pos += 1
                
                elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    if not self.isColorError:
                        game.isEditing = False
                    else:
                        messagebox.showerror("错误", "您输入的颜色不合法!!!\n请输入合法的颜色编号或名称!")
                        game.isEditing = True
                else:
                    if self.option["type"] != "color":
                        if event.key == pygame.K_BACKSPACE:
                            self._handle_backspace()
                            self.backspace_pressed = True
                            self.backspace_last_time = pygame.time.get_ticks()
                        elif event.unicode.isdigit() or event.unicode == "." or event.unicode == "-":
                            original_text = self.text
                            original_pos = self.cursor_pos
                            self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                            self.cursor_pos += 1
                            try:
                                num = float(self.text)
                                if num < self.min:
                                    self.text = str(self.min)
                                    self.cursor_pos = len(self.text)
                                elif num > self.max:
                                    self.text = str(self.max)
                                    self.cursor_pos = len(self.text)
                            except ValueError:
                                self.text = original_text
                                self.cursor_pos = original_pos
                            self.attrUpdate(self.target)
                    else:
                        if event.key == pygame.K_BACKSPACE:
                            self._handle_backspace()
                            self.backspace_pressed = True
                            self.backspace_last_time = pygame.time.get_ticks()
                        elif event.unicode.isalnum() or event.unicode == "#":
                            self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                            self.cursor_pos += 1
                            self.isColorError = False
                            try:
                                pygame.Color(self.text)
                                self.attrUpdate(self.target)
                            except ValueError:
                                self.isColorError = True
                                
                game.lastTime = game.currentTime
                game.currentTime = time.time()
                self.txt_surface = self.font.render(self.text, True, self.color)
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_BACKSPACE:
                self.backspace_pressed = False

    # 新增退格处理函数
    def _handle_backspace(self):
        if self.cursor_pos > 0:
            self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
            self.cursor_pos -= 1
            self.attrUpdate(self.target)

    # 更新输入框状态
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
            
        # 处理长按退格
        if self.backspace_pressed:
            current_time = pygame.time.get_ticks()
            if current_time - self.backspace_last_time > 500:  # 500ms后开始连续删除
                self._handle_backspace()
                self.backspace_last_time = current_time - 450  # 控制删除频率

    # 绘制输入框
    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

        if self.active and self.cursor_visible:
            # 根据光标位置计算渲染位置
            text_before_cursor = self.text[:self.cursor_pos]
            cursor_x = self.font.render(text_before_cursor, True, self.color).get_width() + self.rect.x + 5
            pygame.draw.line(screen, self.color, (cursor_x, self.rect.y + 5), (cursor_x, self.rect.y + 27), 2)

    # 保留原有方法
    def attrUpdate(self, target):
        target.setAttr(self.option["type"], self.text)

# 输入菜单界面类
class InputMenu(Element):
    def __init__(self, position: Vector2, game: Game, target):
        # 每个输入框的垂直间距
        self.vertical_spacing = 100
        self.position = position
        self.width = game.screen.get_width()/3
        self.height = 0
        self.x = position.x - self.width/2 
        self.y = position.y - self.height/2
        self.commitFunction = ""
        self.font = pygame.font.Font("static/HarmonyOS_Sans_SC_Medium.ttf", int(self.vertical_spacing/6))
        self.options = []
        self.input_boxes = []
        self.target = target
        
        
    # 更新输入菜单布局
    def update(self, game: Game):
        l = len(self.options)
        self.height = 0
        self.input_boxes = []
        for i in range(l):
            option = self.options[i]
            # 计算每个输入框的y坐标
            y = self.y + 10 + i * self.vertical_spacing 
            input_box = InputBox(self.x + self.width*3/10, y, self.width - self.width*3/10, self.vertical_spacing/3, option, self.target , str(option["value"]))
            self.height += self.vertical_spacing  # 更新InputMenu的高度
            self.input_boxes.append(input_box)
        self.x = self.position.x - self.width/2
        self.y = self.position.y - self.height/2
        game.lastTime = game.currentTime
        game.currentTime = time.time()
        

    def updateBoxes(self, event, game):
        for box in self.input_boxes:
            box.handle_event(event, game)

    def draw(self, game: Game):
        pygame.draw.rect(game.screen, (255, 255, 255), (self.x, self.y, self.width, self.height), border_radius=int(self.width*2/100))
        
        # 绘制所有输入框和选项文本

        l = len(self.options)
        for i in range(l):
            v = self.options[i]["type"]
            input_box = self.input_boxes[i]
            
            # 绘制选项文本
            option_text = self.font.render(game.translation[v], True, (0, 0, 0))
            game.screen.blit(option_text, (self.x , input_box.rect.y))
            
            # 绘制输入框
            input_box.draw(game.screen)
        
class ControlOption:
    def __init__(self, name, x, y, width, height, color):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def attrEditor(self, game: Game, target):
        inputMenu = InputMenu(Vector2(game.screen.get_width()/2, game.screen.get_height()/2), game, target)
        for option in game.menu.optionsList:
            if option["type"] == target.type:
                inputMenu.options = target.attrs
                inputMenu.target = target
        game.openEditor(inputMenu)

    def copy(self, game: Game, target):
        target.copy(game)

    def delete(self, game: Game, target: Element):
        for type in game.elements.keys():
            if target in game.elements[type]:
                game.elements[type].remove(target)

    def follow(self, game: Game, target: Element):
        target.isFollowing = not target.isFollowing

    def addVelocity(self, game: Game, target: Element):
        option = Option(Vector2(0, 0), Vector2(0,0), "test", game.menu)
        isAdding = True
        target.highLighted = True
        game.update()

        coordinator = Coordinator(0, 0, 200, game)
        coordinator.position = target.position
        coordinator.update(game)
        option.creationPoints = [target.position, target.position]
        self.addVelocity = (option.creationPoints[1] - option.creationPoints[0])
        while isAdding:
            target.position = option.creationPoints[0]
            start_pos = (game.realToScreen(target.position.x, game.x), game.realToScreen(target.position.y, game.y))
            end_pos = (game.realToScreen(option.creationPoints[1].x, game.x), game.realToScreen(option.creationPoints[1].y, game.y))


            game.update()
            pos = pygame.mouse.get_pos()
            option.creationPoints[1] = Vector2(game.screenToReal(pos[0], game.x), game.screenToReal(pos[1], game.y))
            
            
            if coordinator.isMouseOn():
                option.drawArrow(game, start_pos, end_pos, "yellow")
            else:
                option.drawArrow(game, start_pos, end_pos, "red")
            
            coordinator.update(game)
            coordinator.draw(game, option, str(round(abs(self.addVelocity)))+"px/s")
            self.addVelocity = (option.creationPoints[1] - option.creationPoints[0])
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.exit()
                elif event.type == pygame.ACTIVEEVENT:
                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)
                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    target.velocity += option.creationPoints[1] - option.creationPoints[0]
                    isAdding = False
                    target.highLighted = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        game.saveGame()
                    if event.key == pygame.K_l:
                        game.loadGame()
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.loadGame(f"default/{str(event.key - pygame.K_0)}.pkl")
                    if event.key == pygame.K_ESCAPE:
                        isAdding = False
                        target.highLighted = False

            
            game.lastTime = game.currentTime
            game.currentTime = time.time()
            pygame.display.update()

    def clearVelocity(self, game: Game, target: Element):
        target.velocity = Vector2(0, 0)

    def addForce(self, game: Game, target: Element):
        option = Option(Vector2(0, 0), Vector2(0,0), "test", game.menu)
        isAdding = True
        target.highLighted = True
        game.update()

        coordinator = Coordinator(0, 0, 200, game)
        coordinator.position = target.position
        coordinator.update(game)
        option.creationPoints = [target.position, target.position]
        self.additionForce = (option.creationPoints[1] - option.creationPoints[0])

        while isAdding:
            target.position = option.creationPoints[0]
            start_pos = (game.realToScreen(target.position.x, game.x), game.realToScreen(target.position.y, game.y))
            end_pos = (game.realToScreen(option.creationPoints[1].x, game.x), game.realToScreen(option.creationPoints[1].y, game.y))

            game.update()
            pos = pygame.mouse.get_pos()
            option.creationPoints[1] = Vector2(game.screenToReal(pos[0], game.x), game.screenToReal(pos[1], game.y))
            
            if coordinator.isMouseOn():
                option.drawArrow(game, start_pos, end_pos, "yellow")
            else:
                option.drawArrow(game, start_pos, end_pos, "red")
            
            
            coordinator.update(game)
            coordinator.draw(game, option, str(round(abs(self.additionForce))/10)+"N")
            self.additionForce = (option.creationPoints[1] - option.creationPoints[0])
                                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.exit()
                elif event.type == pygame.ACTIVEEVENT:
                    if event.gain == 0 and event.state == 2:
                        setCapsLock(False)
                    elif event.gain == 1 and event.state == 1:
                        setCapsLock(True)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    
                    target.force(self.additionForce)
                    isAdding = False
                    target.highLighted = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        game.saveGame()
                    if event.key == pygame.K_l:
                        game.loadGame()
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.loadGame(f"default/{str(event.key - pygame.K_0)}.pkl")
                    if event.key == pygame.K_ESCAPE:
                        isAdding = False
                        target.highLighted = False

            game.lastTime = game.currentTime
            game.currentTime = time.time()
            pygame.display.update()

    def clearForce(self, game: Game, target: Element):
        target.artificialForces = []

    def isMouseOn(self):
        return self.isPosOn(Vector2(pygame.mouse.get_pos()))

    def isPosOn(self, pos: Vector2):
        return self.x < pos.x < self.x + self.width and self.y < pos.y < self.y + self.height

    def draw(self, game: Game):
        pygame.draw.rect(game.screen, self.color, (self.x, self.y, self.width, self.height), border_radius=int(self.width*2/100))
        text = game.translation[self.name]
        text_surface = game.font.render(text, True, (0, 0, 0))
        game.screen.blit(text_surface, (self.x + self.width/2 - text_surface.get_width()/2, self.y + self.height/2 - text_surface.get_height()/2))

class ElementController:
    def __init__(self, element: Element, position: Vector2):
        self.x = position.x
        self.y = position.y
        self.optionWidth = 300
        self.optionHeight = 50
        self.element = element
        self.controlOptionsList = []
        self.controlOptions = []

    def control(self, game: Game):
        for option in self.controlOptions:
            if option.isMouseOn():
                method = eval(f"option.{option.name}")
                method(game, self.element)
                game.isElementControlling = False
                self.element.highLighted = False
                break

    def isMouseOn(self):
        return self.isPosOn(Vector2(pygame.mouse.get_pos()))
    
    def isPosOn(self, pos: Vector2):
        return self.x < pos.x < self.x + self.optionWidth and self.y < pos.y < self.y + self.optionHeight * len(self.controlOptionsList)
    
    def update(self, game: Game):
        options = game.menu.optionsList
        
        for option in options:
            if option["type"] == self.element.type:
                self.controlOptionsList = option["controlOptions"]
             
        screenHeight = game.screen.get_height()
        if self.y + len(self.controlOptionsList)*self.optionHeight > screenHeight:
                self.y -= len(self.controlOptionsList)*self.optionHeight + 50   
                
        current_y = self.y  # 初始 y 坐标
        for option in self.controlOptionsList:
            controlOption = ControlOption(
                    option["type"],
                    self.x + 30,  # x 坐标保持不变
                    current_y,  # 使用当前 y 坐标
                    self.optionWidth,
                    self.optionHeight,
                    "white"  # 颜色默认白色
                )
            self.controlOptions.append(controlOption)
                
            current_y += self.optionHeight + 5  # 更新 y 坐标，增加当前 ControlOption 的高度和间距
            

    def draw(self, game: Game):
        for option in self.controlOptions:
            option.draw(game)
            
