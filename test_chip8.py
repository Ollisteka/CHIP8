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

    def test_jump_to_return_from_subroutine(self):
        self.game.opcode = 0x2eee
        self.assertEqual(len(self.game.stack), 0)
        self.assertEqual(self.game.registers['pc'], 0x200)
        self.game.call_subroutine()
        self.assertEqual(len(self.game.stack), 1)
        self.assertEqual(self.game.registers['pc'], 0x0eee)

        self.game.opcode = 0x00EE
        self.game.return_from_subroutine()
        self.assertEqual(len(self.game.stack), 0)
        self.assertEqual(self.game.registers['pc'], 0x200)

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

    def test_load_sum_to_reg(self):
        self.game.opcode = 0x7211
        self.game.registers['v'][2] = 1
        self.game.load_sum_to_reg()
        self.assertEqual(self.game.registers['v'][2], 18)
        self.game.registers['v'][2] = 255
        self.game.load_sum_to_reg()
        self.assertEqual(self.game.registers['v'][2], 16)

    def test_set_delay_timer(self):
        self.game.opcode = 0xf215
        self.assertEqual(self.game.timers['delay'], 0)
        self.game.set_delay_timer()
        self.assertEqual(self.game.timers['delay'], 2)

    def test_set_idx_to_location(self):
        self.game.opcode = 0xf129
        self.game.registers['v'][1] = 12
        self.assertEqual(self.game.registers['index'], 0)
        self.game.set_idx_to_location()
        self.assertEqual(self.game.registers['index'], 12)

    def test_skip_if(self):
        self.game.opcode = 0x3011
        self.assertEqual(self.game.registers['pc'], 512)
        self.game.skip_if()
        self.assertEqual(self.game.registers['pc'], 512)
        self.game.registers['v'][0] = 17
        self.game.skip_if()
        self.assertEqual(self.game.registers['pc'], 514)

    def test_put_delay_timer_to_reg(self):
        self.game.opcode = 0xf207
        self.game.timers['delay'] = 12
        self.assertEqual(self.game.registers['v'][2], 0)
        self.game.put_delay_timer_to_reg()
        self.assertEqual(self.game.registers['v'][2], 12)

    @patch.object(CHIP8, 'clear_screen', return_value=None)
    @patch.object(CHIP8, 'return_from_subroutine', return_value=None)
    def test_zero_opcode(self, a, b):
        opcodes = [0x00EE, 0x00E0, 0x01E0]
        for code in opcodes:
            self.game.opcode = code
            if code == 0x01E0:
                with self.assertRaises(Exception):
                    self.game.return_clear()
            else:
                self.game.return_clear()



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
