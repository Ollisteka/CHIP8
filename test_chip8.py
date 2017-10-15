import unittest
from unittest.mock import patch
from chip8 import CHIP8


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.game = CHIP8()

    def test_set_val_to_index(self):
        self.game.opcode = 0xa12e
        self.assertEqual(self.game.registers["index"], 0)
        self.game.set_val_to_index()
        self.assertEqual(self.game.registers["index"], 0x012e)

    def test_load_num_to_reg(self):
        self.game.opcode = 0x63ff
        self.assertEqual(self.game.registers["v"][3], 0)
        self.game.load_num_to_reg()
        self.assertEqual(self.game.registers["v"][3], 0x00ff)

    def test_jump_to_subroutine(self):
        self.game.opcode = 0x2eee
        self.assertEqual(len(self.game.stack), 0)
        self.assertEqual(self.game.registers['pc'], 0x200)
        self.game.call_subroutine()
        self.assertEqual(len(self.game.stack), 1)
        self.assertEqual(self.game.registers['pc'], 0x0eee)

    def test_save_vx_to_idx(self):
        self.game.opcode = 0xf133
        self.game.registers['v'][1] = 333
        for i in range(3):
            self.assertEqual(self.game.memory[self.game.registers['index'] +
                                              i], 0)
        self.game.save_vx_to_index()
        for i in range(3):
            self.assertEqual(self.game.memory[self.game.registers['index'] +
                                              i], 3)

    def test_memory_to_vx(self):
        self.game.opcode = 0x365
        self.game.registers['index'] = 1
        for i in range(10):
            self.game.memory[self.game.registers['index'] + i] = 21
        self.game.save_memory_to_vx()
        for i in range(5):
            self.assertEqual(self.game.registers['v'][i], 21)

    # @patch('chip8.CHIP8.call_subroutine')
    # def test_b_called(self, mock):
    #     complect = {
    #         0x2242: self.game.call_subroutine,
    #         0x6532: self.game.load_num_to_reg,
    #         0xa523: self.game.set_val_to_index,
    #         0xd424: self.game.draw_sprite,
    #         0xf233: self.game.f_functions,
    #     }
    #     for key in complect.keys():
    #         with mock.patch.object(self.game, 'opcode', return_value=key):
    #             self.game.emulate_cycle()
    #         self.assertTrue(mock.called)


if __name__ == '__main__':
    unittest.main()
