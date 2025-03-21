from basic import *
from game import *
from ai import *
import pygame, threading

def executor(userInput, ai : AI):
    assistantMessage = ai.chat(userInput)
    print("AI: ", end="")
    assistantMessage = assistantMessage.replace("```python", "")
    assistantMessage = assistantMessage.replace("```", "")
    exec(assistantMessage)
    

def aiThread(game : Game):
    ai = AI(game)
    while True:
        userInput = input("我: ")
        newExecutor = threading.Thread(target=executor, args=(userInput, ai, ))
        newExecutor.daemon = True 
        newExecutor.start()
        newExecutor.join(timeout=60)
        if newExecutor.is_alive():
            print("AI: 操作超时")
        
if __name__ == '__main__':
    game = Game()
    
    # 创建并启动AI线程
    elementsThread = threading.Thread(target=aiThread, args=(game,))
    elementsThread.daemon = True  # 设置为守护线程，主线程退出时自动退出
    elementsThread.start()
    
    while True:
        game.update()
        pygame.display.update()
        