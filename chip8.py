from random import randint

from config import PC, V, SP, INDEX, SOUND, DELAY

__all__ = ['CHIP8']

FONTS = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
]

NOT_A_KEY = -999


class CHIP8:
    def __init__(self):
        self.opcode = 0
        self.__delay_sync = 0
        self.draw_flag = False
        self.running = True
        self.is_paused = False
        self.memory = bytearray(4096)
        self.__load_fonts()
        self.stack = [0] * 17
        self.registers = {
            PC: 512,  # 16 bit
            INDEX: 0,  # 16 bit
            SP: 0,  # 16 bit
            V: {key: 0 for key in range(16)}  # 8 bit
        }
        self.timers = {
            DELAY: 0,  # 8 bit
            SOUND: 0,  # 8 bit
        }
        self.screen = self.__init_screen()
        self.keys = {key: False for key in range(0, 16)}

        self.operation_table = {
            0x0: self.return_clear,
            0x1: self.jump_to_address,
            0x2: self.call_subroutine,
            0x3: self.skip_if_vx_equals_value,
            0x4: self.skip_if_vx_not_equals_value,
            0x5: self.skip_if_vx_equals_vy,
            0x6: self.put_value_to_vx,
            0x7: self.sum_value_and_vx,
            0x8: self.call_logical_operation,
            0x9: self.skip_if_vx_not_equals_vy,
            0xa: self.put_value_to_index,
            0xb: self.jump_to_address_plus_v0,
            0xc: self.put_rnd_to_vx,
            0xd: self.draw_sprite,
            0xe: self.skip_if_key,
            0xf: self.call_f_operations,
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
            0xE: self.shift_left_vx,
        }
        self.f_operations_table = {
            0x7: self.put_delay_to_vx,
            0xa: self.put_key_to_vx,
            0x15: self.put_vx_to_delay,
            0x18: self.put_vx_to_sound,
            0x1e: self.sum_idx_and_vx,
            0x29: self.put_vx_sprite_to_idx,
            0x33: self.store_vx_in_bcd,
            0x55: self.put_v_reg_to_memory,
            0x65: self.put_memory_to_v_reg,
        }

    def get_reg_dump(self):
        result = {}
        v_regs = {i: bin(self.registers["v"][i]) for i in range(16)}
        result["v"] = v_regs
        result["current_opcode"] = hex(self.opcode)
        for register in self.registers:
            if register == "v":
                continue
            result[register] = str(self.registers[register])
        result["timers"] = {key: str(val) for key, val in self.timers.items()}
        return result

    def get_memory_dump(self):
        return [hex(b) for b in self.memory]

    def get_x_and_y(self):
        """
        opcode: 0x0XY*
        Выделяет из опкода числа X и Y
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        y_num = (self.opcode & 0x00F0) >> 4
        return x_num, y_num

    def set_pc_to_val(self, value):
        """
        Устанавливает значение Programm Counter в value
        :param value: 16 битное значение
        :return:
        """
        if value < 0:
            raise Exception("You can't address negative memory!")
        if value > 4096:
            raise Exception("Out of memory!")
        self.registers[PC] = value & 0xFFFF

    @staticmethod
    def __init_screen():
        """
        Возвращает список списков размером 64*32, заполненный нулями
        :return:
        """
        screen = []
        for i in range(64):
            screen.append([0] * 32)
        return screen

    def __load_fonts(self):
        """
        Загружает шрифты в память
        :return:
        """
        for index, item in enumerate(FONTS):
            self.memory[index] = item

    def jump_to_address_plus_v0(self):
        """
        opcode: 0xbNNN
        Перейти по адресу NNN + V0
        :return:
        """
        self.set_pc_to_val(self.registers[V][0] + (self.opcode & 0x0FFF))

    def sum_value_and_vx(self):
        """
        opcode: 0x7XNN
        Загрузить в регистр VX сумму VX и NN
        :return:
        """
        number = self.opcode & 0x00FF
        reg_num = (self.opcode & 0x0F00) >> 8
        temp = self.registers[V][reg_num] + number
        self.registers[V][reg_num] = temp & 0x00FF

    def put_vy_to_vx(self):
        """
        opcode: 0x8XY0
        VX = VY
        :return:
        """
        x_num, y_num = self.get_x_and_y()
        self.registers[V][x_num] = self.registers[V][y_num]

    def vx_or_vy(self):
        """
        opcode: 0x8XY1
        VX = VX ИЛИ VY
        :return:
        """
        x_num, y_num = self.get_x_and_y()
        x_value = self.registers[V][x_num]
        y_value = self.registers[V][y_num]
        self.registers[V][x_num] = x_value | y_value

    def vx_and_vy(self):
        """
        opcode: 0x8XY2
        VX = VX И VY
        :return:
        """
        x_num, y_num = self.get_x_and_y()
        x_value = self.registers[V][x_num]
        y_value = self.registers[V][y_num]
        self.registers[V][x_num] = x_value & y_value

    def vx_xor_vy(self):
        """
        opcode: 0x8XY3
        VX = VX ИСКЛ.ИЛИ VY
        :return:
        """
        x_num, y_num = self.get_x_and_y()
        x_value = self.registers[V][x_num]
        y_value = self.registers[V][y_num]
        self.registers[V][x_num] = x_value ^ y_value

    def sum_vx_and_vy(self):
        """
        opcode: 0x8XY4
        VX = VX + VY, VF - флаг переноса
        :return:
        """
        x_num, y_num = self.get_x_and_y()
        x_value = self.registers[V][x_num]
        y_value = self.registers[V][y_num]
        temp = x_value + y_value
        if temp >= 256:
            self.registers[V][15] = 1
            self.registers[V][x_num] = temp & 0x00FF
        else:
            self.registers[V][15] = 0
            self.registers[V][x_num] = temp

    def subtract_vx_and_vy(self):
        """
        opcode: 0x8XY5
        VX = VX - VY, VF - флаг переноса
        :return:
        """
        x_num, y_num = self.get_x_and_y()
        x_value = self.registers[V][x_num]
        y_value = self.registers[V][y_num]
        if x_value >= y_value:
            self.registers[V][15] = 1
            self.registers[V][x_num] = x_value - y_value
        else:
            self.registers[V][15] = 0
            self.registers[V][x_num] = 256 + x_value - y_value

    def subtract_vy_and_vx(self):
        """
        opcode: 0x8XY7
        VX = VY - VX, VF - флаг переноса
        :return:
        """
        x_num, y_num = self.get_x_and_y()
        x_value = self.registers[V][x_num]
        y_value = self.registers[V][y_num]
        if y_value >= x_value:
            self.registers[V][15] = 1
            self.registers[V][x_num] = y_value - x_value
        else:
            self.registers[V][15] = 0
            self.registers[V][x_num] = 256 + y_value - x_value

    def shift_right_vx(self):
        """
        opcode: 0x8XY6
        VX = VX >> 1, VF - флаг переноса
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        x_value = self.registers[V][x_num]
        if x_value & 1 == 1:
            self.registers[V][15] = 1
        else:
            self.registers[V][15] = 0
        self.registers[V][x_num] = x_value >> 1

    def shift_left_vx(self):
        """
        opcode: 0x8XYe
        VX = VX << 1, VF - флаг переноса
        :return:
        """
        x_num = (self.opcode & 0x0F00) >> 8
        x_value = self.registers[V][x_num]
        if (bin(x_value))[2:].zfill(8)[0] == '1':
            self.registers[V][15] = 1
        else:
            self.registers[V][15] = 0
        self.registers[V][x_num] = (x_value << 1) & 0x00FF

    def put_v_reg_to_memory(self):
        """
        opcode: 0xfX55
        Сохранить значения регистров от V0 до VX включительно в память,
        начиная с места, на которое указывает I
        :return:
        """
        x_num, _ = self.get_x_and_y()
        idx = self.registers[INDEX]
        for i in range(x_num + 1):
            self.memory[idx + i] = self.registers[V][i]

    def put_memory_to_v_reg(self):
        """
        opcode: 0xfX65
        Загрузить в регистры от V0 до VX (ключительно) значения из памяти,
        начиная с адреса в I
        :return:
        """
        x_num, _ = self.get_x_and_y()
        idx = self.registers[INDEX]
        for i in range(x_num + 1):
            self.registers[V][i] = self.memory[idx + i]

    def put_key_to_vx(self):
        """
        opcode: 0xfX0a
        Подождать, пока не будет нажата клавиша, затем её значение положить
        в VX.
        :return:
        """
        pressed_key = NOT_A_KEY
        for key in self.keys:
            if self.keys[key]:
                pressed_key = key
        if pressed_key == NOT_A_KEY:
            self.set_pc_to_val(self.registers[PC] - 2)
            return
        x_num, _ = self.get_x_and_y()
        self.registers[V][x_num] = pressed_key
        self.keys[pressed_key] = False

    def sum_idx_and_vx(self):
        """
        opcode: 0xfX1e
        Сложить значение, лежащее в индексе, со значением в регистре VX
        :return:
        """
        x_num, _ = self.get_x_and_y()
        idx = self.registers[INDEX]
        self.registers[INDEX] = (self.registers[V][x_num] + idx) & 0xFFFF

    def jump_to_address(self):
        """
        opcode 0x1NNN
        Program Counter устанавливается в NNN
        :return:
        """
        self.set_pc_to_val(self.opcode & 0x0FFF)

    def put_rnd_to_vx(self):
        """
        opcode: 0xcXKK
        Устанавливает в регистр VX случайный байт И KK.
        (И логическое)
        :return:
        """
        x_num, _ = self.get_x_and_y()
        value = self.opcode & 0x00FF
        self.registers[V][x_num] = value & randint(0, 255)

    def skip_if_vx_not_equals_value(self):
        """
        opcode: 0x4XNN
        Пропустить следующую инструкцию, если VX != NN
        :return:
        """
        x_num, _ = self.get_x_and_y()
        value = (self.opcode & 0x00FF)
        if self.registers[V][x_num] != value:
            self.set_pc_to_val(self.registers[PC] + 2)

    def skip_if_vx_equals_value(self):
        """
        opcode: 0x3XNN
        Пропустить следующую инструкцию, если VX = NN
        :return:
        """
        x_num, _ = self.get_x_and_y()
        value = (self.opcode & 0x00FF)
        if self.registers[V][x_num] == value:
            self.set_pc_to_val(self.registers[PC] + 2)

    def skip_if_vx_equals_vy(self):
        """
        opcode: 0x5XY0
        Пропустить следующую инструкцию, если VX == VY
        :return:
        """
        x_num, y_num = self.get_x_and_y()
        x_value = self.registers[V][x_num]
        y_value = self.registers[V][y_num]
        if x_value == y_value:
            self.set_pc_to_val(self.registers[PC] + 2)

    def skip_if_vx_not_equals_vy(self):
        """
        opcode: 0x9XY0
        Пропустить следующую инструкцию, если VX != VY
        :return:
        """
        x_num, y_num = self.get_x_and_y()
        x_value = self.registers[V][x_num]
        y_value = self.registers[V][y_num]
        if x_value != y_value:
            self.set_pc_to_val(self.registers[PC] + 2)

    def put_delay_to_vx(self):
        """
        opcode: 0xfX07
        Регистру VX присваивается значение таймера задержки
        :return:
        """
        x_num, _ = self.get_x_and_y()
        self.registers[V][x_num] = self.timers[DELAY]

    def put_vx_to_delay(self):
        """
        opcode: 0xfX15
        Установить значение таймера задержки равным значению регистра VX
        :return:
        """
        x_num, _ = self.get_x_and_y()
        self.timers[DELAY] = self.registers[V][x_num]

    def put_vx_to_sound(self):
        """
        opcode: 0xfX18
        Установить значение звукового таймера равным значению регистра VX
        :return:
        """
        x_num, _ = self.get_x_and_y()
        self.timers[SOUND] = self.registers[V][x_num]

    def call_logical_operation(self):
        """
        ###
        Переключается между командами, начинающимися с 8
        :return:
        """
        operation = self.opcode & 0x000F
        try:
            self.logical_operations_table[operation]()
        except KeyError as err:
            raise Exception(
                "Operation {} is not supported".format(hex(self.opcode)))

    def return_clear(self):
        """
        opcode: 0x00E0 - очистить экран.
        opcode: 0x00EE - выйти из подзадачи
        :return:
        """
        operation = self.opcode & 0x0FFF

        if operation == 0x00E0:
            self.clear_screen()
        elif operation == 0x00EE:
            self.return_from_subroutine()
        else:
            """
            0x0NNN
            Перейти к машинному коду в NNN.
            
            Использовалось только в самый первых интерпретаторах, во всех 
            современных просто игнорируется.
            """
            return

    def put_vx_sprite_to_idx(self):
        """
        opcode: 0xfX29
        Команда загружает в регистр I адрес спрайта, значение которого
        находится в VX. Длина спрайта - 5 байт
        :return:
        """
        x_num, _ = self.get_x_and_y()
        self.registers[INDEX] = self.registers[V][x_num] * 5

    def store_vx_in_bcd(self):
        """
        opcode: 0xfX33
        Сохранить разряды значения регистра VX по адресам I, I+1 и I+2
        (в двоично десятичном виде)
            сотни       -> self.memory[index]
            десятки     -> self.memory[index + 1]
            единицы     -> self.memory[index + 2]
        :return:
        """
        x_num, _ = self.get_x_and_y()
        source = self.registers[V][x_num]
        idx = self.registers[INDEX]
        self.memory[idx] = source // 100
        self.memory[idx + 1] = ((source // 10) % 10)
        self.memory[idx + 2] = ((source % 100) % 10)

    def call_f_operations(self):
        """
        ###
        Вызывает нужную команду для опкода вида 0xfNN
        :return:
        """
        operation = self.opcode & 0x00FF
        try:
            self.f_operations_table[operation]()
        except KeyError:
            raise Exception(
                "Operation {} is not supported".format(hex(self.opcode)))

    def skip_if_key_pressed(self):
        """
        opcode: 0xeX9E
        Пропустить следующую инструкцию, если нажата клавиша с кодом,
        лежащим в регистре VX
        :return:
        """
        x_num, _ = self.get_x_and_y()
        if self.keys[self.registers[V][x_num]]:
            self.set_pc_to_val(self.registers[PC] + 2)

    def skip_if_key_not_pressed(self):
        """
        opcode: 0xeXa1
        Пропустить следующую инструкцию, если клавиша с кодом,
        лежащим в регистре VX НЕ нажата
        :return:
        """
        x_num, _ = self.get_x_and_y()
        if not self.keys[self.registers[V][x_num]]:
            self.set_pc_to_val(self.registers[PC] + 2)

    def skip_if_key(self):
        """
        opcode: 0xeX__
        :return:
        """
        operation = self.opcode & 0x00FF
        if operation == 0x9e:
            self.skip_if_key_pressed()
        elif operation == 0xa1:
            self.skip_if_key_not_pressed()
        else:
            raise Exception(
                "Operation {} is not supported".format(hex(self.opcode)))

    def call_subroutine(self):
        """
        opcode: 0x2NNN
        Вызвать подпрограмму
        Увеличить stack pointer, положить текущий PC на вершину стека,
        РС присвоить значение NNN
        :return:
        """
        if self.registers[SP] >= 16:
            raise Exception("Stack Overflow!")
        self.registers[SP] += 1
        self.stack[self.registers[SP]] = self.registers[PC]
        self.set_pc_to_val(self.opcode & 0x0FFF)

    def return_from_subroutine(self):
        """
        opcode: 0x00EE
        Возврат из подпрограммы.
        Устанавливает в program counter адрес с вершины стека,
        затем вычитает 1 из stack pointer
        :return:
        """
        self.set_pc_to_val(self.stack[self.registers[SP]])
        self.registers[SP] -= 1

    def draw_sprite(self):
        """
        opcode: 0xdXYN
        Нарисовать на экране спрайт. Эта инструкция считывает N байт начиная с
        адреса из регистра I и рисует их на экране в виде спрайта с
        координатами VX, VY
        :return:
        """
        x_coord = self.registers[V][(self.opcode & 0x0F00) >> 8]
        y_coord = self.registers[V][(self.opcode & 0x00F0) >> 4]
        n_bytes = self.opcode & 0x000F

        self.registers[V][15] = 0

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
        I = self.registers[INDEX]
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
                    self.registers[V][15] = 1

                self.screen[x_coord][y_coord] ^= bit_at_idx

        self.draw_flag = True

    def clear_screen(self):
        """
        opcode: 0x00E0
        Функция "очищает" экран, устанавливая каждый пиксель в ноль
        :return:
        """
        for y in range(32):
            for x in range(64):
                self.screen[x][y] = 0

    def put_value_to_index(self):
        """
        opcode: 0xaNNN
        Загрузить в регистр index (I) значение NNN
        :return:
        """
        self.registers[INDEX] = self.opcode & 0x0FFF

    def put_value_to_vx(self):
        """
        opcode: 0x6XNN
        Загрузить в регистр VX число NN
        :return:
        """
        idx = (self.opcode & 0x0F00) >> 8
        self.registers[V][idx] = self.opcode & 0x00FF

    def emulate_cycle(self, opcode=None):
        """
        Имитация одного цикла машины:
           1) Выборка команд
           2) Выполнение команды
           3) Увеличение счётчика команд
        :param opcode:
        :return:
        """
        if self.is_paused:
            return

        pc = self.registers[PC]
        if not opcode:
            self.opcode = (self.memory[pc] << 8) | self.memory[pc + 1]
        else:
            self.opcode = opcode

        operation = (self.opcode & 0xF000) >> 12
        self.set_pc_to_val(self.registers[PC] + 2)
        try:
            self.operation_table[operation]()
        except KeyError:
            raise Exception(
                "Operation {} is not supported".format(hex(self.opcode)))

    def get_opcode_docstring(self, opcode):
        operation = (opcode & 0xF000) >> 12
        possible_func = self.operation_table[operation]
        doc = possible_func.__doc__
        if "###" in doc:
            try:
                operation = self.opcode & 0x00FF
                return self.f_operations_table[operation].__doc__.replace(":return:", "").strip('\n')
            except KeyError:
                try:
                    operation = self.opcode & 0x000F
                    return self.logical_operations_table[operation].__doc__
                except KeyError:
                    return doc.replace(":return:", "").strip('\n')
        return doc.replace(":return:", "").strip('\n')

    def decrement_sound_timer(self):
        if self.timers[SOUND] > 0:
            self.timers[SOUND] -= 1

    def decrement_delay_timer(self):
        if self.timers[DELAY] > 0:
            self.timers[DELAY] -= 1

    def load_rom(self, rom):
        """
        Загрузить данные ROM файла в память
        :param rom:
        :return:
        """
        with open(rom, "rb") as file:
            data = file.read()
        for index, value in enumerate(data):
            self.memory[index + 0x200] = value
