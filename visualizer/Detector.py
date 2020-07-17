from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from numpy import clip
from tools import init_model, free_model, resize_model, detect


class Detector(QObject):
    detectionCompleted = pyqtSignal(QPixmap)

    def __init__(self, config_file, model_file, classes_file):
        super(Detector, self).__init__()
        self.config_file = config_file
        self.model_file = model_file
        self.classes_file = classes_file
        self.classes = self.get_classes()
        self.image_file = None
        self.pen = QPen(Qt.red)
        self.pen.setWidth(3)
        self.model = init_model(config_file, model_file)

    def get_classes(self):
        with open(self.classes_file, 'r') as f:
            classes = f.readlines()
        for i in range(len(classes)):
            if classes[i][-1] == '\n':
                classes[i] = classes[i][:-1]
        return classes

    def detect(self):
        bboxes, scores, classes = detect(self.model, self.image_file, threshold=0.4)
        image = QPixmap(self.image_file)
        image_draw = QPainter(image)
        image_draw.setPen(self.pen)
        for bbox, score, cl in zip(bboxes, scores, classes):
            self.preprocess_box(bbox, image.width(), image.height())
            if (bbox[2] <= 0) or (bbox[3] <= 0):
                continue
            image_draw.drawRect(bbox[0], bbox[1], bbox[2], bbox[3])
        image_draw.end()
        self.detectionCompleted.emit(image)

    def preprocess_box(self, bbox, im_w, im_h):
        bbox[0] = clip(bbox[0], 0, im_w-1)
        bbox[1] = clip(bbox[1], 0, im_h-1)
        bbox[2] = clip(bbox[2], 0, im_w-1)
        bbox[3] = clip(bbox[3], 0, im_h-1)
        bbox[:] = [round(b) for b in bbox]
        bbox[2] -= bbox[0]
        bbox[3] -= bbox[1]

    def __del__(self):
        if hasattr(self, 'model'):
            free_model(self.model)
