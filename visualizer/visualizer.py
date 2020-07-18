from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from ImageSelector import ImageSelector
from ThresholdSelector import ThresholdSelector
from InputSizeSelector import InputSizeSelector
from ImageScaleSelector import ImageScaleSelector
from Viewer import Viewer
from Detector import Detector
import os


class Visualizer(QWidget):
    def __init__(self, config_file, model_file, classes_file, images_folder, window_width, window_height,
                 input_base_width, input_base_height):
        super(Visualizer, self).__init__()
        self.image_selector = ImageSelector(images_folder, show_delay=True)
        self.threshold_selector = ThresholdSelector(show_delay=True)
        self.input_size_selector = InputSizeSelector(input_base_width, input_base_height, show_delay=True)
        self.image_scale_selector = ImageScaleSelector(show_delay=True)
        self.viewer = Viewer(window_width, window_height)
        self.detector = Detector(config_file, model_file, classes_file, self.image_selector.get_current_image_file(),
                                 self.threshold_selector.get_current_threshold(),
                                 self.input_size_selector.get_current_input_size(),
                                 self.image_scale_selector.get_current_image_scale())
        self.image_selector.imageChanged.connect(self.detector.new_image)
        self.threshold_selector.thresholdChanged.connect(self.detector.new_threshold)
        self.input_size_selector.inputSizeChanged.connect(self.detector.new_input_size)
        self.image_scale_selector.imageScaleChanged.connect(self.detector.new_image_scale)
        self.detector.detectionsDrawn.connect(self.viewer.set_pixmap)
        self.init_UI()
        self.detector.detect()
        self.detector.draw()

    def init_UI(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_selector)
        vbox.addWidget(self.viewer)
        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.threshold_selector)
        hbox.addWidget(self.input_size_selector)
        hbox.addWidget(self.image_scale_selector)
        self.setLayout(hbox)


os.environ["CUDA_VISIBLE_DEVICES"] = str("0")
app = QApplication([])
root_folder = '/home/k_andrei/new_darknet/darknet/auto_labeled/vehicle+pedestrian+traffic_light+traffic_sign/yolov3-mod/'
images_folder = '/home/k_andrei/new_darknet/darknet/auto_labeled/vehicle+pedestrian+traffic_light+traffic_sign/' \
                'test_yandex_disk/Taganrog_15'
vis = Visualizer(root_folder + 'config/yolov3-mod.cfg', root_folder + 'epoch_40.weights',
                 root_folder + 'config/classes.names', images_folder, 900, 500, 1024, 576)
vis.show()
app.exec_()
