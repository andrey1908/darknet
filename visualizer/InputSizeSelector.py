from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout, QSlider
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from time import time


class InputSizeSelector(QGroupBox):
    inputSizeChanged = pyqtSignal(tuple)

    def __init__(self, base_width, base_height, show_delay=False):
        super(InputSizeSelector, self).__init__('Input size selector')
        self.base_width = base_width
        self.base_height = base_height
        self.show_delay = show_delay
        self.scale = None
        self.init_UI()
        self.slider.valueChanged.connect(self.input_size_changed)

    def init_UI(self):
        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)
        self.scale = 1.
        self.label = QLabel()
        vbox = QVBoxLayout()
        vbox.addWidget(self.slider)
        vbox.addWidget(self.label)
        if self.show_delay:
            self.delay_label = QLabel()
            self.delay_label.setText('- ms')
            vbox.addWidget(self.delay_label)
        self.setLayout(vbox)

        self.refresh_UI()

    def refresh_UI(self):
        w, h = self.get_current_input_size()
        self.label.setText('{} x {} (x{:.2f})'.format(w, h, self.scale))

    def my_round(self, a):
        i = int(a)
        if a - i < 0.5:
            return i
        else:
            return i + 1

    def get_current_input_size(self):
        w, h = self.base_width * self.scale, self.base_height * self.scale
        w = max(self.my_round(w / 32) * 32, 32)
        h = max(self.my_round(h / 32) * 32, 32)
        return w, h

    def input_size_changed(self, new_value):
        if self.show_delay:
            start_time = time()
        if new_value >= 50:
            self.scale = (new_value - 50) / 50 + 1
        else:
            self.scale = new_value / 100 + 0.5
        self.refresh_UI()
        self.inputSizeChanged.emit(self.get_current_input_size())
        if self.show_delay:
            time_passed = (time() - start_time) * 1000
            self.delay_label.setText('{:.1f} ms'.format(time_passed))
