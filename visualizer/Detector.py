from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt
from numpy import clip
from tools import init_model, free_model, resize_model, detect


class Detector(QGroupBox):
    def __init__(self, config_file, model_file, classes_file, window_width, window_height):
        super(Detector, self).__init__('Detector')
        self.config_file = config_file
        self.model_file = model_file
        self.classes_file = classes_file
        self.classes = self.get_classes()
        self.window_width = window_width
        self.window_height = window_height
        self.image_file = None
        self.init_UI()
        self.model = init_model(config_file, model_file)

    def get_classes(self):
        with open(self.classes_file, 'r') as f:
            classes = f.readlines()
        for i in range(len(classes)):
            if classes[i][-1] == '\n':
                classes[i] = classes[i][:-1]
        return classes

    def init_UI(self):
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(self.window_width, self.window_height)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black")
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        self.setLayout(vbox)

        self.pen = QPen(Qt.red)
        self.pen.setWidth(1)

    def refresh_UI(self):
        bboxes, scores, classes = detect(self.model, self.image_file, threshold=0.4)
        image = QPixmap(self.image_file)
        old_width = image.width()
        image = image.scaled(self.window_width, self.window_height, Qt.KeepAspectRatio)
        scale_factor = image.width() / old_width
        image_draw = QPainter(image)
        image_draw.setPen(self.pen)
        for bbox, score, cl in zip(bboxes, scores, classes):
            bbox = list(map(lambda x: x * scale_factor, bbox))
            self.preprocess_box(bbox, image.width(), image.height())
            if (bbox[2] <= 0) or (bbox[3] <= 0):
                continue
            image_draw.drawRect(bbox[0], bbox[1], bbox[2], bbox[3])
        image_draw.end()
        self.image_label.setPixmap(image)

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
