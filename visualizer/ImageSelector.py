from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
import os


class ImageSelector(QGroupBox):
    imageChanged = pyqtSignal(str)

    def __init__(self, images_folder, width=None, height=None):
        super(ImageSelector, self).__init__('Image selector')
        self.images_folder = images_folder
        self.width = width
        self.height = height
        self.show_selected_image = (self.width is not None) and (self.height is not None)
        self.load_images()
        self.current_image_idx = 0 if len(self.images_files) > 0 else None
        self.init_UI()
        self.prev_button.clicked.connect(self.go_to_prev_image)
        self.next_button.clicked.connect(self.go_to_next_image)

    def load_images(self):
        images_files = sorted(os.listdir(self.images_folder))
        self.images_files = list(map(lambda x: os.path.join(self.images_folder, x), images_files))

    def init_UI(self):
        self.prev_button = QPushButton('Prev')
        self.next_button = QPushButton('Next')
        self.current_image_idx_label = QLabel()
        hbox = QHBoxLayout()
        hbox.addWidget(self.prev_button)
        hbox.addWidget(self.next_button)
        hbox.addWidget(self.current_image_idx_label)
        layout = hbox
        if self.show_selected_image:
            self.image_label = QLabel()
            self.image_label.setFixedSize(self.width, self.height)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setStyleSheet("background-color: black")
            vbox = QVBoxLayout()
            vbox.addLayout(hbox)
            vbox.addWidget(self.image_label)
            layout = vbox
        self.setLayout(layout)
        self.refresh_UI()

    def refresh_UI(self):
        self.current_image_idx_label.setNum(self.current_image_idx)
        if self.show_selected_image:
            image_to_show = QPixmap(self.images_files[self.current_image_idx])
            image_to_show = image_to_show.scaled(self.width, self.height, Qt.KeepAspectRatio)
            self.image_label.setPixmap(image_to_show)

    def go_to_prev_image(self):
        if self.current_image_idx > 0:
            self.current_image_idx -= 1
        else:
            self.current_image_idx = len(self.images_files) - 1
        self.refresh_UI()
        self.imageChanged.emit(self.images_files[self.current_image_idx])

    def go_to_next_image(self):
        if self.current_image_idx + 1 < len(self.images_files):
            self.current_image_idx += 1
        else:
            self.current_image_idx = 0
        self.refresh_UI()
        self.imageChanged.emit(self.images_files[self.current_image_idx])
