from random import randint

NOT_A_KEY = -999
FONTS = [
  0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
  0x20, 0x60, 0x20, 0x20, 0x70, # 1
  0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
  0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
  0x90, 0x90, 0xF0, 0x10, 0x10, # 4
  0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
  0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
  0xF0, 0x10, 0x20, 0x40, 0x40, # 7
  0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
  0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
  0xF0, 0x90, 0xF0, 0x90, 0x90, # A
  0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
  0xF0, 0x80, 0x80, 0x80, 0xF0, # C
  0xE0, 0x90, 0x90, 0x90, 0xE0, # D
  0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
  0xF0, 0x80, 0xF0, 0x80, 0x80  # F
]


class CHIP8:
    def __init__(self):
        self.running = True
        self.shift_only_vx = True
        self.draw_flag = False
        self.opcode = 0
        self.screen = self.__init_screen()
        self.memory = bytearray(4096)
        self.__load_fonts()
        self.registers = {
            "pc": 512,  # 16 bit
            "index": 0,  # 16 bit
            "sp": 0,
            "v": {key: 0 for key in range(16)}  # 8 bit
        }
        self.timers = {
            "sound": 0,  # 8 bit
            "delay": 0  # 8 bit
        }
        self.timers_sync = 0
        self.stack = [0] * 16
        self.keys = {key: False for key in range(16)}
        self.opcode_table = {
            0x0: self.clear_return,
            0x1: self.jump_to_address,
            0x2: self.call_subroutine,
            0x3: self.skip_if_vx_equals_value,
            0x4: self.skip_if_vx_not_equals_value,
            0x5: self.skip_if_vx_equals_vy,
            0x6: self.put_value_to_vx,
            0x7: self.sum_value_and_vx,
            0x8: self.logical_operations,
            0x9: self.skip_if_vx_not_equals_vy,
            0xa: self.put_value_to_index,
            0xb: self.jump_to_address_plus_v0,
            0xc: self.put_rnd_to_vx,
            0xd: self.draw_sprite,
            0xe: self.skip_if_key,
            0xf: self.execute_f_func
        }
        self.logical_operations_table = {
            0x0: self.put_vy_to_vx,
            0x1: self.vx_or_vy,
            0x2: self.vx_and_vy,
            0x3: self.vx_xor_vy,
            0x4: self.sum_vx_and_vy,
            0x5: self.subtract_vx_and_vy,
            0x6: self.shift_right_vx,
            0x7: self.subtract_vy_and_vx,
            0xe: self.shift_left_vx,
        }
        self.f_operations_table = {
            0x07: self.put_delay_to_vx,
            0x0a: self.put_key_to_vx,
            0x15: self.put_vx_to_delay,
            0x18: self.put_vx_to_sound,
            0x1e: self.sum_idx_and_vx,
            0x29: self.put_vx_sprite_to_idx,
            0x33: self.store_vx_in_bcd,
            0x55: self.put_v_reg_to_memory,
            0x65: self.put_memory_to_v_reg
        }

    @staticmethod
    def __init_screen():
        screen = []
        for x in range(64):
            screen.append([0] * 32)
        return screen

    def __load_fonts(self):
        offset = 0
        for item in FONTS:
            self.memory[offset] = item
            offset += 1
        return

    def load_rom(self, rom):
        data = open(rom, 'rb').read()
        for index, val in enumerate(data):
            self.memory[512 + index] = val

    def emulate_cycle(self, opcode=None):
        pc = self.registers['pc']
        if opcode:
            self.opcode = opcode
        else:
            self.opcode = (self.memory[pc] << 8) | self.memory[pc + 1]
            self.registers['pc'] += 2
        operation = (self.opcode & 0xF000) >> 12
        print(hex(self.opcode))
        try:
            self.opcode_table[operation]()
        except KeyError:
            raise Exception("Operation {} is not supported".format(hex(
                self.opcode)))

        self.timers_sync += 1
        if self.timers_sync % 8 == 0:
            if self.timers['delay'] > 0:
                self.timers['delay'] -= 1

            if self.timers['sound'] > 0:
                self.timers['sound'] -= 1

    def clear_return(self):
        operation = self.opcode & 0x00FF
        sub_operation = operation & 0x00F0
        if sub_operation == 0x00C0:
            raise Exception("Operation {} is not supported".format(hex(
                self.opcode)))

        elif operation == 0x00E0:
            self.clear_screen()

        elif operation == 0x00EE:
            self.return_from_subroutine()

        elif operation == 0x00FB:
            raise Exception("Operation {} is not supported".format(hex(
                self.opcode)))

        elif operation == 0x00FC:
            raise Exception("Operation {} is not supported".format(hex(
                self.opcode)))

        elif operation == 0x00FD:
            raise Exception("Operation {} is not supported".format(hex(
                self.opcode)))

        elif operation == 0x00FE:
            raise Exception("Operation {} is not supported".format(hex(
                self.opcode)))

        elif operation == 0x00FF:
            raise Exception("Operation {} is not supported".format(hex(
                self.opcode)))
        else:
            raise Exception("Operation {} is not supported".format(hex(
                self.opcode)))

    def set_pc_to_val(self, value):
        self.registers["pc"] = value

    def get_x_and_y(self):
        x_num = (self.opcode & 0x0F00) >> 8
        y_num = (self.opcode & 0x00F0) >> 4
        return x_num, y_num

    def clear_screen(self):
        self.screen = self.__init_screen()

    def return_from_subroutine(self):
        self.set_pc_to_val(self.stack[self.registers["sp"]])
        self.registers["sp"] -= 1

    def jump_to_address(self):
        self.set_pc_to_val(self.opcode & 0x0FFF)

    def call_subroutine(self):
        self.registers["sp"] += 1
        self.stack[self.registers["sp"]] = self.registers["pc"]
        self.set_pc_to_val(self.opcode & 0x0FFF)

    def skip_if_vx_equals_value(self):
        x_num = (self.opcode & 0x0F00) >> 8
        if self.registers["v"][x_num] == (self.opcode & 0x00FF):
            self.registers["pc"] += 2

    def skip_if_vx_not_equals_value(self):
        x_num = (self.opcode & 0x0F00) >> 8
        if self.registers["v"][x_num] != (self.opcode & 0x00FF):
            self.registers["pc"] += 2

    def skip_if_vx_equals_vy(self):
        x_num, y_num = self.get_x_and_y()
        if self.registers["v"][x_num] == self.registers["v"][y_num]:
            self.registers["pc"] += 2

    def put_value_to_vx(self):
        x_num = (self.opcode & 0x0F00) >> 8
        self.registers["v"][x_num] = self.opcode & 0x00FF

    def sum_value_and_vx(self):
        x_num = (self.opcode & 0x0F00) >> 8
        x_value = self.registers["v"][x_num]
        temp = x_value + (self.opcode & 0x00FF)
        self.registers["v"][x_num] = temp % 256

    def logical_operations(self):
        operation = self.opcode & 0x000F
        try:
            self.logical_operations_table[operation]()
        except KeyError:
            raise Exception(
                "Operation {} is not supported".format(hex(self.opcode)))

    def put_vy_to_vx(self):
        x_num, y_num = self.get_x_and_y()
        self.registers["v"][x_num] = self.registers["v"][y_num]

    def get_xvalue_and_yvalue(self, x_num, y_num):
        return self.registers["v"][x_num], self.registers["v"][y_num]

    def vx_or_vy(self):
        x_num, y_num = self.get_x_and_y()
        x_value, y_value = self.get_xvalue_and_yvalue(x_num, y_num)
        self.registers["v"][x_num] = x_value | y_value

    def vx_and_vy(self):
        x_num, y_num = self.get_x_and_y()
        x_value, y_value = self.get_xvalue_and_yvalue(x_num, y_num)
        self.registers["v"][x_num] = x_value & y_value

    def vx_xor_vy(self):
        x_num, y_num = self.get_x_and_y()
        x_value, y_value = self.get_xvalue_and_yvalue(x_num, y_num)
        self.registers["v"][x_num] = x_value ^ y_value

    def raise_flag(self):
        self.registers["v"][15] = 1

    def sum_vx_and_vy(self):
        x_num, y_num = self.get_x_and_y()
        x_value, y_value = self.get_xvalue_and_yvalue(x_num, y_num)
        temp = x_value + y_value
        if temp > 255:
            self.raise_flag()
        else:
            self.registers['v'][15] = 0
        self.registers["v"][x_num] = temp % 256

    def subtract_vx_and_vy(self):
        x_num, y_num = self.get_x_and_y()
        x_value, y_value = self.get_xvalue_and_yvalue(x_num, y_num)
        if x_value > y_value:
            self.raise_flag()
            self.registers["v"][x_num] = x_value - y_value
        else:
            self.registers['v'][15] = 0
            self.registers["v"][x_num] = 256 + x_value - y_value

    def shift_right_vx(self):
        x_num, y_num = self.get_x_and_y()
        x_value, y_value = self.get_xvalue_and_yvalue(x_num, y_num)

        if self.shift_only_vx:
            bit_zero = self.registers['v'][x_num] & 0x1
            self.registers['v'][x_num] = x_value >> 1
            self.registers['v'][0xF] = bit_zero
        else:
            bit_zero = self.registers['v'][y_num] & 0x1
            self.registers['v'][x_num] = \
                self.registers['v'][y_num] = \
                y_value >> 1
            self.registers['v'][0xF] = bit_zero

    def subtract_vy_and_vx(self):
        x_num, y_num = self.get_x_and_y()
        x_value, y_value = self.get_xvalue_and_yvalue(x_num, y_num)
        if y_value > x_value:
            self.raise_flag()
            self.registers["v"][x_num] = y_value - x_value
        else:
            self.registers['v'][15] = 0
            self.registers["v"][x_num] = 256 + y_value - x_value

    def shift_left_vx(self):
        x_num, y_num = self.get_x_and_y()
        x_value, y_value = self.get_xvalue_and_yvalue(x_num, y_num)

        if self.shift_only_vx:
            bit_seven = (self.registers['v'][x_num] & 0x80) >> 8
            self.registers['v'][x_num] = x_value << 1
            self.registers['v'][0xF] = bit_seven
        else:
            bit_seven = (self.registers['v'][y_num] & 0x80) >> 8
            self.registers['v'][x_num] = \
                self.registers['v'][y_num] = \
                y_value << 1
            self.registers['v'][0xF] = bit_seven

    def skip_if_vx_not_equals_vy(self):
        x_num, y_num = self.get_x_and_y()
        if self.registers["v"][x_num] != self.registers["v"][y_num]:
            self.registers["pc"] += 2

    def put_value_to_index(self):
        self.registers["index"] = self.opcode & 0x0FFF

    def jump_to_address_plus_v0(self):
        self.set_pc_to_val(self.registers["v"][0] + (self.opcode & 0x0FFF))

    def put_rnd_to_vx(self):
        x_num, _ = self.get_x_and_y()
        self.registers["v"][x_num] = (self.opcode & 0x00FF) & randint(0, 255)

    def draw_sprite(self):
        x_num, y_num = self.get_x_and_y()
        x_coord = self.registers['v'][x_num]
        y_coord = self.registers['v'][y_num]
        n_bytes = self.opcode & 0x000F

        self.registers['v'][15] = 0

        self.draw(x_coord, y_coord, n_bytes)

    def draw(self, x, y, height):
        """
        Если при рисовании один спрайт накладывается на другой, в точке
        наложения цвет инвертируется, а регистр VF принимает значение 1. Иначе
        он принимает значение 0.
        :param x:
        :param y:
        :param height:
        :return:
        """
        I = self.registers['index']
        for y_line in range(height):
            pixel_byte = self.memory[I + y_line]
            b = bin(pixel_byte)
            pixel_byte = b[2:].zfill(8)
            y_coord = (y + y_line) % 32
            for x_idx in range(8):
                x_coord = (x + x_idx) % 64

                bit_at_idx = int(pixel_byte[x_idx])
                prev_bit_at_idx = self.screen[x_coord][y_coord]

                if bit_at_idx == prev_bit_at_idx == 1:
                    self.registers['v'][0xF] = self.registers['v'][0xF] | 1

                self.screen[x_coord][y_coord] ^= bit_at_idx

        self.draw_flag = True

    def skip_if_key(self):
        x_num, _ = self.get_x_and_y()
        operation = self.opcode & 0x00FF
        if operation == 0x9E:
            if self.keys[self.registers["v"][x_num]]:
                self.registers["pc"] += 2
        elif operation == 0xA1:
            if not self.keys[self.registers["v"][x_num]]:
                self.registers["pc"] += 2

    def execute_f_func(self):
        operation = self.opcode & 0x00FF
        try:
            self.f_operations_table[operation]()
        except KeyError:
            raise Exception(
                "Operation {} is not supported".format(hex(self.opcode)))

    def put_delay_to_vx(self):
        x_num, _ = self.get_x_and_y()
        self.registers["v"][x_num] = self.timers['delay']

    def put_key_to_vx(self):
        print("here")
        pressed_key = NOT_A_KEY
        for key in self.keys:
            if self.keys[key]:
                pressed_key = key
        if pressed_key == NOT_A_KEY:
            self.registers['pc'] -= 2
            return
        reg_value = (self.opcode & 0x0F00) >> 8
        self.registers['v'][reg_value] = pressed_key
        self.keys[pressed_key] = False

    def put_vx_to_delay(self):
        x_num, _ = self.get_x_and_y()
        self.timers['delay'] = self.registers["v"][x_num]

    def put_vx_to_sound(self):
        x_num, _ = self.get_x_and_y()
        self.timers['sound'] = self.registers["v"][x_num]

    def sum_idx_and_vx(self):
        x_num, _ = self.get_x_and_y()
        idx_value = self.registers["index"]
        self.registers["index"] = idx_value + self.registers["v"][x_num]

    def put_vx_sprite_to_idx(self):
        x_num, _ = self.get_x_and_y()
        self.registers["index"] = self.registers["v"][x_num] * 5

    def store_vx_in_bcd(self):
        x_num, _ = self.get_x_and_y()
        idx = self.registers['index']
        source = self.registers['v'][x_num]
        self.memory[idx] = int(source / 100)
        self.memory[idx + 1] = int((source / 10) % 10)
        self.memory[idx + 2] = int((source % 100) % 10)

    def put_v_reg_to_memory(self):
        x_num, _ = self.get_x_and_y()
        idx = self.registers["index"]
        for i in range(x_num + 1):
            self.memory[idx + i] = self.registers["v"][i] % 256

    def put_memory_to_v_reg(self):
        x_num, _ = self.get_x_and_y()
        idx = self.registers["index"]
        for i in range(x_num + 1):
            self.registers["v"][i] = self.memory[idx + i]
