import argparse
import os
import sys
import threading

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QPainter, QFont
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QMainWindow, QPushButton, QGridLayout, QLabel, \
    QLineEdit, QVBoxLayout

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

PIXEL_HEIGHT = 15
PIXEL_WIDTH = 15

DEBUG_WINDOW_WIDTH = 400


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

    window = GameWindow(args.rom, args.speed + 1, args.delay + 1)
    window.show()

    app.exec_()


class ScreenFillerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(64 * PIXEL_WIDTH, 32 * PIXEL_HEIGHT)


class DebugWidget(QtWidgets.QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        super().setFont(QFont('Serif', 10, QFont.Light))
        self.game = game
        current_opcode_label = QLabel()
        current_opcode_label.setText("Current opcode:")
        current_opcode_label.setFont(QFont('Serif', 10, QFont.Bold))

        reg_dump = self.game.get_reg_dump()

        self.current_opcode = QLineEdit()
        self.current_opcode.setText(reg_dump["current_opcode"])
        self.current_opcode.setReadOnly(True)

        self.v_reg_labels = self.get_v_reg_labels(reg_dump)
        self.other_regs = self.get_other_regs(reg_dump)

        self.execute_button = QPushButton()
        self.execute_button.setText("EXECUTE")
        self.execute_button.released.connect(self.execute_opcode)
        _cur_code_layout = QGridLayout()
        _cur_code_layout.setSpacing(5)
        _cur_code_layout.addWidget(current_opcode_label, 0, 0)
        _cur_code_layout.addWidget(self.current_opcode, 0, 1)

        _reg_layout = QGridLayout()
        _reg_layout.setSpacing(3)
        for i in range(0, len(self.v_reg_labels)):
            label, line_edit = self.v_reg_labels[i]
            _reg_layout.addWidget(label, i, 2)
            _reg_layout.addWidget(line_edit, i, 3)
        for i in range(0, len(self.other_regs)):
            label, line_edit = self.other_regs[i]
            _reg_layout.addWidget(label, i, 0)
            _reg_layout.addWidget(line_edit, i, 1)

        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.addLayout(_cur_code_layout)
        layout.addLayout(_reg_layout)
        layout.addWidget(self.execute_button)
        self.setLayout(layout)

    def get_other_regs(self, reg_dump):
        return [self.make_labeled_line_edit("Program "
                                            "counter: ",
                                            reg_dump["pc"]),

                self.make_labeled_line_edit("Index register: ",
                                            reg_dump[
                                                "index"]),

                self.make_labeled_line_edit("Stack pointer: ",
                                            reg_dump["sp"]),

                self.make_labeled_line_edit("Sound timer: ",
                                            reg_dump["timers"]["sound"]),

                self.make_labeled_line_edit("Delay timer: ",
                                            reg_dump["timers"]["delay"]),
                ]

    def get_v_reg_labels(self, reg_dump):
        v_regs = reg_dump["v"]
        return [(self.make_label("V" + str(i) + ": "), self.make_line_edit(
            v_regs[i]))
                for i in v_regs]

    def make_labeled_line_edit(self, description, text):
        return self.make_label(description), self.make_line_edit(text)

    def make_label(self, text):
        label = QLabel()
        label.setText(text)
        label.setAlignment(Qt.AlignRight)
        return label

    def make_line_edit(self, text):
        line_edit = QLineEdit()
        line_edit.setText(text)
        line_edit.setReadOnly(True)
        return line_edit

    def execute_opcode(self):
        print("HEY")
        # self.game.emulate_cycle()


class GameWindow(QMainWindow):
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

        thread = threading.Thread(target=self.execute_instructions,
                                  args=(delay, speed))
        thread.start()

    def start_timer(self, interval, func):
        timer = QTimer(self)
        timer.setInterval(interval)
        timer.timeout.connect(func)
        timer.start()

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


if __name__ == '__main__':
    main()
