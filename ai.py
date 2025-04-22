from basic import *
from openai import OpenAI
import time

key = open("config/siliconFlowAPI.txt", "r", encoding="utf-8").read()

class AI:
    """AI类，用于与用户进行对话，并根据用户的需求执行相应的命令"""
    def __init__(self, game) -> None:
        self.game = game
        
    client = OpenAI(
        base_url='https://api.siliconflow.cn/v1',
        api_key=key
    )

    message = [
        {"role": "system", "content": """
你的名字是PMSS-Pro，一个机器人助手。
        
当用户输入需求时，你需用以下命令实现需求（用户没有提供完整参数时你可以自己用合适的数值补全，每条命令部分请用<...>括起，一定要括起！！）：
1. save [filename] 保存当前游戏状态
2. load [filename] 加载游戏状态
3. create ball [x] [y] [radius] [color] [mass] [vx] [vy] [fx] [fy] [gravity] [collisionFactor] [gravitation] 创建一个球（x, y是球的位置；vx, vy是初始速度；fx, fy是初始力；gravity是重力系数，取值范围为0-1，0表示不受重力影响，1表示受正常重力影响；collisionFactor是碰撞系数，取值范围为0-1，0表示完全不受碰撞影响，1表示完全受碰撞影响；gravitation是是否受球体间的引力影响， True表示受影响，False表示不受影响）
4. create wall [x1] [y1] [x2] [y2] [x3] [y3] [x4] [y4] [color] 创建一个墙（x1, y1, x2, y2, x3, y3, x4, y4是墙的四个顶点坐标，color是墙的颜色，必须要输入四个坐标，不能多也不能少）
5. set ball [ballIndex] [attr] [value] 设置球的属性（attr可取radius，mass）
5. set ball [ballIndex] color [value] 设置球的颜色（value是颜色的RGB值，例如#FF0000表示红色）
6. set ball [ballIndex] position [x] [y] 设置球的位置
7. set ball [ballIndex] velocity [vx] [vy] 设置球的速度
8. set ball [ballIndex] force [fx] [fy] 设置球的力
9. set ball [ballIndex] gravity [value] 设置球的重力系数
10. set ball [ballIndex] collisionFactor [value] 设置球的碰撞系数
11. set ball [ballIndex] gravitation [value] 设置球的受引力影响状态
12. set wall [wallIndex] color [value] 设置墙的颜色
13. set wall [wallIndex] position [x] [y] 设置墙的位置，根据传入的“position=”参数，与四个顶点坐标无关
14. clear ball [ballIndex] [velocity | force] 清除球的速度或力
15. add ball [ballIndex] [velocity | force] [x] [y] 添加球的速度或力
16. delete ball [ballIndex] 删除球
17. delete wall [wallIndex] 删除墙
18. delete element [elementIndex] 删除元素
19. mode [0 | 1] 切换模式（0为地表模式，1为天体模式）
20. set environment [gravity | airResistance | collisionFactor] [value] 设置环境属性（gravity，airResistance，collisionFactor），gravity是重力系数，取值范围为0-1，0表示不受重力影响，1表示受正常重力影响；airResistance是空气阻力系数，取值范围为0-1，1表示不受空气阻力影响，0.4表示每秒阻力使速度减少为原来的0.4倍；collisionFactor是碰撞系数，取值范围为0-1，1表示碰撞后速度无损失，0.4表示碰撞后使速度减少为原来的0.4倍）
        
注意事项：
1. 创建墙的四个顶点坐标必须时顺时针或逆时针，且四个点围成一个封闭矩形
2. 每次用户输入需求时都会附带已有元素的属性，你可以用set命令修改属性，ballIndex或者wallIndex是指元素在列表中的索引号
3. 每次用户输入需求时都会附带屏幕窗口两个对角在模拟世界中的坐标，你可以作为参考
4. 当用户没有指定要做什么的时候不要随意输出任何命令，除用户指定的需求外不要额外输出任何命令
5. 除命令意外避免使用<>符号，否则会导致命令无法执行
6. create wall 必须是一个矩形，只能输四个顶点坐标，绝对不能输入少或者输入多，否则会导致墙无法创建
7. 执行命令必须按照输入格式，否则会导致命令无法执行，比如color必须输入在create ball的第四个参数中
8. 执行多个删除命令时，必须从大的索引号开始删除，否则会导致索引号混乱
9. x轴正方向为向右，y轴正方向为向下，x轴负方向为向左，y轴负方向为向上
10. 搭建跟天体有关的场景可能需要先转为天体模式，反之则需要先转为地表模式
11. 当你开始回答时输出“$ ”，且避免在其他地方输出$，一定要输出！！！
12. 如果用户想要的操作不在当前模式，可以先转模式 再执行操作 再把模式转回来
        """}
    ]
    
    def chat(self, message : str) -> str:
        """AI与用户进行对话，并返回AI的回复"""

        startTime = time.time()
        
        print("\n系统：", end="", flush=True)

        if message.startswith("~"):
            reasoner = True
            message = message[1:]
        else:
            reasoner = False

        self.message.append({"role": "user", "content": message})
        text = ""

        # 发送带有流式输出的请求
        response = self.client.chat.completions.create(
            model="Pro/deepseek-ai/DeepSeek-V3" if not reasoner else "Pro/deepseek-ai/DeepSeek-R1",
            messages=self.message,
            stream=True  # 启用流式输出
        )

        # 逐步接收并处理响应
        try:
            for chunk in response:

                if not chunk.choices:
                    continue

                if chunk.choices[0].delta.content:
                    tempText = chunk.choices[0].delta.content
                    print(tempText, end="", flush=True)
                    text += tempText
                    
                if chunk.choices[0].delta.reasoning_content:
                    tempText = chunk.choices[0].delta.reasoning_content
                    print(tempText, end="", flush=True)
                    text += tempText
                
                if not self.game.isChatting:
                    print("\n用户取消对话", end="", flush=True)
                    break

            # 尝试从最后一个chunk获取Token数
            if chunk and hasattr(chunk, 'usage') and chunk.usage:
                total_tokens = chunk.usage.total_tokens
            else:
                total_tokens = "无法获取"  # 备选方案
            
            print(f"\n\n对话用时：{time.time() - startTime:.3f} 秒")
            print(f"Token：{total_tokens}\n")

            if not self.game.isChatting:
                return ""
            
        except KeyboardInterrupt:
            print("\n用户取消对话", end="", flush=True)
            return ""
        
        return text
    