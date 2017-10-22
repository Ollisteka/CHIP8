from random import randint

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
        # первые 512 (0x200) заняты оригинальным интерпретатором
        self.memory = bytearray(4096)
        self.stack = []
        # 16 x 8-bit general purpose registers (V0 - VF**)
        # 1 x 16-bit index register (I)
        # 1 x 16-bit stack pointer (SP)
        # 1 x 16-bit program counter (PC)
        # 1 x 8-bit delay timer (DT)
        # 1 x 8-bit sound timer (ST)
        self.registers = {
            'v': [0] * 16,
            'index': 0,
            'sp': 82,
            'pc': 512,
        }
        self.timers = {
            'delay': 0,
            'sound': 0,
        }
        self.opcode = 0
        self.draw_flag = False
        self.waiting_for_key = False

        self.operation_table = {
            0x0: self.return_clear,
            0x1: self.goto,
            0x2: self.call_subroutine,
            0x3: self.skip_if_equal,
            0x4: self.skip_if_not_equal,
            0x6: self.load_num_to_reg,  # Загрузить в регистр VX число NN
            0x7: self.load_sum_to_reg,  # Загрузить в регистр VX сумму VX и NN
            0x8: self.call_logical_operation,
            0xa: self.set_val_to_index,  # Значение регистра I
                                         # устанавливается в NNN
            0xc: self.set_rnd_to_vx,
            0xd: self.draw_sprite,
            0xf: self.call_f_functions,
        }
        self.logocal_operations = {
            0x0: self.load_vy_to_vx,
            0x1: self.vx_or_vy,
            0x2: self.vx_and_vy,
            0x3: self.vx_xor_vy,
            0x4: self.sum_vx_and_vy,
            0x5: self.substract_vx_and_vy,
            0x6: self.shift_right_vx,
            0x7: self.substract_vy_and_vx,
            0xE: self.shift_left_vx,
        }
        self.f_functions = {
            0x7: self.put_delay_timer_to_reg,
            0xa: self.wait_for_key_press,
            0x15: self.set_delay_timer,
            0x1e: self.sum_idx_and_vx,
            0x33: self.save_vx_to_index,
            0x55: self.save_vx_to_memory,
            0x65: self.save_memory_to_vx,
            0x29: self.set_idx_to_location,
        }
        self.screen = []
        self.key_pressed = None
        self.__init_screen()  # [[0]*32]*64
        self.__load_fonts()

    def __init_screen(self):
        for i in range(64):
            self.screen.append([0]*32)

    def __load_fonts(self):
        """
        Загружает шрифты в память
        :return:
        """
        for i in range(80):
            self.memory[i] = FONTS[i]

    def load_vy_to_vx(self):
        """
        opcode: 0x8XY0
        VX = VY
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        y_num = (self.opcode & 0x00F0) >> 4
        self.registers['v'][x_num] = self.registers['v'][y_num]

    def vx_or_vy(self):
        """
        opcode: 0x8XY1
        VX = VX ИЛИ VY
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        y_num = (self.opcode & 0x00F0) >> 4
        x_value = self.registers['v'][x_num]
        y_value = self.registers['v'][y_num]
        self.registers['v'][x_num] = x_value | y_value

    def vx_and_vy(self):
        """
        opcode: 0x8XY2
        VX = VX И VY
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        y_num = (self.opcode & 0x00F0) >> 4
        x_value = self.registers['v'][x_num]
        y_value = self.registers['v'][y_num]
        self.registers['v'][x_num] = x_value & y_value

    def vx_xor_vy(self):
        """
        opcode: 0x8XY3
        VX = VX ИСКЛ.ИЛИ VY
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        y_num = (self.opcode & 0x00F0) >> 4
        x_value = self.registers['v'][x_num]
        y_value = self.registers['v'][y_num]
        self.registers['v'][x_num] = x_value ^ y_value

    def sum_vx_and_vy(self):
        """
        opcode: 0x8XY4
        VX = VX + VY, VF - флаг переноса
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        y_num = (self.opcode & 0x00F0) >> 4
        x_value = self.registers['v'][x_num]
        y_value = self.registers['v'][y_num]
        temp = x_value + y_value
        if temp >= 256:
            self.registers['v'][15] = 1
            self.registers['v'][x_num] = temp - 256
        else:
            self.registers['v'][15] = 0
            self.registers['v'][x_num] = temp - 256

    def substract_vx_and_vy(self):
        """
        opcode: 0x8XY5
        VX = VX - VY, VF - флаг переноса
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        y_num = (self.opcode & 0x00F0) >> 4
        x_value = self.registers['v'][x_num]
        y_value = self.registers['v'][y_num]
        if x_value > y_value:
            self.registers['v'][15] = 1
            self.registers['v'][x_num] = x_value - y_value
        else:
            self.registers['v'][15] = 0
            self.registers['v'][x_num] = 256 + x_value - y_value

    def substract_vy_and_vx(self):
        """
        opcode: 0x8XY7
        VX = VY - VX, VF - флаг переноса
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        y_num = (self.opcode & 0x00F0) >> 4
        x_value = self.registers['v'][x_num]
        y_value = self.registers['v'][y_num]
        if y_value > x_value:
            self.registers['v'][15] = 1
            self.registers['v'][x_num] = y_value - x_value
        else:
            self.registers['v'][15] = 0
            self.registers['v'][x_num] = 256 + y_value - x_value

    def shift_right_vx(self):
        """
        opcode: 0x8XY6
        VX = VX >> 1, VF - флаг переноса
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        x_value = self.registers['v'][x_num]
        if x_value & 1 == 1:
            self.registers['v'][15] = 1
        else:
            self.registers['v'][15] = 0
        self.registers['v'][x_num] = x_value >> 1

    def shift_left_vx(self):
        """
        opcode: 0x8XYe
        VX = VX >> 1, VF - флаг переноса
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        x_value = self.registers['v'][x_num]
        if x_value & 128 == 1:
            self.registers['v'][15] = 1
        else:
            self.registers['v'][15] = 0
        self.registers['v'][x_num] = (x_value << 1) & 127

    def save_vx_to_memory(self):
        """
        opcode: 0xfX55
        Сохранить значения регистров от V0 до VX включительно в память,
        начиная с места, на которое указывает I
        :return:
        """
        for i in range((self.opcode & 0x0F00) >> 8):
            self.memory[self.registers['index'] + i] = self.registers['v'][i]

    def wait_for_key_press(self):
        """
        opcode: 0xfX0a
        Подождать, пока не будет нажата клавиша, зачем е значение положить в VX.
        :return:
        """
        if not self.key_pressed:
            self.waiting_for_key = True
            self.registers['pc'] -= 2
            return
        reg_value = (self.opcode & 0x0F00) >> 8
        self.registers['v'][reg_value] = self.key_pressed
        self.key_pressed = None
        self.waiting_for_key = False

    def sum_idx_and_vx(self):
        """
        opcode: 0xfX1e
        :return:
        """
        value = (self.opcode & 0x0F00) >> 8
        idx_value = self.registers['index']
        temp = value + idx_value
        self.registers['index'] = temp % 32768

    def goto(self):
        """
        opcode 0x1NNN
        Program Counter устанавливается в NNN
        :return:
        """
        self.registers['pc'] = self.opcode & 0x0FFF

    def set_rnd_to_vx(self):
        """
        opcode: 0xcXKK
        Устанавливает в регистр VX случайный байт И KK.
        (И логическое)
        :return:
        """
        rnd = randint(0, 255)
        reg_num = (self.opcode & 0x0F00) >> 8
        value = self.opcode & 0x00FF
        self.registers['v'][reg_num] = value & rnd

    def skip_if_not_equal(self):
        """
        opcode: 0x4XNN
        Пропустить следующую инструкцию, если VX != NN
        :return:
        """
        reg_num = (self.opcode & 0x0F00) >> 8
        value = (self.opcode & 0x00FF)
        if self.registers['v'][reg_num] != value:
            self.registers['pc'] += 2

    def skip_if_equal(self):
        """
        opcode: 0x3XNN
        Пропустить следующую инструкцию, если VX = NN
        :return:
        """
        reg_num = (self.opcode & 0x0F00) >> 8
        value = (self.opcode & 0x00FF)
        if self.registers['v'][reg_num] == value:
            self.registers['pc'] += 2

    def put_delay_timer_to_reg(self):
        """
        opcode: 0xfX07
        Регистру VX присваивается значение таймера задержки
        :return:
        """
        self.registers['v'][(self.opcode & 0x0F00) >> 8] = self.timers['delay']

    def set_delay_timer(self):
        """
        opcode: 0xfX15
        Установить значение таймера задержки равным значению регистра VX
        :return:
        """
        self.timers['delay'] = (self.opcode & 0x0F00) >> 8

    def call_logical_operation(self):
        """
        Переключается между командами, начинающимися с 8
        :return:
        """
        operation = self.opcode & 0x000F
        try:
            self.logocal_operations[operation]()
        except KeyError as err:
            raise err


    def return_clear(self):
        """
        Переключается между кодами, начинающимися с нуля
        :return:
        """
        operation = self.opcode & 0x0FFF

        if operation == 0x00E0:
            self.clear_screen()
        elif operation == 0x00EE:
            self.return_from_subroutine()
        else:
            raise Exception("Operation {0} is not supported".format(
                  self.opcode))

    def load_sum_to_reg(self):
        """
        opcode: 0x7XNN
        Загрузить в регистр VX сумму VX и NN
        :return:
        """
        number = self.opcode & 0x00FF
        reg_num = (self.opcode & 0x0F00) >> 8
        temp = self.registers['v'][reg_num] + number
        self.registers['v'][reg_num] = temp % 256

    def set_idx_to_location(self):
        """
        opcode: 0xfX29
        Команда загружает в регистр I адрес спрайта, значение которого
        находится в VX
        Sets I to the location of the sprite for the character in VX.
        Characters 0-F (in hexadecimal) are represented by a 4x5 font.
        :return:
        """
        number = (self.opcode & 0x0F00) >> 8
        self.registers['index'] = self.registers['v'][number]

    def save_memory_to_vx(self):
        """
        opcode: 0xfX65
        Загрузить значения регистров от V0 до VX (ключительно) из памяти,
        начиная с адреса в I
        :return:
        """
        for i in range(((self.opcode & 0x0F00) >> 8) + 2):
            self.registers['v'][i] = self.memory[self.registers['index'] + i]

    def save_vx_to_index(self):
        """
        opcode: 0xfX33
        Сохранить разряды значения регистра VX по адресам I, I+1 и I+2
        (в двоично десятичном виде)
            сотни       -> self.memory[index]
            десятки     -> self.memory[index + 1]
            единицы     -> self.memory[index + 2]
        :return:
        """
        source = self.registers['v'][(self.opcode & 0x0F00) >> 8]
        self.memory[self.registers['index']] = int(source/100)
        self.memory[self.registers['index'] + 1] = int((source/10) % 10)
        self.memory[self.registers['index'] + 2] = int((source % 100) % 10)

    def call_f_functions(self):
        """
        Вызывает нужную команду для опкода вида 0xfNN
        :return:
        """
        operation = self.opcode & 0x00FF
        deb = hex(operation)
        try:
            self.f_functions[operation]()
        except KeyError as err:
            raise err

    def call_subroutine(self):
        """
        opcode: 0x2NNN
        Вызвать подпрограмму
        Увеличить stack pointer, положить текущий PC на вершину стека,
        РС присвоить значение NNN
        :return:
        """
        self.registers['sp'] += 1
        self.stack.append(self.registers['pc'])
        self.registers['pc'] = self.opcode & 0x0FFF

    def return_from_subroutine(self):
        """
        opcode: 0x00EE
        Возврат из подпрограммы.
        Устанавливает в program counter адрес с вершины стека,
        затем вычитает 1 из stack pointer
        :return:
        """
        self.registers['pc'] = self.stack.pop()
        self.registers['sp'] -= 1

    def draw_sprite(self):
        """
        opcode: 0xdXYN
        Нарисовать на экране спрайт. Эта инструкция считывает N байт начиная с
        адреса из регистра I и рисует их на экране в виде спрайта с
        координатами VX, VY
        :return:
        """
        x_coord = self.registers['v'][(self.opcode & 0x0F00) >> 8]
        y_coord = self.registers['v'][(self.opcode & 0x00F0) >> 4]
        n_bytes = self.opcode & 0x000F

        self.registers['v'][15] = 0

        self.draw(x_coord, y_coord, n_bytes)

    def draw(self, x, y, height):
        """
        Draws a sprite at coordinate (VX, VY) that has a width of 8 pixels and
        a height of N pixels. Each row of 8 pixels is read as bit-coded
        starting from memory location I; I value doesn’t change after the
        execution of this instruction. As described above, VF is set to 1 if
        any screen pixels are flipped from set to unset when the sprite is
        drawn, and to 0 if that doesn’t happen.
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
            c = b[2:].zfill(8)
            pixel_byte = c
            y_coord = (y + y_line) % 32
            for x_idx in range(8):
                x_coord = (x + x_idx) % 64

                bit_at_idx = int(pixel_byte[x_idx])
                prev_bit_at_idx = self.screen[x_coord][y_coord]

                if bit_at_idx == prev_bit_at_idx == 1:
                    self.registers['v'][15] = 1
                    self.screen[x_coord][y_coord] = 0
                elif bit_at_idx == prev_bit_at_idx == 0:
                    self.screen[x_coord][y_coord] = 0
                else:
                    self.screen[x_coord][y_coord] = bit_at_idx ^ prev_bit_at_idx

        self.draw_flag = True

    def clear_screen(self):
        self.screen = []
        self.__init_screen()

    def set_val_to_index(self):
        """
        opcode: 0xaNNN
        Загрузить в регистр index (I) значение NNN
        :return:
        """
        self.registers['index'] = self.opcode & 0x0FFF

    def load_num_to_reg(self):
        """
        opcode: 0x6XNN
        Загрузить в регистр VX число NN
        :return:
        """
        idx = (self.opcode & 0x0F00) >> 8  # убираю лишние нули справа
        self.registers['v'][idx] = self.opcode & 0x00FF

    def emulate_cycle(self, opcode=None):
        pc = self.registers['pc']
        if not opcode:
            self.opcode = (self.memory[pc] << 8) | self.memory[pc + 1]
        else:
            self.opcode = opcode
        self.registers['pc'] += 2
        operation = (self.opcode & 0xF000) >> 12
        deb = hex(operation)
        debb = hex(self.opcode)
        try:
            self.operation_table[operation]()
        except KeyError as err:
            raise err
        a = 0

    def load_rom(self, rom):
        with open(rom, "rb") as file:
            data = file.read()
        i = 0
        for val in data:
            a = hex(val)
            self.memory[i + 0x200] = val
            i += 1
        # for index, value in enumerate(data):
        #     self.memory[index + 0x200] = value
