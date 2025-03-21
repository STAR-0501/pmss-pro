import openai 
import json

class AI:
    def __init__(self, game):
        self.game = game
        self.key = "sk-c41d82fe4a0b4e97b5c1d8bacff3790e"
        self.baseUrl = "https://api.deepseek.com"
        self.modal = "deepseek-chat"
        # self.modal = "deepseek-reasoner"  # 使用R1模型
        self.client = openai.OpenAI(api_key=self.key, base_url=self.baseUrl)
        self.messages = []

        with open("game.py", "r", encoding="utf-8") as f:
            words = f.read()
            self.gameCode = {"role": "system", "content": words}
            self.messages.append(self.gameCode)

        with open("basic.py", "r", encoding="utf-8") as f:
            words = f.read()
            self.basicCode = {"role": "system", "content": words}
            self.messages.append(self.basicCode)
            
        with open("config/aiWords.json", "r", encoding="utf-8") as f:
            words = json.load(f)
            for k,v in words.items():
                self.messages.append({"role": "system", "content": v})

        print("AI初始化完成！")

    def generate_text(self, prompt):
        """进行简单文本生成，根据给定的提示生成文本。"""
        response = self.client.chat.completions.create(
            model=self.modal,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        return response.choices[0].message.content

    def chat(self, user_input):
        """进行多轮对话。将用户输入与历史对话一起发送。"""
        # 添加用户输入到历史对话
        self.messages.append({"role": "user", "content": user_input})

        # 发送整个对话历史给 DeepSeek，获取模型回应
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=self.messages,
            stream=True
        )

        # 初始化一个空字符串来存储模型的回应
        assistant_message = ""
        
        # 迭代流式响应，逐步获取数据
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                assistant_message += chunk.choices[0].delta.content

        # 将模型回应添加到历史对话
        self.messages.append({"role": "assistant", "content": assistant_message})

        return assistant_message

    def clear_memory(self):
        """清空历史对话记忆。"""
        self.messages = []

if __name__ == '__main__':
    game = "game"
    ai = AI(game)
    while True:
        user_input = input("我：")
        if user_input == "exit":
            break
        assistant_message = ai.chat(user_input)
        eval(assistant_message)
