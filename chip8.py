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
            'sp': 0,
            'pc': 0x200,
        }
        self.timers = {
            'delay': 0,
            'sound': 0,
        }
        self.opcode = 0
        self.draw_flag = False

        self.operation_table = {
            0x0: self.return_clear,
            0x2: self.call_subroutine,
            0x3: self.skip_if,
            0x6: self.load_num_to_reg,  # Загрузить в регистр VX число NN
            0x7: self.load_sum_to_reg,  # Загрузить в регистр VX сумму VX и NN
            0xa: self.set_val_to_index,  # Значение регистра I
                                         # устанавливается в NNN
            0xd: self.draw_sprite,
            0xf: self.f_functions,
        }
        self.f_functions = {
            0x7: self.put_delay_timer_to_reg,
            0x15: self.set_delay_timer,
            0x33: self.save_vx_to_index,
            0x65: self.save_memory_to_vx,
            0x29: self.set_idx_to_location,
        }

    def skip_if(self):
        """
        opcode: 0x3XNN
        Пропустить следующую инструкцию, если VX = NN
        :return:
        """
        reg_num = (self.opcode & 0x0F00) >> 8
        value = self.opcode & 0x00FF
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

    def f_functions(self):
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
        Нарисовать на экране спрайт. Эта инструкция считывает N байт по адресу
        в регистре I и рисует их на экране в виде спрайта с координатами VX, VY
        :return:
        """
        x_coord = self.registers['v'][(self.opcode & 0x0F00) >> 8]
        y_coord = self.registers['v'][(self.opcode & 0x00F0) >> 4]
        n_bytes = self.opcode & 0x000F

        self.draw(x_coord, y_coord, n_bytes)

    # TODO
    def draw(self, x, y, n_bytes):
        pass

    # TODO
    def clear_screen(self):
        pass

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

    def emulate_cycle(self):
        pc = self.registers['pc']
        self.opcode = (self.memory[pc] << 8) | self.memory[pc + 1]
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
        for index, value in enumerate(data):
            self.memory[index + 0x200] = value
