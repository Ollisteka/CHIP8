import argparse
import os
import sys
import threading
import time

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from chip8 import CHIP8

KEYBOARD = {
    Qt.Key_1: 0x1,
    Qt.Key_2: 0x2,
    Qt.Key_3: 0x3,
    Qt.Key_4: 0x4,
    Qt.Key_5: 0x5,
    Qt.Key_6: 0x6,
    Qt.Key_7: 0x7,
    Qt.Key_8: 0x8,
    Qt.Key_9: 0x9,
    Qt.Key_0: 0x0,
    Qt.Key_A: 0xa,
    Qt.Key_B: 0xb,
    Qt.Key_C: 0xc,
    Qt.Key_D: 0xd,
    Qt.Key_E: 0xe,
    Qt.Key_F: 0xf,
}

def main():
    parser = argparse.ArgumentParser(
        usage='{} rom'.format(
            os.path.basename(
                sys.argv[0])),
        description='CHIP8 emulator. Play a game which is 30 years old!')
    parser.add_argument('rom', type=str, help='way to rom file')

    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    window = GameWindow(args.rom)
    window.show()

    app.exec_()


class GameThread(QtCore.QObject):
    draw_signal = QtCore.pyqtSignal()
    stop_running = False

    def __init__(self, game, rom):
        super().__init__()
        self._abort = False
        self.game = game
        self.rom = rom

    def start_game(self):
        self.game.load_rom(self.rom)

        while self.game.running:
            if self.stop_running:
                print("EXITING")
                sys.exit()
            time.sleep(.01)
            self.game.emulate_cycle()

            if self.game.draw_flag:
                self.draw_signal.emit()
                self.game.draw_flag = False


class GameWindow(QMainWindow):
    def __init__(self, rom, parent=None):
        super().__init__(parent)
        self.rom = rom
        self.setWindowTitle(rom)

        self.game = CHIP8()
        self.pixel_height = 10
        self.pixel_width = 10

        self.resize(64*self.pixel_width, 32*self.pixel_height)

        self.game_thread = GameThread(self.game, rom)
        self.game_thread.draw_signal.connect(self.call_repaint)
        thread = threading.Thread(target=self.game_thread.start_game)
        thread.start()

    @QtCore.pyqtSlot()
    def call_repaint(self):
        self.repaint()

    def closeEvent(self, event):
        self.game_thread.stop_running = True
        event.accept()

    def keyPressEvent(self, e):
        if e.key() in KEYBOARD:
            if self.game.waiting_for_key:
                self.game.key_pressed = KEYBOARD[e.key()]

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        # self.setWindowTitle("Drawing")

        for y in range(32):
            for x in range(64):
                color = Qt.black if not self.game.screen[x][y] else Qt.white
                qp.setBrush(color)
                qp.drawRect(x*self.pixel_width, y*self.pixel_height,
                            self.pixel_width, self.pixel_height)


if __name__ == '__main__':
    main()
