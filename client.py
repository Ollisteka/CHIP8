import argparse
import os
import sys

from PyQt5 import QtWidgets

from gui.GameWindow import GameWindow


def main():
    parser = argparse.ArgumentParser(
        usage='{} rom'.format(
            os.path.basename(
                sys.argv[0])),
        description='CHIP8 emulator. Play a game which is 30 years old!',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('rom', type=str, help='way to rom file')
    parser.add_argument('--debug', action="store_true",
                        help="Enable debug mode")
    parser.add_argument('-s', '--speed', type=int, default=12000,
                        help='try to adjust CPU speed. The bigger the value '
                             'is, the slower the game speed gets')
    parser.add_argument('-d', '--delay', type=int, default=10,
                        help='try to adjust delay timer. The bigger the '
                             'value is, the slower things move')

    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    GameWindow.DEBUG = args.debug
    window = GameWindow(args.rom, args.speed + 1, args.delay + 1)
    window.show()

    app.exec_()


if __name__ == '__main__':
    main()
