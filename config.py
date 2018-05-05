from PyQt5.QtCore import Qt

# GUI
WIDTH = 64
HEIGHT = 32
PIXEL_SIZE = 10
PIXEL_SIZE_DEBUG = 15

DEBUG_WINDOW_WIDTH = 400

KEYBOARD = {
    Qt.Key_1: 0x1,
    Qt.Key_2: 0x2,
    Qt.Key_3: 0x3,
    Qt.Key_Q: 0x4,
    Qt.Key_W: 0x5,
    Qt.Key_E: 0x6,
    Qt.Key_A: 0x7,
    Qt.Key_S: 0x8,
    Qt.Key_D: 0x9,
    Qt.Key_X: 0x0,
    Qt.Key_Z: 0xa,
    Qt.Key_C: 0xb,
    Qt.Key_4: 0xc,
    Qt.Key_R: 0xd,
    Qt.Key_F: 0xe,
    Qt.Key_V: 0xf,
}

# Registers' names
PC = "pc"
INDEX = "index"
SP = "sp"
SOUND = "sound"
DELAY = "delay"
TIMERS = "timers"
V = "v"
