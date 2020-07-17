from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout, QSlider
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal


class ThresholdSelector(QGroupBox):
    thresholdChanged = pyqtSignal(float)

    def __init__(self):
        super(ThresholdSelector, self).__init__('Threshold selector')
        self.init_UI()
        self.slider.valueChanged.connect(self.threshold_changed)

    def init_UI(self):
        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(40)
        self.label = QLabel()
        vbox = QVBoxLayout()
        vbox.addWidget(self.slider)
        vbox.addWidget(self.label)
        self.setLayout(vbox)

        self.refresh_UI()

    def refresh_UI(self):
        self.label.setNum(self.get_current_threshold())

    def get_current_threshold(self):
        return self.slider.value() / 100

    def threshold_changed(self, new_value):
        self.refresh_UI()
        self.thresholdChanged.emit(new_value / 100)
