import unittest
from unittest.mock import patch

from chip8 import CHIP8


class TestHelperFunctions(unittest.TestCase):
    def setUp(self):
        self.game = CHIP8()
        self.v_registers = self.game.registers['v']

    def test_get_x_and_y(self):
        self.game.opcode = 0x0120
        x, y = self.game.get_x_and_y()
        self.assertEqual(1, x)
        self.assertEqual(2, y)

    def test_set_pc_to_value(self):
        with self.assertRaises(Exception):
            self.game.set_pc_to_val(-999)

    def test_out_of_memory(self):
        with self.assertRaises(Exception):
            for x in range(4096):
                self.game.emulate_cycle(opcode=0x0111)

    def test_stack_overflow(self):
        with self.assertRaises(Exception):
            for x in range(18):
                self.game.emulate_cycle(opcode=0x2111)

    def test_clear_screen(self):
        for i in range(2, 10):
            for j in range(1, 6):
                self.game.screen[i][j] = 1
        self.game.opcode = 0x00E0
        self.game.clear_screen()
        for i in range(64):
            for j in range(32):
                self.assertEqual(0, self.game.screen[i][j])

    def test_game_is_paused(self):
        self.game.emulate_cycle(0x0111)
        self.assertEqual(514, self.game.registers["pc"])
        self.game.is_paused = True
        self.game.emulate_cycle(0x0111)
        self.assertEqual(514, self.game.registers["pc"])

    def test_extract_opcode_from_memory(self):
        self.game.memory[512] = 0x0f
        self.game.memory[513] = 0x00ff
        self.game.emulate_cycle()
        self.assertEqual(0x0fff, self.game.opcode)
        self.assertEqual(514, self.game.registers["pc"])

class TestLogicalOperations(unittest.TestCase):
    """
    opcode: 0x8**
    """

    def setUp(self):
        self.game = CHIP8()
        self.v_registers = self.game.registers['v']

    def test_load_vy_to_vx(self):
        self.game.opcode = 0x8120
        self.v_registers[2] = 11
        self.assertEqual(0, self.v_registers[1])
        self.game.put_vy_to_vx()
        self.assertEqual(11, self.v_registers[1])

    def test_logical_or(self):
        self.game.opcode = 0x8121
        self.v_registers[1] = 0b101010
        self.v_registers[2] = 0b010101
        self.game.vx_or_vy()
        self.assertEqual(0b111111, self.v_registers[1])
        self.assertEqual(0b010101, self.v_registers[2])

    def test_logical_and(self):
        self.game.opcode = 0x8122
        self.v_registers[1] = 0b101010
        self.v_registers[2] = 0b010101
        self.game.vx_and_vy()
        self.assertEqual(0b000000, self.v_registers[1])
        self.assertEqual(0b010101, self.v_registers[2])

    def test_logical_xor(self):
        self.game.opcode = 0x8123
        self.v_registers[1] = 0b111111
        self.v_registers[2] = 0b010101
        self.game.vx_xor_vy()
        self.assertEqual(0b101010, self.v_registers[1])
        self.assertEqual(0b010101, self.v_registers[2])

    def test_sum_vx_and_vy_no_overflow(self):
        self.game.opcode = 0x8214
        self.assertEqual(0, self.v_registers[15])
        self.v_registers[1] = 21
        self.v_registers[2] = 25
        self.game.sum_vx_and_vy()
        self.assertEqual(0, self.v_registers[15])
        self.assertEqual(46, self.v_registers[2])
        self.assertEqual(21, self.v_registers[1])

    def test_sum_vx_and_vy_overflow(self):
        self.game.opcode = 0x8124
        self.assertEqual(0, self.v_registers[15])
        self.v_registers[1] = 255
        self.v_registers[2] = 1
        self.game.sum_vx_and_vy()
        self.assertEqual(1, self.v_registers[15])
        self.assertEqual(0, self.v_registers[1])
        self.assertEqual(1, self.v_registers[2])

    def test_subtract_vx_and_vy_no_overflow(self):
        self.game.opcode = 0x8125
        self.assertEqual(0, self.v_registers[15])
        self.v_registers[1] = 12
        self.v_registers[2] = 2
        self.game.subtract_vx_and_vy()
        self.assertEqual(1, self.v_registers[15])
        self.assertEqual(10, self.v_registers[1])
        self.assertEqual(2, self.v_registers[2])

    def test_subtract_vx_and_vy_overflow(self):
        self.game.opcode = 0x8125
        self.assertEqual(0, self.v_registers[15])
        self.v_registers[1] = 0
        self.v_registers[2] = 2
        self.game.subtract_vx_and_vy()
        self.assertEqual(0, self.v_registers[15])
        self.assertEqual(254, self.v_registers[1])
        self.assertEqual(2, self.v_registers[2])

    def test_shift_right_lost_one(self):
        self.game.opcode = 0x8126
        self.v_registers[1] = 0b1001
        self.game.shift_right_vx()
        self.assertEqual(1, self.v_registers[15])
        self.assertEqual(0b0100, self.v_registers[1])

    def test_shift_right_lost_zero(self):
        self.game.opcode = 0x8126
        self.v_registers[1] = 0b1000
        self.game.shift_right_vx()
        self.assertEqual(0, self.v_registers[15])
        self.assertEqual(0b0100, self.v_registers[1])

    def test_subtract_vy_and_vx_no_overflow(self):
        self.game.opcode = 0x8127
        self.assertEqual(0, self.v_registers[15])
        self.v_registers[1] = 12
        self.v_registers[2] = 20
        self.game.subtract_vy_and_vx()
        self.assertEqual(1, self.v_registers[15])
        self.assertEqual(8, self.v_registers[1])
        self.assertEqual(20, self.v_registers[2])

    def test_subtract_vy_and_vx_overflow(self):
        self.game.opcode = 0x8127
        self.assertEqual(0, self.v_registers[15])
        self.v_registers[1] = 4
        self.v_registers[2] = 0
        self.game.subtract_vy_and_vx()
        self.assertEqual(0, self.v_registers[15])
        self.assertEqual(252, self.v_registers[1])
        self.assertEqual(0, self.v_registers[2])

    def test_shift_left_lost_one(self):
        self.game.opcode = 0x812e
        self.v_registers[1] = 0b10010000
        self.game.shift_left_vx()
        self.assertEqual(1, self.v_registers[15])
        self.assertEqual(0b00100000, self.v_registers[1])

    def test_shift_left_lost_zero(self):
        self.game.opcode = 0x812e
        self.v_registers[1] = 0b00010000
        self.game.shift_left_vx()
        self.assertEqual(0, self.v_registers[15])
        self.assertEqual(0b00100000, self.v_registers[1])


class TestFFunctions(unittest.TestCase):
    def setUp(self):
        self.game = CHIP8()
        self.v_registers = self.game.registers['v']

    def test_put_key_to_vx(self):
        for i in range(12):
            self.assertEqual(512, self.game.registers['pc'])
            self.assertEqual(0, self.v_registers[1])
            self.game.emulate_cycle(opcode=0xf10a)
            self.assertEqual(512, self.game.registers['pc'])
            self.assertEqual(0, self.v_registers[1])
        self.game.keys[10] = True
        self.game.emulate_cycle(opcode=0xf10a)
        self.assertEqual(514, self.game.registers['pc'])
        self.assertEqual(10, self.v_registers[1])
        self.assertEqual(False, self.game.keys[10])

    def test_skip_if_key_pressed(self):
        self.v_registers[1] = 1
        self.game.emulate_cycle(0xe19e)
        self.assertEqual(514, self.game.registers["pc"])
        self.game.keys[1] = True
        self.game.emulate_cycle(0xe19e)
        self.assertEqual(518, self.game.registers["pc"])

    def test_skip_if_key_not_pressed(self):
        self.v_registers[1] = 1
        self.game.keys[1] = True
        self.game.emulate_cycle(0xe1a1)
        self.assertEqual(514, self.game.registers["pc"])
        self.game.keys[1] = False
        self.game.emulate_cycle(0xe1a1)
        self.assertEqual(518, self.game.registers["pc"])

    def test_put_vx_to_sound(self):
        self.game.opcode = 0xf218
        self.v_registers[2] = 101
        self.assertEqual(0, self.game.timers['sound'])
        self.game.put_vx_to_sound()
        self.assertEqual(101, self.game.timers['sound'])

    def test_put_delay_timer_to_reg(self):
        self.game.opcode = 0xf207
        self.game.timers['delay'] = 12
        self.assertEqual(0, self.game.registers['v'][2])
        self.game.put_delay_to_vx()
        self.assertEqual(12, self.game.registers['v'][2])

    def test_sum_idx_and_vx(self):
        self.game.opcode = 0xf21e
        self.v_registers[2] = 11
        self.game.registers['index'] = 12
        self.game.sum_idx_and_vx()
        self.assertEqual(11, self.v_registers[2])
        self.assertEqual(23, self.game.registers['index'])

    def test_save_vx_to_memory(self):
        self.game.registers['index'] = 514
        for i in range(15):
            self.v_registers[i] = i
        self.game.opcode = 0xf555
        for i in range(6):
            self.assertEqual(0, self.game.memory[self.game.registers[
                                                     'index'] + i])
        self.game.put_v_reg_to_memory()
        for i in range(6):
            self.assertEqual(i, self.game.memory[self.game.registers[
                                                     'index'] + i])
        for i in range(6, 16):
            self.assertEqual(0, self.game.memory[self.game.registers[
                                                     'index'] + i])

    def test_memory_to_vx(self):
        self.game.opcode = 0xf465
        self.game.registers['index'] = 1
        for i in range(10):
            self.game.memory[self.game.registers['index'] + i] = 21
        self.game.put_memory_to_v_reg()
        for i in range(5):
            self.assertEqual(21, self.game.registers['v'][i])
        for i in range(5, 16):
            self.assertEqual(0, self.game.registers['v'][i])

    def test_set_delay_timer(self):
        self.game.opcode = 0xf215
        self.v_registers[2] = 2
        self.assertEqual(0, self.game.timers['delay'])
        self.game.put_vx_to_delay()
        self.assertEqual(2, self.game.timers['delay'])

    def test_set_idx_to_location(self):
        self.game.opcode = 0xf129
        self.game.registers['v'][1] = 12
        self.assertEqual(0, self.game.registers['index'])
        self.game.put_vx_sprite_to_idx()
        self.assertEqual(60, self.game.registers['index'])

    def test_save_vx_to_memory_at_index(self):
        self.game.opcode = 0xf233
        self.v_registers[2] = 333
        self.game.registers['index'] = 555
        for i in range(555, 558):
            self.assertEqual(0, self.game.memory[i])
        self.game.store_vx_in_bcd()
        for i in range(555, 558):
            self.assertEqual(3, self.game.memory[i])


class TestDifferentThings(unittest.TestCase):
    def setUp(self):
        self.game = CHIP8()
        self.v_registers = self.game.registers['v']

    def test_exceptions(self):
        opcodes = [0x8009, 0x880a, 0x800b, 0x800c, 0x800d, 0x800f, 0xf001,
                   0xf021, 0xf905, 0xf451, 0xf028, 0xf006, 0xf204, 0xf005,
                   0xe1a3]
        for opcode in opcodes:
            with self.assertRaises(Exception):
                self.game.emulate_cycle(opcode)

    def test_goto(self):
        self.game.opcode = 0x1000
        self.assertEqual(512, self.game.registers['pc'])
        self.game.jump_to_address()
        self.assertEqual(0, self.game.registers['pc'])

    def test_skip_if_equal_not_equal(self):
        self.game.opcode = 0x3011
        self.assertEqual(512, self.game.registers['pc'])
        self.game.skip_if_vx_equals_value()
        self.assertEqual(512, self.game.registers['pc'])

    def test_skip_if_equal_equal(self):
        self.game.opcode = 0x3011
        self.v_registers[0] = 17  # 0x11
        self.game.skip_if_vx_equals_value()
        self.assertEqual(514, self.game.registers['pc'])

    def test_skip_if_not_equal_equal(self):
        self.game.opcode = 0x4011
        self.v_registers[0] = 17
        self.game.skip_if_vx_not_equals_value()
        self.assertEqual(512, self.game.registers['pc'])

    def test_skip_if_not_equal_not_equal(self):
        self.game.opcode = 0x4011
        self.game.skip_if_vx_not_equals_value()
        self.assertEqual(514, self.game.registers['pc'])

    def test_skip_if_regs_equal_equal(self):
        self.game.opcode = 0x5120
        self.assertEqual(512, self.game.registers['pc'])
        self.v_registers[1] = self.v_registers[2] = 13
        self.game.skip_if_vx_equals_vy()
        self.assertEqual(514, self.game.registers['pc'])

    def test_skip_if_regs_equal_not_equal(self):
        self.game.opcode = 0x5120
        self.assertEqual(512, self.game.registers['pc'])
        self.v_registers[1] = 2
        self.v_registers[2] = 13
        self.game.skip_if_vx_equals_vy()
        self.assertEqual(512, self.game.registers['pc'])

    def test_load_num_to_reg(self):
        self.game.opcode = 0x63ff
        self.assertEqual(0, self.game.registers["v"][3])
        self.game.put_value_to_vx()
        self.assertEqual(255, self.game.registers["v"][3])  # 0x00ff

    def test_load_sum_to_reg_no_overflow(self):
        self.game.opcode = 0x7211
        self.game.registers['v'][2] = 1
        self.game.sum_value_and_vx()
        self.assertEqual(18, self.game.registers['v'][2])

    def test_load_sum_to_reg_overflow(self):
        self.game.opcode = 0x7201
        self.v_registers[2] = 255
        self.game.sum_value_and_vx()
        self.assertEqual(0, self.v_registers[2])

    def test_skip_if_regs_not_equal_equal(self):
        self.game.opcode = 0x9010
        self.v_registers[0] = self.v_registers[1] = 12
        self.assertEqual(512, self.game.registers['pc'])
        self.game.skip_if_vx_not_equals_vy()
        self.assertEqual(512, self.game.registers['pc'])

    def test_skip_if_regs_not_equal_not_equal(self):
        self.game.opcode = 0x9010
        self.v_registers[0] = 1
        self.v_registers[1] = 12
        self.assertEqual(512, self.game.registers['pc'])
        self.game.skip_if_vx_not_equals_vy()
        self.assertEqual(514, self.game.registers['pc'])

    def test_set_val_to_index(self):
        self.game.opcode = 0xa12e
        self.assertEqual(0, self.game.registers["index"])
        self.game.put_value_to_index()
        self.assertEqual(302, self.game.registers["index"])  # 0x012e

    def test_jump_to(self):
        self.game.opcode = 0xb000
        self.v_registers[0] = 1
        self.assertEqual(512, self.game.registers['pc'])
        self.game.jump_to_address_plus_v0()
        self.assertEqual(1, self.game.registers['pc'])

    @patch.object(CHIP8, 'clear_screen', return_value=None)
    @patch.object(CHIP8, 'return_from_subroutine', return_value=None)
    def test_zero_opcode(self, a, b):
        opcodes = [0x00EE, 0x00E0, 0x01E0]
        for code in opcodes:
            self.game.opcode = code
            self.game.return_clear()

    def test_maze(self):

        opcodes = [0x6000, 0x6100, 0xa222, 0xc201, 0x3201, 0xa21e, 0xd014,
                   0x7004, 0x3040, 0x1204, 0xa6000, 0xa7104, 0xa3120,
                   0xa1204,  0xa121c, 0xa8040, 0x010, 0x2040, 0xa8010]
        v_registers = self.game.registers['v']
        registers = self.game.registers
        self.game.emulate_cycle(opcodes[0])
        self.assertEqual(0, v_registers[0])
        self.game.emulate_cycle(opcodes[1])
        self.assertEqual(0, v_registers[1])
        self.game.emulate_cycle(opcodes[2])
        self.assertEqual(546, registers['index'])
        self.game.emulate_cycle(opcodes[3])

    def test_jump_to_return_from_subroutine(self):
        self.game.opcode = 0x2eee
        self.assertEqual(0, self.game.registers["sp"])
        self.assertEqual(0x200, self.game.registers['pc'])

        self.game.call_subroutine()
        self.assertEqual(1, self.game.registers["sp"])
        self.assertEqual(0x0eee, self.game.registers['pc'])

        self.game.opcode = 0x00EE
        self.game.return_from_subroutine()
        self.assertEqual(0, self.game.registers["sp"])
        self.assertEqual(0x200, self.game.registers['pc'])

    def test_draw(self):
        """
        ***.***.
        *.*..*..
        *.*..*..
        :return:
        """
        self.game.memory[512] = 0b11101110
        self.game.memory[513] = 0b10100100
        self.game.memory[514] = 0b10100100
        self.game.registers['index'] = 512
        self.game.opcode = 0xd003
        self.game.draw_sprite()
        for x in range(8):
            if x == 3 or x == 7:
                self.assertEqual(0, self.game.screen[x][0])
            else:
                self.assertEqual(1, self.game.screen[x][0])
        for y in range(1, 3):
            for x in range(8):
                if x in [1, 3, 4, 6, 7]:
                    self.assertEqual(0, self.game.screen[x][y])
                else:
                    self.assertEqual(1, self.game.screen[x][y])
        self.assertEqual(0, self.v_registers[15])

    def test_draw_out_of_border(self):
        self.game.memory[512] = 0b11111111
        self.game.memory[513] = 0b11111111
        self.game.registers['index'] = 512
        self.v_registers[0] = 60
        self.v_registers[1] = 0
        self.game.opcode = 0xd012
        self.game.draw_sprite()
        self.assertEqual(0, self.v_registers[15])
        for y in range(2):
            for x in range(64):
                if x in [0, 1, 2, 3, 60, 61, 62, 63]:
                    self.assertEqual(1, self.game.screen[x][y])
                else:
                    self.assertEqual(0, self.game.screen[x][y])

    def test_draw_overlap(self):
        self.game.memory[512] = 0b11000000
        self.game.memory[513] = 0b11000000
        self.game.registers['index'] = 512
        self.game.opcode = 0xd002
        self.game.draw_sprite()
        self.v_registers[0] = 1
        self.game.opcode = 0xd002
        self.game.draw_sprite()
        self.assertEqual(1, self.v_registers[15])
        for y in range(3):
            for x in range(8):
                if (x == 0 and y == 2) \
                        or (x == 1 and y == 1) \
                        or (x == 2 and y == 0) \
                        or x >= 3:
                    self.assertEqual(0, self.game.screen[x][y])
                else:
                    self.assertEqual(1, self.game.screen[x][y])


if __name__ == '__main__':
    unittest.main()
