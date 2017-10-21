import unittest
from unittest.mock import patch

from chip8 import CHIP8


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.game = CHIP8()

    def test_set_val_to_index(self):
        self.game.opcode = 0xa12e
        self.assertEqual(0, self.game.registers["index"])
        self.game.set_val_to_index()
        self.assertEqual(302, self.game.registers["index"])  # 0x012e

    def test_load_num_to_reg(self):
        self.game.opcode = 0x63ff
        self.assertEqual(0, self.game.registers["v"][3])
        self.game.load_num_to_reg()
        self.assertEqual(255, self.game.registers["v"][3])  # 0x00ff

    def test_jump_to_return_from_subroutine(self):
        self.game.opcode = 0x2eee
        self.assertEqual(0, len(self.game.stack))
        self.assertEqual(0x200, self.game.registers['pc'])
        self.game.call_subroutine()
        self.assertEqual(1, len(self.game.stack))
        self.assertEqual(0x0eee, self.game.registers['pc'])

        self.game.opcode = 0x00EE
        self.game.return_from_subroutine()
        self.assertEqual(0, len(self.game.stack))
        self.assertEqual(0x200, self.game.registers['pc'])

    def test_save_vx_to_idx(self):
        self.game.opcode = 0xf133
        self.game.registers['index'] = 512
        self.game.registers['v'][1] = 333
        for i in range(3):
            self.assertEqual(0, self.game.memory[self.game.registers[
                                                     'index'] + i])
        self.game.save_vx_to_index()
        for i in range(3):
            self.assertEqual(3, self.game.memory[self.game.registers[
                                                     'index'] + i])

    def test_memory_to_vx(self):
        self.game.opcode = 0x365
        self.game.registers['index'] = 1
        for i in range(10):
            self.game.memory[self.game.registers['index'] + i] = 21
        self.game.save_memory_to_vx()
        for i in range(5):
            self.assertEqual(21, self.game.registers['v'][i])

    def test_load_sum_to_reg(self):
        self.game.opcode = 0x7211
        self.game.registers['v'][2] = 1
        self.game.load_sum_to_reg()
        self.assertEqual(18, self.game.registers['v'][2])
        # overflow
        self.game.registers['v'][2] = 255
        self.game.load_sum_to_reg()
        self.assertEqual(16, self.game.registers['v'][2])

    def test_set_delay_timer(self):
        self.game.opcode = 0xf215
        self.assertEqual(0, self.game.timers['delay'])
        self.game.set_delay_timer()
        self.assertEqual(2, self.game.timers['delay'])

    def test_set_idx_to_location(self):
        self.game.opcode = 0xf129
        self.game.registers['v'][1] = 12
        self.assertEqual(0, self.game.registers['index'])
        self.game.set_idx_to_location()
        self.assertEqual(12, self.game.registers['index'])

    def test_skip_if(self):
        self.game.opcode = 0x3011
        self.assertEqual(512, self.game.registers['pc'])
        self.game.skip_if()
        self.assertEqual(512, self.game.registers['pc'])
        self.game.registers['v'][0] = 17  # 0x11
        self.game.skip_if()
        self.assertEqual(514, self.game.registers['pc'])

    def test_put_delay_timer_to_reg(self):
        self.game.opcode = 0xf207
        self.game.timers['delay'] = 12
        self.assertEqual(0, self.game.registers['v'][2])
        self.game.put_delay_timer_to_reg()
        self.assertEqual(12, self.game.registers['v'][2])

    def test_goto(self):
        self.game.opcode = 0x1000
        self.game.goto()
        self.assertEqual(0, self.game.registers['pc'])

    # def test_rnd_to_vx(self):
    #     self.game.opcode = 0xc111
    #     with patch('randint', return_value=0):
    #         self.game.set_rnd_to_vx()
    #         self.assertEqual(0, self.game.registers['v'][1])

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
