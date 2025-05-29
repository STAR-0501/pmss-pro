import ctypes

def setCapsLock(state: bool = True) -> None:
    """
    设置或取消CapsLock状态
    state=True: 开启大写
    state=False: 关闭大写
    """
    VK_CAPITAL = 0x14
    current = ctypes.windll.user32.GetKeyState(VK_CAPITAL)

    if (current & 0xFFFF) != int(state):
        ctypes.windll.user32.keybd_event(VK_CAPITAL, 0, 0x1, 0)  # 按下
        ctypes.windll.user32.keybd_event(VK_CAPITAL, 0, 0x3, 0)  # 释放
