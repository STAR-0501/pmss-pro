from ..game import *
from .ai_thread_loop import *
import pygame
import threading

if __name__ == "__main__":
    game: Game = Game()

    # 创建并启动AI线程
    AIThread: threading.Thread = threading.Thread(
        target=AIThreadLoop, args=(game,))
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
