import os
import threading

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QUrl, QTimer, pyqtSlot
from PyQt5.QtGui import QPainter
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QMainWindow, QGridLayout

from chip8 import CHIP8
from gui.DebugWidget import DebugWidget

PIXEL_HEIGHT = 15
PIXEL_WIDTH = 15

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


class GameWindow(QMainWindow):
    DEBUG = False

    def __init__(self, rom, speed, delay, parent=None):
        super().__init__(parent)

        self.rom = rom
        self.setWindowTitle(rom)

        self.game = CHIP8()

        self.setFixedSize(64 * PIXEL_WIDTH + DEBUG_WINDOW_WIDTH,
                          32 * PIXEL_HEIGHT)

        url = QUrl.fromLocalFile(os.path.abspath("sound.wav"))
        content = QMediaContent(url)
        self.player = QMediaPlayer()
        self.player.setMedia(content)

        self.debug_widget = DebugWidget(self.game)

        _layout = QGridLayout()
        _layout.setSpacing(5)
        _layout.addWidget(ScreenFillerWidget(), 0, 0)
        _layout.addWidget(self.debug_widget, 0, 1)
        _window = QtWidgets.QWidget()
        _window.setLayout(_layout)
        self.setCentralWidget(_window)

        self.game.load_rom(self.rom)

        self.start_timer(delay, self.game.decrement_sound_timer)
        self.start_timer(delay, self.game.decrement_delay_timer)

        self.debug_widget.sig_execute.connect(self.execute_one_instruction)

        self.delay = delay
        self.speed = speed
        if not self.DEBUG:
            thread = threading.Thread(target=self.execute_instructions,
                                      args=(delay, speed))

            thread.start()

    def start_timer(self, interval, func):
        timer = QTimer(self)
        timer.setInterval(interval)
        timer.timeout.connect(func)
        timer.start()

    @pyqtSlot()
    def execute_one_instruction(self):
        for _ in range(self.delay):
            for _ in range(self.speed):
                continue

            self.game.emulate_cycle()

            self.debug_widget.update_registers()

            if self.game.draw_flag:
                self.update()
                self.game.draw_flag = False
            if self.game.timers['sound'] == 1:
                self.player.play()

    def execute_instructions(self, delay, speed):
        while self.game.running:
            for _ in range(delay):
                for _ in range(speed):
                    continue
                self.game.emulate_cycle()

                # pprint(self.game.get_reg_dump())

                if self.game.draw_flag:
                    self.update()
                    self.game.draw_flag = False
                if self.game.timers['sound'] == 1:
                    self.player.play()

    def closeEvent(self, event):
        self.game.running = False
        event.accept()

    def keyPressEvent(self, e):
        if e.key() in KEYBOARD.keys():
            self.game.keys[KEYBOARD[e.key()]] = True
        if e.key() == Qt.Key_P:
            self.game.is_paused = not self.game.is_paused
        if e.key() == Qt.Key_Escape:
            self.close()

    def keyReleaseEvent(self, e):
        if e.key() in KEYBOARD.keys():
            self.game.keys[KEYBOARD[e.key()]] = False

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        for y in range(32):
            for x in range(64):
                color = Qt.black if not self.game.screen[x][y] else Qt.white
                qp.fillRect(x * PIXEL_WIDTH, y * PIXEL_HEIGHT,
                            PIXEL_WIDTH, PIXEL_HEIGHT, color)


class ScreenFillerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(64 * PIXEL_WIDTH, 32 * PIXEL_HEIGHT)
