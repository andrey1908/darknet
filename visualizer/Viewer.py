from PyQt5.QtWidgets import QApplication, QWidget, QToolButton, QLineEdit, QVBoxLayout, QHBoxLayout, QGraphicsView,\
                            QGraphicsScene, QGraphicsPixmapItem, QFrame, QGraphicsItem, QGroupBox
from PyQt5.QtGui import QPixmap, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint, QRectF, pyqtSignal


class Viewer(QGroupBox):
    def __init__(self, width, height):
        super(Viewer, self).__init__('Viewer')
        self.width = width
        self.height = height
        self.zoom = 0
        self.init_UI()

    def init_UI(self):
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene = QGraphicsScene()
        self.scene.addItem(self.pixmap_item)
        self.view = QGraphicsView()
        self.view.setScene(self.scene)
        self.view.wheelEvent = self.wheelEvent
        self.view.setFixedSize(self.width, self.height)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        # self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.view.setFrameShape(QFrame.NoFrame)
        vbox = QVBoxLayout()
        vbox.addWidget(self.view)
        self.setLayout(vbox)

    def set_pixmap(self, pixmap=None):
        if pixmap is not None:
            self.pixmap_item.setPixmap(pixmap)
        if self.pixmap_item.pixmap().isNull():
            return
        rect = QRectF(self.pixmap_item.pixmap().rect())
        self.view.setSceneRect(rect)
        unity = self.view.transform().mapRect(QRectF(0, 0, 1, 1))
        self.view.scale(1 / unity.width(), 1 / unity.height())
        viewrect = self.view.viewport().rect()
        scenerect = self.view.transform().mapRect(rect)
        factor = min(viewrect.width() / scenerect.width(),
                     viewrect.height() / scenerect.height())
        self.view.scale(factor, factor)
        self.zoom = 0

    def wheelEvent(self, event):
        if self.pixmap_item.pixmap().isNull():
            return
        if event.angleDelta().y() > 0:
            factor = 1.25
            self.zoom += 1
        else:
            factor = 0.8
            self.zoom -= 1
        if self.zoom > 0:
            self.view.scale(factor, factor)
        elif self.zoom == 0:
            self.set_pixmap()
        else:
            self.zoom = 0


class _Viewer(QGraphicsView):
    def __init__(self, parent):
        super(Viewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setFixedSize(600, 300)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        #self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.setFrameShape(QFrame.NoFrame)

    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        if self._photo.pixmap().isNull():
            return
        rect = QRectF(self._photo.pixmap().rect())
        self.setSceneRect(rect)
        unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
        self.scale(1 / unity.width(), 1 / unity.height())
        viewrect = self.viewport().rect()
        scenerect = self.transform().mapRect(rect)
        factor = min(viewrect.width() / scenerect.width(),
                     viewrect.height() / scenerect.height())
        self.scale(factor, factor)
        self._zoom = 0

    def setPhoto(self, pixmap=None):
        self._zoom = 0
        self._empty = False
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._photo.setPixmap(pixmap)
        self.fitInView()

    def wheelEvent(self, event):
        if self._photo.pixmap().isNull():
            return
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1
        if self._zoom > 0:
            self.scale(factor, factor)
        elif self._zoom == 0:
            self.fitInView()
        else:
            self._zoom = 0


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.viewer = Viewer(self)
        # 'Load image' button
        self.btnLoad = QToolButton(self)
        self.btnLoad.setText('Load image')
        self.btnLoad.clicked.connect(self.loadImage)
        # Arrange layout
        VBlayout = QVBoxLayout(self)
        VBlayout.addWidget(self.viewer)
        HBlayout = QHBoxLayout()
        HBlayout.setAlignment(Qt.AlignLeft)
        HBlayout.addWidget(self.btnLoad)
        VBlayout.addLayout(HBlayout)

    def loadImage(self):
        self.viewer.set_pixmap(QPixmap('image.jpg'))


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
