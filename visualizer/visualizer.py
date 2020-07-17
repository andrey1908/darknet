from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from ImageSelector import ImageSelector
from Viewer import Viewer
from Detector import Detector
from ThresholdSelector import ThresholdSelector
import os


class Visualizer(QWidget):
    def __init__(self, config_file, model_file, classes_file, images_folder, window_width, window_height):
        super(Visualizer, self).__init__()
        self.image_selector = ImageSelector(images_folder)
        self.threshold_selector = ThresholdSelector()
        self.viewer = Viewer(window_width, window_height)
        self.detector = Detector(config_file, model_file, classes_file)
        self.image_selector.imageChanged.connect(self.detector.new_image)
        self.threshold_selector.thresholdChanged.connect(self.detector.new_threshold)
        self.detector.detectionsDrawn.connect(self.viewer.set_pixmap)
        self.init_UI()
        self.init_detector()

    def init_UI(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_selector)
        vbox.addWidget(self.viewer)
        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.threshold_selector)
        self.setLayout(hbox)

    def init_detector(self):
        self.detector.image_file = self.image_selector.get_current_image_file()
        self.detector.image_pixmap = QPixmap(self.detector.image_file)
        self.detector.threshold = self.threshold_selector.get_current_threshold()
        self.detector.detect()
        self.detector.draw()


os.environ["CUDA_VISIBLE_DEVICES"] = str("0")
app = QApplication([])
root_folder = '/home/k_andrei/new_darknet/darknet/auto_labeled/vehicle+pedestrian+traffic_light+traffic_sign/yolov4/'
images_folder = '/home/k_andrei/new_darknet/darknet/auto_labeled/vehicle+pedestrian+traffic_light+traffic_sign/' \
                'test_yandex_disk/Taganrog_15'
vis = Visualizer(root_folder + 'config/yolov4.cfg', root_folder + 'epoch_36.weights',
                 root_folder + 'config/classes.names', images_folder, 800, 500)
vis.show()
app.exec_()
