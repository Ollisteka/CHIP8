from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton, QGridLayout, QLabel, \
    QLineEdit, QVBoxLayout

from config import PC, TIMERS, V, SP, INDEX, SOUND, DELAY


class DebugWidget(QtWidgets.QWidget):
    sig_execute = pyqtSignal()

    def __init__(self, game, parent=None):
        super().__init__(parent)
        super().setFont(QFont('Serif', 10, QFont.Light))
        self.game = game
        self.execute_button = QPushButton()
        self.execute_button.setText("EXECUTE")
        self.execute_button.released.connect(self.sig_execute.emit)

        reg_dump = self.game.get_reg_dump()

        current_opcode_label = QLabel()
        current_opcode_label.setText("Current opcode:")
        current_opcode_label.setFont(QFont('Serif', 10, QFont.Bold))

        self.current_opcode = QLineEdit()
        self.current_opcode.setText(reg_dump["current_opcode"])
        self.current_opcode.setReadOnly(True)
        self.current_opcode.setToolTip(self.game.get_opcode_docstring(
            self.game.opcode))

        v_reg_labels = self.get_v_reg_labels(reg_dump)
        other_regs = self.get_other_regs(reg_dump)

        _cur_code_layout = QGridLayout()
        _cur_code_layout.setSpacing(5)
        _cur_code_layout.addWidget(current_opcode_label, 0, 0)
        _cur_code_layout.addWidget(self.current_opcode, 0, 1)

        _reg_layout = QGridLayout()
        _reg_layout.setSpacing(3)
        self.v_line_edits = []
        for i in range(0, len(v_reg_labels)):
            label, line_edit = v_reg_labels[i]
            _reg_layout.addWidget(label, i, 2)
            _reg_layout.addWidget(line_edit, i, 3)
            self.v_line_edits.append(line_edit)

        self.other_line_edits = []
        for i in range(0, len(other_regs)):
            label, line_edit = other_regs[i]
            _reg_layout.addWidget(label, i, 0)
            _reg_layout.addWidget(line_edit, i, 1)
            self.other_line_edits.append(line_edit)

        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.addLayout(_cur_code_layout)
        layout.addLayout(_reg_layout)
        layout.addWidget(self.execute_button)
        self.setLayout(layout)

    def update_registers(self):
        reg_dump = self.game.get_reg_dump()
        self.current_opcode.setText(reg_dump["current_opcode"])
        self.current_opcode.setToolTip(
            self.game.get_opcode_docstring(self.game.opcode))

        for i in range(0, 15 + 1):
            self.v_line_edits[i].setText(reg_dump[V][i])

        for line_edit in self.other_line_edits:
            name = line_edit.accessibleName()
            if name == PC:
                line_edit.setText(reg_dump[PC])
            elif name == SP:
                line_edit.setText(reg_dump[SP])
            elif name == INDEX:
                line_edit.setText(reg_dump[INDEX])
            elif name == SOUND:
                line_edit.setText(reg_dump[TIMERS][SOUND])
            elif name == DELAY:
                line_edit.setText(reg_dump[TIMERS][DELAY])
            else:
                raise Exception("Unknown name. Should'n happen normally")

    def get_other_regs(self, reg_dump):
        return [self.make_labeled_line_edit("Program  counter: ", reg_dump[PC], PC),

                self.make_labeled_line_edit("Index register: ", reg_dump[INDEX], INDEX),

                self.make_labeled_line_edit("Stack pointer: ", reg_dump[SP], SP),

                self.make_labeled_line_edit("Sound timer: ", reg_dump[TIMERS][SOUND], SOUND),

                self.make_labeled_line_edit("Delay timer: ", reg_dump[TIMERS][DELAY], DELAY),
                ]

    def get_v_reg_labels(self, reg_dump, ):
        v_regs = reg_dump[V]
        return [(self.make_label("V" + str(i) + ": "), self.make_line_edit(v_regs[i])) for i in v_regs]

    def make_labeled_line_edit(self, description, text, name=""):
        return self.make_label(description), self.make_line_edit(text, name)

    def make_label(self, text):
        label = QLabel()
        label.setText(text)
        label.setAlignment(Qt.AlignRight)
        return label

    def make_line_edit(self, text, name=""):
        line_edit = QLineEdit()
        line_edit.setText(text)
        line_edit.setReadOnly(True)
        line_edit.setAccessibleName(name)
        return line_edit
