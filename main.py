from basic import *
from game import *
from ai import *
import pygame
import threading
import re
import json

modelList = json.loads(
    open("config/modelList.json", "r", encoding="utf-8").read())


def ballsToString(balls: list[Element]) -> str:
    """balls列表转字符串"""
    text: str = ""
    for i, ball in enumerate(balls):
        text += (
            f"ballIndex={i} "
            f"position={ball.position.toTuple()} "
            f"radius={ball.radius} "
            f"color={ball.color} "
            f"mass={ball.mass} "
            f"velocity={ball.velocity.toTuple()} "
            f"acceleration={ball.acceleration.toTuple()} "
            f"gravity={ball.gravity} "
            f"collisionFactor={ball.collisionFactor} "
            f"gravitation={ball.gravitation}\n"
        )
    return text


def wallsToString(walls: list[Element]) -> str:
    """walls列表转字符串"""
    text: str = ""
    for i, wall in enumerate(walls):
        text += (
            f"wallIndex={i} "
            f"position={wall.position.toTuple()} "
            f"x1={wall.vertexes[0].x} y1={wall.vertexes[0].y} "
            f"x2={wall.vertexes[1].x} y2={wall.vertexes[1].y} "
            f"x3={wall.vertexes[2].x} y3={wall.vertexes[2].y} "
            f"x4={wall.vertexes[3].x} y4={wall.vertexes[3].y} "
            f"color={wall.color}\n"
        )
    return text


def command(text: str, game: Game) -> bool:
    """执行命令"""
    commands: list[str] = text.split()

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
            ball = Ball(
                Vector2(float(commands[2]), float(commands[3])),
                float(commands[4]),
                commands[5],
                float(commands[6]),
                Vector2(float(commands[7]), float(commands[8])),
                [Vector2(float(commands[9]), float(commands[10]))],
                float(commands[11]),
                float(commands[12]),
                bool(commands[13]),
            )
            game.elements["all"].append(ball)
            game.elements["ball"].append(ball)

        elif commands[1] == "wall":
            """create wall [x1] [y1] [x2] [y2] [x3] [y3] [x4] [y4] [color]"""
            wall = Wall(
                [
                    Vector2(float(commands[2]), float(commands[3])),
                    Vector2(float(commands[4]), float(commands[5])),
                    Vector2(float(commands[6]), float(commands[7])),
                    Vector2(float(commands[8]), float(commands[9])),
                ],
                commands[10],
            )
            game.elements["all"].append(wall)
            game.elements["wall"].append(wall)

        else:
            return False

    elif commands[0] == "set":

        if commands[1] == "ball":

            if commands[3] in ["radius", "mass"]:
                """set ball [ballIndex] [attr] [value]"""
                game.elements["ball"][int(commands[2])].setAttr(
                    commands[3], float(commands[4])
                )

            else:

                if commands[3] == "color":
                    """set ball [ballIndex] color [value]"""
                    game.elements["ball"][int(commands[2])].color = commands[4]

                elif commands[3] == "position":
                    """set ball [ballIndex] position [x] [y]"""
                    game.elements["ball"][int(commands[2])].position = Vector2(
                        float(commands[4]), float(commands[5])
                    )

                elif commands[3] == "velocity":
                    """set ball [ballIndex] velocity [vx] [vy]"""
                    game.elements["ball"][int(commands[2])].velocity = Vector2(
                        float(commands[4]), float(commands[5])
                    )

                elif commands[3] == "force":
                    """set ball [ballIndex] force [fx] [fy]"""
                    game.elements["ball"][int(commands[2])].artificialForces = [
                        Vector2(float(commands[4]), float(commands[5]))
                    ]

                elif commands[3] == "gravity":
                    """set ball [ballIndex] gravity [value]"""
                    game.elements["ball"][int(
                        commands[2])].gravity = float(commands[4])

                elif commands[3] == "collisionFactor":
                    """set ball [ballIndex] collisionFactor [value]"""
                    game.elements["ball"][int(commands[2])].collisionFactor = float(
                        commands[4]
                    )

                elif commands[3] == "gravitation":
                    """set ball [ballIndex] gravitation [value]"""
                    game.elements["ball"][int(commands[2])].gravitation = bool(
                        commands[4]
                    )

                else:
                    return False

        elif commands[1] == "wall":

            if commands[3] == "color":
                """set wall [wallIndex] color [value]"""
                game.elements["wall"][int(commands[2])].color = commands[4]

            elif commands[3] == "position":
                """set wall [wallIndex] position [x] [y]"""
                game.elements["wall"][int(commands[2])].position = Vector2(
                    float(commands[4]), float(commands[5])
                )

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
                game.elements["ball"][int(
                    commands[2])].artificialForces.clear()

            else:
                return False

    elif commands[0] == "add":
        if commands[1] == "ball":
            "add ball [ballIndex] [velocity | force] [x] [y]"

            if commands[3] == "velocity":
                game.elements["ball"][int(commands[2])].velocity += Vector2(
                    float(commands[4]), float(commands[5])
                )

            elif commands[3] == "force":
                game.elements["ball"][int(commands[2])].artificialForces.append(
                    Vector2(float(commands[4]), float(commands[5]))
                )

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
            for option in game.environmentOptions:

                if option["type"] == "mode":
                    option["value"] = "0"

                if option["type"] == "gravity":
                    option["value"] = "1"

            game.GroundSurfaceMode()

        elif commands[1] == "1":
            """mode 1"""
            for option in game.environmentOptions:

                if option["type"] == "mode":
                    option["value"] = "1"

                if option["type"] == "gravity":
                    option["value"] = "0"

            game.CelestialBodyMode()

        else:
            return False

    else:
        return False

    return True


def AIThreadMethod(game: Game) -> None:
    """AI线程方法"""
    ai: AI = AI(game)

    print(
        f"""
直接输入使用第一模型
在开头插入“~”使用第二模型

当前第一模型：{config["models"][0]}
当前第二模型：{config["models"][1]}

输入“.”切换第一模型
输入“..”切换第二模型
        """
    )

    while True:
        try:
            game.isChatting = False

            if not game.isCelestialBodyMode:
                groundPoint1 = game.screenToReal(
                    Vector2(0, 0), Vector2(game.x, game.y))

                groundPoint2 = game.screenToReal(
                    Vector2(game.screen.get_width(), game.screen.get_height()),
                    Vector2(game.x, game.y),
                )

                celestialPoint1 = game.screenToReal(
                    Vector2(0, 0), Vector2(game.lastX, game.lastY)
                )

                celestialPoint2 = game.screenToReal(
                    Vector2(game.screen.get_width(), game.screen.get_height()),
                    Vector2(game.lastX, game.lastY),
                )

            else:

                groundPoint1 = game.screenToReal(
                    Vector2(0, 0), Vector2(game.lastX, game.lastY)
                )

                groundPoint2 = game.screenToReal(
                    Vector2(game.screen.get_width(), game.screen.get_height()),
                    Vector2(game.lastX, game.lastY),
                )

                celestialPoint1 = game.screenToReal(
                    Vector2(0, 0), Vector2(game.x, game.y)
                )

                celestialPoint2 = game.screenToReal(
                    Vector2(game.screen.get_width(), game.screen.get_height()),
                    Vector2(game.x, game.y),
                )

            message: str = input("User：")

            if message == ".":
                print()

                for i in range(len(modelList)):
                    print(f"{i+1}. {modelList[i]}")

                while True:

                    user_input = input(
                        f"\n当前第一模型：{config['models'][0]}\n请选择模型以切换第一模型："
                    )

                    if not user_input.isdigit() or not 1 <= int(user_input) <= len(modelList):
                        print(f"输入有误，请输入1到{len(modelList)}之间的整数编号。")
                        continue

                    index -= 1
                    config["models"][0] = modelList[index]
                    print("已切换第一模型：" + config["models"][0] + "\n")

                    json.dump(config, open(
                        "config/siliconFlowConfig.json", "w"), indent=4)

                    break

            elif message == "..":
                print()

                for i in range(len(modelList)):
                    print(f"{i+1}. {modelList[i]}")

                while True:

                    user_input = input(
                        f"\n当前第二模型：{config['models'][1]}\n请选择模型以切换第二模型："
                    )

                    if not user_input.isdigit() or not 1 <= int(user_input) <= len(modelList):
                        print(f"输入有误，请输入1到{len(modelList)}之间的整数编号。")
                        continue

                    index -= 1
                    config["models"][1] = modelList[index]
                    print("已切换第二模型：" + config["models"][1] + "\n")

                    json.dump(config, open(
                        "config/siliconFlowConfig.json", "w"), indent=4)

                    break

            else:
                game.isChatting = True

                text: str = ai.chat(
                    message=message + "\n"
                    + "当前模式："
                    + ("天体模式" if game.isCelestialBodyMode else "地表模式") + "\n"
                    + "地表模式屏幕对角坐标及元素属性："
                    + str(groundPoint1.toTuple()) + " "
                    + str(groundPoint2.toTuple()) + "\n"
                    + ballsToString(game.groundElements["ball"]) + "\n"
                    + wallsToString(game.groundElements["wall"]) + "\n"
                    + "天体模式屏幕对角坐标及元素属性："
                    + str(celestialPoint1.toTuple()) + " "
                    + str(celestialPoint2.toTuple()) + "\n"
                    + ballsToString(game.celestialElements["ball"]) + "\n"
                    + wallsToString(game.celestialElements["wall"])
                )

                try:
                    text = text.split("$")[1]

                except IndexError:
                    ...

                result: list = re.findall("<.*>", text)

                for i in result:

                    try:
                        if not command(i[1:-1].replace("\n", ""), game):
                            print("执行命令出错：未知命令", end="\n\n")

                    except Exception as e:
                        print(f"执行命令出错：{e}", end="\n\n")

        except EOFError:
            break


if __name__ == "__main__":
    game: Game = Game()

    # 创建并启动AI线程
    AIThread: threading.Thread = threading.Thread(
        target=AIThreadMethod, args=(game,))
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
