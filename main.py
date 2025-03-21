from basic import *
from game import *
from ai import *
import pygame, threading

def executor(userInput, starbot : Starbot):
    assistant_message = starbot.chat(userInput)
    print("Starbot：", end="")
    assistant_message = assistant_message.replace("```python", "")
    assistant_message = assistant_message.replace("```", "")
    exec(assistant_message)
    

def aiThread(game : Game):
    starbot = Starbot(game)
    while True:
        userInput = input("我：")
        newExecutor = threading.Thread(target=executor, args=(userInput, starbot, ))
        newExecutor.daemon = True 
        newExecutor.start()
        newExecutor.join(timeout=60)
        if newExecutor.is_alive():
            print("Starbot：操作超时")
        
if __name__ == '__main__':
    game = Game()
    
    # 创建并启动AI线程
    elements_thread = threading.Thread(target=aiThread, args=(game,))
    elements_thread.daemon = True  # 设置为守护线程，主线程退出时自动退出
    elements_thread.start()
    
    while True:
        game.update()
        pygame.display.update()