from basic import *
from game import *
from ai import *
import pygame
import threading
import re

def ballsToString(balls : list[Element]) -> str:
    """balls列表转字符串"""
    text = ""
    for i in range(len(balls)):
        text += f"ballIndex={i} position={balls[i].position.toTuple()} radius={balls[i].radius} color={balls[i].color} mass={balls[i].mass} velocity={balls[i].velocity.toTuple()} acceleration={balls[i].acceleration.toTuple()} gravity={balls[i].gravity} collisionFactor={balls[i].collisionFactor} gravitation={balls[i].gravitation} \n"
    return text

def wallsToString(walls : list[Element]) -> str:
    """walls列表转字符串"""
    text = ""   
    for i in range(len(walls)):
        text += f"wallIndex={i} position={walls[i].position.toTuple()} x1={walls[i].vertexes[0].x} y1={walls[i].vertexes[0].y} x2={walls[i].vertexes[1].x} y2={walls[i].vertexes[1].y} x3={walls[i].vertexes[2].x} y3={walls[i].vertexes[2].y} x4={walls[i].vertexes[3].x} y4={walls[i].vertexes[3].y} color={walls[i].color} \n"
    return text

def command(text : str, game) -> bool:
    """执行命令"""
    commands = text.split()

    if len(commands) == 0:
        return
        
    elif commands[0] == "save":
        """save [filename]"""
        game.saveGame(commands[1])

    elif commands[0] == "load":
        """load [filename]"""
        game.loadGame(commands[1])

    elif commands[0] == "create":

        if commands[1] == "ball":
            """create ball [x] [y] [radius] [color] [mass] [vx] [vy] [fx] [fy] [gravity] [collisionFactor] [gravitation]"""
            ball = Ball(Vector2(float(commands[2]), float(commands[3])), float(commands[4]), commands[5], float(commands[6]), Vector2(float(commands[7]), float(commands[8])), [Vector2(float(commands[9]), float(commands[10]))], float(commands[11]), float(commands[12]), bool(commands[13]))
            game.elements["all"].append(ball)
            game.elements["ball"].append(ball)

        elif commands[1] == "wall":
            """create wall [x1] [y1] [x2] [y2] [x3] [y3] [x4] [y4] [color]"""
            wall = Wall([Vector2(float(commands[2]), float(commands[3])), Vector2(float(commands[4]), float(commands[5])), Vector2(float(commands[6]), float(commands[7])), Vector2(float(commands[8]), float(commands[9]))], commands[10])
            game.elements["all"].append(wall)
            game.elements["wall"].append(wall)
        
        else:
                return False

    elif commands[0] == "set":
        
        if commands[1] == "ball":

            if commands[3] in ["radius", "mass"]:
                """set ball [ballIndex] [attr] [value]"""
                game.elements["ball"][int(commands[2])].setAttr(commands[3], float(commands[4]))

            else:

                if commands[3] == "color":
                    """set ball [ballIndex] color [value]"""
                    game.elements["ball"][int(commands[2])].color = commands[4]
                    
                elif commands[3] == "position":
                    """set ball [ballIndex] position [x] [y]"""
                    game.elements["ball"][int(commands[2])].position = Vector2(float(commands[4]), float(commands[5]))

                elif commands[3] == "velocity":
                    """set ball [ballIndex] velocity [vx] [vy]"""
                    game.elements["ball"][int(commands[2])].velocity = Vector2(float(commands[4]), float(commands[5]))

                elif commands[3] == "force":
                    """set ball [ballIndex] force [fx] [fy]"""
                    game.elements["ball"][int(commands[2])].artificialForces = [Vector2(float(commands[4]), float(commands[5]))]
                    
                elif commands[3] == "gravity":
                    """set ball [ballIndex] gravity [value]"""
                    game.elements["ball"][int(commands[2])].gravity = float(commands[4])

                elif commands[3] == "collisionFactor":
                    """set ball [ballIndex] collisionFactor [value]"""
                    game.elements["ball"][int(commands[2])].collisionFactor = float(commands[4])

                elif commands[3] == "gravitation":
                    """set ball [ballIndex] gravitation [value]"""
                    game.elements["ball"][int(commands[2])].gravitation = bool(commands[4])

                else:
                    return False

        elif commands[1] == "wall":
            
            if commands[3] == "color":
                """set wall [wallIndex] color [value]"""
                game.elements["wall"][int(commands[2])].color = commands[4]

            elif commands[3] == "position":
                """set wall [wallIndex] position [x] [y]"""
                game.elements["wall"][int(commands[2])].position = Vector2(float(commands[4]), float(commands[5]))
            
            else:
                return False
            
        elif commands[1] == "environment":

            if commands[2] == "gravity":
                """set environment gravity [value]"""
                for option in game.environmentOptions:
                    if option["type"] == "gravity":
                        option["value"] = commands[3]
            
            elif commands[2] == "airResistance":
                """set environment airResistance [value]"""
                for option in game.environmentOptions:
                    if option["type"] == "airResistance":
                        option["value"] = commands[3]

            elif commands[2] == "collisionFactor":
                """set environment collisionFactor [value]"""
                for option in game.environmentOptions:
                    if option["type"] == "collisionFactor":
                        option["value"] = commands[3]
            
            else:
                return False

    elif commands[0] == "clear":
        if commands[1] == "ball":
            """clear ball [ballIndex] [velocity | force]"""

            if commands[3] == "velocity":
                game.elements["ball"][int(commands[2])].velocity = ZERO

            elif commands[3] == "force":
                game.elements["ball"][int(commands[2])].artificialForces.clear()

            else:
                return False

    elif commands[0] == "add":
        if commands[1] == "ball":
            "add ball [ballIndex] [velocity | force] [x] [y]"

            if commands[3] == "velocity":
                game.elements["ball"][int(commands[2])].velocity += Vector2(float(commands[4]), float(commands[5]))

            elif commands[3] == "force":
                game.elements["ball"][int(commands[2])].artificialForces.append(Vector2(float(commands[4]), float(commands[5])))

            else:
                return False

    elif commands[0] == "delete" or commands[0] == "remove":

        if commands[1] == "ball":
            """delete ball [ballIndex]"""
            ball = game.elements["ball"][int(commands[2])]
            game.elements["all"].remove(ball)
            game.elements["ball"].remove(ball)

        elif commands[1] == "wall":
            """delete wall [wallIndex]"""
            wall = game.elements["wall"][int(commands[2])]
            game.elements["all"].remove(wall)
            game.elements["wall"].remove(wall)
            
        elif commands[1] == "element":
            """delete element [elementIndex]"""
            element = game.elements["all"][int(commands[2])]
            game.elements["all"].remove(element)

            if element.type == "ball":
                game.elements["ball"].remove(element)

            elif element.type == "wall":
                game.elements["wall"].remove(element)

            else:
                return False
        
        else:
            return False
    
    elif commands[0] == "mode":

        if commands[1] == "0":
            """mode 0"""
            game.GroundSurfaceMode()
        
        elif commands[1] == "1":
            """mode 1"""
            game.CelestialBodyMode()
        
        else:
            return False

    else:
        return False
    
    return True

def AIThreadMethod(game : Game) -> None:
    """AI线程方法"""
    ai = AI(game)
    while True:
        try:
            game.isChatting = False
            point1 = game.screenToReal(Vector2(0, 0), Vector2(game.x, game.y))
            point2 = game.screenToReal(Vector2(game.screen.get_width(), game.screen.get_height()), Vector2(game.x, game.y))
            
            message = input("用户：")
            game.isChatting = True
            text = ai.chat(message=message + "\n" + "屏幕对角坐标：" + str(point1.toTuple()) + " " + str(point2.toTuple()) + "\n" + ballsToString(game.elements["ball"]) + "\n" + wallsToString(game.elements["wall"]))
            
            try:
                text = text.split("$")[1]
            except IndexError:
                ...

            result = re.findall("<.*>", text)

            for i in result:
                try:
                    if not command(i[1:-1].replace("\n", ""), game):
                        print("执行命令出错：未知命令", end="\n\n")
                except Exception as e:
                    print(f"执行命令出错：{e}", end="\n\n")
        except EOFError:
            break

if __name__ == '__main__': 
    game = Game()
    
    # 创建并启动AI线程
    AIThread = threading.Thread(target=AIThreadMethod, args=(game,))
    AIThread.daemon = True  # 设置为守护线程，主线程退出时自动退出
    AIThread.start()
    
    while True: 
        try:
            game.update()
            pygame.display.update()
        except KeyboardInterrupt:
            if game.isChatting:
                game.isChatting = False
            else:
                game.exit()
