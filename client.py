import argparse
import os
import sys

from chip8 import CHIP8


def main():
    parser = argparse.ArgumentParser(
        usage='{} rom'.format(
            os.path.basename(
                sys.argv[0])),
        description='CHIP8 emulator. Play a game which is 30 years old!')
    parser.add_argument('rom', type=str, help='way to rom file')

    args = parser.parse_args()

    game = CHIP8()
    game.load_rom(args.rom)

    while game.running:
        game.emulate_cycle()

if __name__ == '__main__':
    main()
