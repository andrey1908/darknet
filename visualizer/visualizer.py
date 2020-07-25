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
import argparse


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cfg', '--config-file', required=True, type=str)
    parser.add_argument('-model', '--model-file', required=True, type=str)
    parser.add_argument('-cls', '--classes-file', required=True, type=str)
    parser.add_argument('-img-fld', '--images-folder', required=True, type=str)
    parser.add_argument('-img-file', '--images-file', type=str, default=None)
    parser.add_argument('-win-w', '--window-width', type=int, default=900)
    parser.add_argument('-win-h', '--window-height', type=int, default=500)
    parser.add_argument('-in-w', '--input-base-width', type=int, default=1024)
    parser.add_argument('-in-h', '--input-base-height', type=int, default=576)
    parser.add_argument('-gpu', '--gpu', type=int, default=0)
    return parser


class Visualizer(QWidget):
    def __init__(self, config_file, model_file, classes_file, images_folder, images_file, window_width=900, window_height=500,
                 input_base_width=1024, input_base_height=576):
        super(Visualizer, self).__init__()
        self.image_selector = ImageSelector(images_folder, images_file, show_delay=True)
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
        self.detector.detectionsDrawn.connect(self.viewer.set_scene)
        self.init_UI()
        self.detector.detect()
        self.detector.draw(reset_scale=True)

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


if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
    kwargs = vars(args)
    kwargs.pop('gpu')
    app = QApplication([])
    vis = Visualizer(**kwargs)
    vis.show()
    app.exec_()
