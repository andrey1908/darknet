from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from ImageSelector import ImageSelector
from Detector import Detector
import os


class Visualizer(QWidget):
    def __init__(self, config_file, model_file, classes_file, images_folder, window_width, window_height):
        super(Visualizer, self).__init__()
        self.image_selector = ImageSelector(images_folder)
        self.image_selector.imageChanged.connect(self.imageChanged)
        self.detector = Detector(config_file, model_file, classes_file, window_width, window_height)
        self.init_UI()
        self.init_detector()

    def init_UI(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_selector)
        vbox.addWidget(self.detector)
        self.setLayout(vbox)

    def init_detector(self):
        self.detector.image_file = self.image_selector.images_files[self.image_selector.current_image_idx]
        self.detector.refresh_UI()

    def imageChanged(self):
        self.detector.image_file = self.image_selector.images_files[self.image_selector.current_image_idx]
        self.detector.refresh_UI()


os.environ["CUDA_VISIBLE_DEVICES"] = str("0")
app = QApplication([])
root_folder = '/home/k_andrei/new_darknet/darknet/auto_labeled/vehicle+pedestrian+traffic_light+traffic_sign/yolov4/'
images_folder = '/home/k_andrei/new_darknet/darknet/auto_labeled/vehicle+pedestrian+traffic_light+traffic_sign/' \
                'test_yandex_disk/Taganrog_15'
vis = Visualizer(root_folder + 'config/yolov4.cfg', root_folder + 'epoch_36.weights',
                 root_folder + 'config/classes.names', images_folder, 700, 500)
vis.show()
app.exec_()
