from ..basic import *
from ..game import *
from ..ai import *
from .command import *
import re
import json


def AIThreadLoop(game: Game) -> None:
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

                    index = int(user_input) - 1
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

                    index = int(user_input) - 1
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
