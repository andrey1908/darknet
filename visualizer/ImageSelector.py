from PyQt5.QtWidgets import QLineEdit, QLabel, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap, QIntValidator
from PyQt5.QtCore import Qt, pyqtSignal
import os
import os.path as osp
import json
from time import time


class ImageSelector(QGroupBox):
    imageChanged = pyqtSignal(str)

    def __init__(self, images_folder, images_file, show_delay=False):
        super(ImageSelector, self).__init__('Image selector')
        self.images_folder = images_folder
        self.images_file = images_file
        self.show_delay = show_delay
        self.load_images()
        self.images_number = len(self.images_files)
        self.current_image_idx = 0 if self.images_number > 0 else None
        self.init_UI()
        self.prev_button.clicked.connect(self.go_to_prev_image)
        self.next_button.clicked.connect(self.go_to_next_image)
        self.apply_image_file_button.clicked.connect(self.go_to_selected_image)

    def load_images(self):
        if self.images_file is None:
            self.load_images_from_folder()
        elif self.images_file.endswith('.json'):
            self.load_images_from_json()
        else:
            raise RuntimeError('Unsupported images file format')

    def load_images_from_folder(self):
        images_files = sorted(os.listdir(self.images_folder))
        self.images_files = list(map(lambda x: osp.join(self.images_folder, x), images_files))

    def load_images_from_json(self):
        with open(self.images_file, 'r') as f:
            json_dict = json.load(f)
        self.images_files = list()
        for image in json_dict['images']:
            self.images_files.append(osp.join(self.images_folder, image['file_name']))

    def get_current_image_file(self):
        return self.images_files[self.current_image_idx]

    def init_UI(self):
        self.images_number_label = QLabel()
        self.images_number_label.setText('{} images'.format(self.images_number))
        self.prev_button = QPushButton('Prev')
        self.next_button = QPushButton('Next')
        self.current_image_idx_line_edit = QLineEdit()
        self.current_image_idx_line_edit.setValidator(QIntValidator())
        self.apply_image_file_button = QPushButton('Apply')
        if self.show_delay:
            self.delay_label = QLabel()
            self.delay_label.setText('- ms')

        hbox = QHBoxLayout()
        hbox.addWidget(self.prev_button)
        hbox.addWidget(self.next_button)
        hbox.addWidget(self.current_image_idx_line_edit)
        hbox.addWidget(self.apply_image_file_button)
        if self.show_delay:
            hbox.addWidget(self.delay_label)
        vbox = QVBoxLayout()
        vbox.addWidget(self.images_number_label)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.refresh_UI()

    def refresh_UI(self):
        self.current_image_idx_line_edit.setText(str(self.current_image_idx))

    def go_to_prev_image(self):
        if self.show_delay:
            start_time = time()
        if self.current_image_idx > 0:
            self.current_image_idx -= 1
        else:
            self.current_image_idx = self.images_number - 1
        self.refresh_UI()
        self.imageChanged.emit(self.images_files[self.current_image_idx])
        if self.show_delay:
            time_passed = (time() - start_time) * 1000
            self.delay_label.setText('{:.1f} ms'.format(time_passed))

    def go_to_next_image(self):
        if self.show_delay:
            start_time = time()
        if self.current_image_idx + 1 < self.images_number:
            self.current_image_idx += 1
        else:
            self.current_image_idx = 0
        self.refresh_UI()
        self.imageChanged.emit(self.images_files[self.current_image_idx])
        if self.show_delay:
            time_passed = (time() - start_time) * 1000
            self.delay_label.setText('{:.1f} ms'.format(time_passed))

    def go_to_selected_image(self):
        if self.show_delay:
            start_time = time()
        self.current_image_idx = int(self.current_image_idx_line_edit.text())
        if self.current_image_idx < 0:
            self.current_image_idx = 0
        if self.current_image_idx >= self.images_number:
            self.current_image_idx = self.images_number - 1
        self.refresh_UI()
        self.imageChanged.emit(self.images_files[self.current_image_idx])
        if self.show_delay:
            time_passed = (time() - start_time) * 1000
            self.delay_label.setText('{:.1f} ms'.format(time_passed))
