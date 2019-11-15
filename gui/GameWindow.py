import os
import threading

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QUrl, QTimer, pyqtSlot
from PyQt5.QtGui import QPainter
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QMainWindow, QGridLayout

from chip8 import CHIP8
# noinspection PyUnresolvedReferences
from config import PIXEL_SIZE_DEBUG, PIXEL_SIZE, PIXEL_SIZE_DEBUG, KEYBOARD, WIDTH, HEIGHT
from gui.DebugWidget import DebugWidget


class GameWindow(QMainWindow):
    DEBUG = False

    def __init__(self, rom, speed, delay, parent=None):
        super().__init__(parent)
        self.rom = rom
        title = rom
        if self.DEBUG:
            title += " (DEBUG)"
        self.setWindowTitle(title)
        self.game = CHIP8()

        if self.DEBUG:
            global PIXEL_SIZE
            PIXEL_SIZE = PIXEL_SIZE_DEBUG
        else:
            global DEBUG_WINDOW_WIDTH
            DEBUG_WINDOW_WIDTH = 0
        self.setFixedSize(WIDTH * PIXEL_SIZE + DEBUG_WINDOW_WIDTH,
                          HEIGHT * PIXEL_SIZE)

        url = QUrl.fromLocalFile(os.path.abspath("sound.wav"))
        content = QMediaContent(url)
        self.player = QMediaPlayer()
        self.player.setMedia(content)
        self.game.load_rom(self.rom)

        self.delay = delay
        self.speed = speed

        _layout = QGridLayout()
        _layout.setSpacing(5)
        _layout.addWidget(ScreenFillerWidget(), 0, 0)

        if self.DEBUG:
            self.debug_widget = DebugWidget(self.game)
            self.debug_widget.sig_execute.connect(self.execute_one_instruction)
            _layout.addWidget(self.debug_widget, 0, 1)

        else:
            self.start_timer(delay, self.game.decrement_sound_timer)
            self.start_timer(delay, self.game.decrement_delay_timer)

            thread = threading.Thread(target=self.execute_instructions,
                                      args=(delay, speed))

            thread.start()

        _window = QtWidgets.QWidget()
        _window.setLayout(_layout)
        self.setCentralWidget(_window)

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

            if self.game.draw_flag:
                self.update()
                self.game.draw_flag = False

        self.game.decrement_delay_timer()
        self.game.decrement_sound_timer()
        if self.game.timers['sound'] == 1:
            self.player.play()

        self.debug_widget.update_registers()

    def execute_instructions(self, delay, speed):
        while self.game.running:
            for _ in range(delay):
                for _ in range(speed):
                    continue
                self.game.emulate_cycle()

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
        for y in range(HEIGHT):
            for x in range(WIDTH):
                color = Qt.black if not self.game.screen[x][y] else Qt.white
                qp.fillRect(x * PIXEL_SIZE, y * PIXEL_SIZE,
                            PIXEL_SIZE, PIXEL_SIZE, color)


class ScreenFillerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(WIDTH * PIXEL_SIZE, HEIGHT * PIXEL_SIZE)
