import argparse
import os
import sys
import threading

from PyQt5 import QtWidgets
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

PIXEL_HEIGHT = 10
PIXEL_WIDTH = 10


def main():
    parser = argparse.ArgumentParser(
        usage='{} rom'.format(
            os.path.basename(
                sys.argv[0])),
        description='CHIP8 emulator. Play a game which is 30 years old!',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('rom', type=str, help='way to rom file')
    parser.add_argument('-s', '--speed', type=int, default=12000,
                        help='try to adjust CPU speed. The bigger the value '
                             'is, the slower the game speed gets')
    parser.add_argument('-d', '--delay', type=int, default=10,
                        help='try to adjust delay timer. The bigger the '
                             'value is, the slower things move')

    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    window = GameWindow(args.rom, args.speed, args.delay)
    window.show()

    app.exec_()


class GameWindow(QMainWindow):
    def __init__(self, rom, speed, delay, parent=None):
        super().__init__(parent)
        self.rom = rom
        self.setWindowTitle(rom)

        self.game = CHIP8()

        self.setFixedSize(64 * PIXEL_WIDTH, 32 * PIXEL_HEIGHT)

        url = QUrl.fromLocalFile(os.path.abspath("sound.wav"))
        content = QMediaContent(url)
        self.player = QMediaPlayer()
        self.player.setMedia(content)

        self.game.load_rom(self.rom)

        thread = threading.Thread(target=self.execute_instructions,
                                  args=(delay, speed))
        thread.start()

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

            self.game.decrement_sound_timer()
            self.game.decrement_delay_timer()

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


if __name__ == '__main__':
    main()
