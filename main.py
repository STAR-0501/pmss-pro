from basic import *
from game import *
import pygame, threading

def updateElementsThread(game : Game):
    while True:
        game.updateElements()
        
# if __name__ == '__main__':
#     game = Game()
    
#     # 创建并启动更新元素的线程
#     elementsThread = threading.Thread(target=updateElementsThread, args=(game,))
#     elementsThread.daemon = True  # 设置为守护线程，主线程退出时自动退出
#     elementsThread.start()
    
#     while True:
#         game.eventLoop()
#         game.updateScreen()
#         game.updateMenu()
#         pygame.display.update()

if __name__ == '__main__':
    game = Game()
    
    while True:
        game.update()
        pygame.display.update()