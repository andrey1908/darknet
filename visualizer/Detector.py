from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from numpy import clip
from tools import init_model, free_model, resize_model, detect, lib


class Detector(QObject):
    detectionsDrawn = pyqtSignal(QPixmap)

    def __init__(self, config_file, model_file, classes_file, image_file, threshold, input_size):
        super(Detector, self).__init__()
        self.config_file = config_file
        self.model_file = model_file
        self.classes_file = classes_file
        self.classes_names = self.get_classes_names()
        self.pen = QPen(Qt.red)
        self.pen.setWidth(3)
        self.font = QFont('Decorative', 20)
        self.model = init_model(config_file, model_file)
        resize_model(self.model, input_size[0], input_size[1])

        self.bboxes, self.scores, self.classes = None, None, None
        self.image_file = image_file
        self.image_pixmap = QPixmap(image_file)
        self.image_c = lib.load_image(image_file.encode(), 0, 0, lib.get_model_c(self.model))
        self.threshold = threshold
        self.input_size = input_size

    def get_classes_names(self):
        with open(self.classes_file, 'r') as f:
            classes_names = f.readlines()
        for i in range(len(classes_names)):
            if classes_names[i][-1] == '\n':
                classes_names[i] = classes_names[i][:-1]
        return classes_names

    def new_image(self, image_file):
        self.image_file = image_file
        self.image_pixmap = QPixmap(image_file)
        self.image_c = lib.load_image(image_file.encode(), 0, 0, lib.get_model_c(self.model))
        self.detect()
        self.draw()

    def new_threshold(self, threshold):
        self.threshold = threshold
        self.draw()

    def new_input_size(self, input_size):
        self.input_size = input_size
        resize_model(self.model, input_size[0], input_size[1])
        self.detect()
        self.draw()

    def detect(self):
        self.bboxes, self.scores, self.classes = detect(self.model, self.image_c, max_dets=100)
        for bbox, score, cl in zip(self.bboxes, self.scores, self.classes):
            self.preprocess_box(bbox, self.image_pixmap.width(), self.image_pixmap.height())
            if score < self.threshold:
                continue
            if (bbox[2] <= 0) or (bbox[3] <= 0):
                continue

    def draw(self):
        image = self.image_pixmap.copy()
        image_draw = QPainter(image)
        image_draw.setPen(self.pen)
        image_draw.setFont(self.font)
        for bbox, score, cl in zip(self.bboxes, self.scores, self.classes):
            if score < self.threshold:
                continue
            if (bbox[2] <= 0) or (bbox[3] <= 0):
                continue
            image_draw.drawRect(bbox[0], bbox[1], bbox[2], bbox[3])
            image_draw.drawText(bbox[0], bbox[1], '{} {:.2f}'.format(self.classes_names[cl], score))
        image_draw.end()
        self.detectionsDrawn.emit(image)

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