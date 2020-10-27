from PyQt5.QtWidgets import QLabel, QGroupBox, QHBoxLayout, QVBoxLayout, QGraphicsPixmapItem, QGraphicsScene,\
                            QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from numpy import clip
from darknet import load_network, detect_image_letterbox, free_network_ptr, resize_network, load_image, make_image, resize_image, fill_image, embed_image, free_image
from time import time


class Detector(QObject):
    detectionsDrawn = pyqtSignal(QGraphicsScene, bool)

    def __init__(self, config_file, network_file, classes_file, image_file, threshold, input_size, image_scale):
        super(Detector, self).__init__()
        self.config_file = config_file
        self.network_file = network_file
        self.classes_file = classes_file
        self.classes_names = self.get_classes_names()
        self.network = load_network(config_file, None, network_file)
        resize_network(self.network, input_size[0], input_size[1])

        self.bboxes, self.scores, self.classes = None, None, None
        self.image_file = image_file
        self.pixmap_item = QGraphicsPixmapItem(QPixmap(image_file))
        self.image_c = load_image(image_file.encode(), 0, 0)
        self.threshold = threshold
        self.input_size = input_size
        self.image_scale = image_scale
        self.image_c_scaled = None
        self.image_c_scaled = self.get_scaled_image()

    def get_scaled_image(self):
        #start_time = time()
        assert 0 < self.image_scale <= 1
        if self.image_scale == 1:
            #print((time() - start_time) * 1000)
            return None
        w, h = self.image_c.w, self.image_c.h
        new_w, new_h = int(w * self.image_scale), int(h * self.image_scale)
        resized = resize_image(self.image_c, new_w, new_h)
        boxed = make_image(w, h, self.image_c.c)
        fill_image(boxed, 0.5)
        embed_image(resized, boxed, int((w - new_w) / 2), int((h - new_h) / 2))
        free_image(resized)
        #print((time() - start_time) * 1000)
        return boxed

    def get_classes_names(self):
        with open(self.classes_file, 'r') as f:
            classes_names = f.readlines()
        for i in range(len(classes_names)):
            if classes_names[i][-1] == '\n':
                classes_names[i] = classes_names[i][:-1]
        return classes_names

    def new_image(self, image_file):
        self.image_file = image_file
        self.pixmap_item = QGraphicsPixmapItem(QPixmap(image_file))
        free_image(self.image_c)
        if self.image_c_scaled is not None:
            free_image(self.image_c_scaled)
        self.image_c = load_image(image_file.encode(), 0, 0)
        self.image_c_scaled = self.get_scaled_image()
        self.detect()
        self.draw(reset_scale=True)

    def new_threshold(self, threshold):
        self.threshold = threshold
        self.draw(reset_scale=False)

    def new_input_size(self, input_size):
        self.input_size = input_size
        resize_network(self.network, input_size[0], input_size[1])
        self.detect()
        self.draw(reset_scale=False)

    def new_image_scale(self, image_scale):
        self.image_scale = image_scale
        if self.image_c_scaled is not None:
            free_image(self.image_c_scaled)
        self.image_c_scaled = self.get_scaled_image()
        self.detect()
        self.draw(reset_scale=False)

    def detect(self):
        if self.image_c_scaled is None:
            image = self.image_c
        else:
            image = self.image_c_scaled
        predictions = detect_image_letterbox(self.network, image, max_dets=100)
        self.classes, self.scores, self.bboxes = list(), list(), list()
        for cl, score, bbox in predictions:
            bbox = [bbox[0] - bbox[2]/2, bbox[1] - bbox[3]/2, bbox[0] + bbox[2]/2, bbox[1] + bbox[3]/2]
            self.preprocess_box(bbox, self.pixmap_item.pixmap().width(), self.pixmap_item.pixmap().height())
            self.classes.append(cl)
            self.scores.append(score)
            self.bboxes.append(bbox)

    def draw(self, reset_scale):
        scene = QGraphicsScene()
        scene.addItem(self.pixmap_item)
        for bbox, score, cl in zip(self.bboxes, self.scores, self.classes):
            if score < self.threshold:
                continue
            if (bbox[2] <= 0) or (bbox[3] <= 0):
                continue
            text = self.classes_names[cl]
            text = text + ' {:.2f}'.format(score)
            rect_item = QGraphicsRectItem(bbox[0], bbox[1], bbox[2], bbox[3])
            text_item = QGraphicsTextItem(text)
            text_item.setPos(bbox[0], bbox[1])
            scene.addItem(rect_item)
            scene.addItem(text_item)
        self.detectionsDrawn.emit(scene, reset_scale)

    def preprocess_box(self, bbox, im_w, im_h):
        bbox[0], bbox[1] = self.transform_point(bbox[0], bbox[1])
        bbox[2], bbox[3] = self.transform_point(bbox[2], bbox[3])
        bbox[0] = clip(bbox[0], 0, im_w)
        bbox[1] = clip(bbox[1], 0, im_h)
        bbox[2] = clip(bbox[2], 0, im_w)
        bbox[3] = clip(bbox[3], 0, im_h)
        bbox[:] = [round(b) for b in bbox]
        bbox[2] -= bbox[0]
        bbox[3] -= bbox[1]

    def transform_point(self, x, y):
        x -= self.image_c.w / 2
        y -= self.image_c.h / 2
        x /= self.image_scale
        y /= self.image_scale
        x += self.image_c.w / 2
        y += self.image_c.h / 2
        return x, y

    def __del__(self):
        if hasattr(self, 'network'):
            free_network_ptr(self.network)
        if hasattr(self, 'image_c'):
            free_image(self.image_c)
        if hasattr(self, 'image_c_scaled'):
            if self.image_c_scaled is not None:
                free_image(self.image_c_scaled)
