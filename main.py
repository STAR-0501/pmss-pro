from basic import *
from game import *
import pygame, threading

def update_elements_thread(game : Game):
    while True:
        game.update_elements()
        
# if __name__ == '__main__':
#     game = Game()
    
#     # 创建并启动更新元素的线程
#     elements_thread = threading.Thread(target=update_elements_thread, args=(game,))
#     elements_thread.daemon = True  # 设置为守护线程，主线程退出时自动退出
#     elements_thread.start()
    
#     while True:
#         game.event_loop()
#         game.update_screen()
#         game.update_menu()
#         pygame.display.update()

if __name__ == '__main__':
    game = Game()
    
    while True:
        game.update()
        pygame.display.update()