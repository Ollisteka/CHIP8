import argparse
import os
import sys
import threading
import time

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QPainter
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QMainWindow

from chip8 import CHIP8

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
    sound_signal = QtCore.pyqtSignal()
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
                sys.exit()
            time.sleep(.004)
            self.game.emulate_cycle()

            if self.game.draw_flag:
                self.draw_signal.emit()
                self.game.draw_flag = False
            if self.game.timers['sound'] == 1:
                self.sound_signal.emit()


class GameWindow(QMainWindow):
    def __init__(self, rom, parent=None):
        super().__init__(parent)
        self.rom = rom
        self.setWindowTitle(rom)

        self.game = CHIP8()
        self.pixel_height = 10
        self.pixel_width = 10

        self.resize(64*self.pixel_width, 32*self.pixel_height)

        url = QUrl.fromLocalFile(os.path.abspath("sound.wav"))
        content = QMediaContent(url)
        self.player = QMediaPlayer()
        self.player.setMedia(content)

        self.game_thread = GameThread(self.game, rom)
        self.game_thread.draw_signal.connect(self.call_repaint)
        self.game_thread.sound_signal.connect(self.make_sound)
        thread = threading.Thread(target=self.game_thread.start_game)
        thread.start()

    @QtCore.pyqtSlot()
    def call_repaint(self):
        self.repaint()

    @QtCore.pyqtSlot()
    def make_sound(self):
        self.player.play()

    def closeEvent(self, event):
        self.game_thread.stop_running = True
        event.accept()

    def keyPressEvent(self, e):
        if e.key() in KEYBOARD.keys():
            self.game.keys[KEYBOARD[e.key()]] = True

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
                qp.setBrush(color)
                qp.drawRect(x*self.pixel_width, y*self.pixel_height,
                            self.pixel_width, self.pixel_height)


if __name__ == '__main__':
    main()
