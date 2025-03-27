from game import *
from basic import *
from openai import OpenAI

def command(text : str, game : Game):
    commands = text.split()
    if len(commands) == 0:
        return

client = OpenAI(
    base_url='https://api.siliconflow.cn/v1',
    api_key='sk-kceztlqyxifrxdqwfqwnmmlrbgpvjhrrtdqezhttlqmjnoxn'
)

# 发送带有流式输出的请求
response = client.chat.completions.create(
    model="Pro/deepseek-ai/DeepSeek-V3",
    messages=[
        {"role": "user", "content": "你好"}
    ],
    stream=True  # 启用流式输出
)

# 逐步接收并处理响应
for chunk in response:
    if not chunk.choices:
        continue
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end="", flush=True)