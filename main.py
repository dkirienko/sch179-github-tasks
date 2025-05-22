# -*- coding: utf-8 -*-

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Slot
from PySide6.QtGui import QAction
from cmath import *

import sys
import math
import datetime

INIT_X = 640
INIT_Y = 480

class MyWidget(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width = INIT_X
        self.height = INIT_Y
        self.resize(self.width, self.height)
        self.param = 128
        self.undo = []
        self.image = None
        self.set_fractal_type('original')
        self.rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Shape.Rectangle, self)

    def color_grid(self, x, y):
        red = int(128 + self.param * math.sin((x + y) * 16))
        green = int(128 + (x + y) * 16)
        blue = int(128 + self.param * math.sin((x - y) * 16))

        red = min(max(red, 0), 255)
        green = min(max(green, 0), 255)
        blue = min(max(blue, 0), 255)

        return (red << 16) + (green << 8) + blue

    def color(self, x, y):
        if self.fractal_type == 'mandelbrot':
            return self.color_mandelbrot(x, y)
        elif self.fractal_type == 'newton6':
            return self.color_newton6(x, y)
        else:
            return self.color_grid(x, y)

    def color_mandelbrot(self, x, y):
        max_iter = self.param
        zx, zy = 0.0, 0.0
        for i in range(max_iter):
            zx2, zy2 = zx * zx, zy * zy
            if zx2 + zy2 > 4.0:
                break
            zy = 2.0 * zx * zy + y
            zx = zx2 - zy2 + x
        if i == max_iter - 1:
            return 0x000000
        else:
            hue = int(255 * i / max_iter)
            r = hue
            g = 255 - hue
            b = hue // 2
            return (r << 16) + (g << 8) + b
    
    def color_newton6(self, x, y):
        max_iter = self.param
        f = lambda z: pow(z, 6) - 1
        fd = lambda z: 5 * pow(z, 5)
        roots = [-1, 1, complex(-0.5, sqrt(3) / 2), complex(-0.5, -sqrt(3) / 2), complex(0.5, sqrt(3) / 2), complex(0.5, -sqrt(3) / 2)]
        colorlist = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (0, 1, 1), (1, 0, 1)]
        zx, zy = x, y
        z = complex(zx, zy)
        for i in range(max_iter):
            try:
                z -= f(z) / fd(z)
            except:
                break
            tol = 1e-6
            for j in range(len(roots)):
                d = z - roots[j]
                if (abs(d.real) < tol and abs(d.imag) < tol):
                    hue = min(255, max(0, 255 - int(255 * i / max_iter * 3)))
                    col = 0
                    for k in range(3):
                        col += (hue * colorlist[j][k]) << (k * 8)
                    return col
        return 0x000000
            

    def update(self):
        xm = [self.xa + (self.xb - self.xa) * kx / self.width for kx in range(self.width)]
        ym = [self.yb + (self.ya - self.yb) * ky / self.height for ky in range(self.height)]
        self.image = QtGui.QImage(self.width, self.height, QtGui.QImage.Format.Format_RGB32)
        for i in range(self.width):
            for j in range(self.height):
                self.image.setPixel(i, j, self.color(xm[i], ym[j]))
        painter = QtGui.QPainter(self.image)
        painter.setPen(QtGui.QColor("white"))
        painter.drawText(QtCore.QRectF(0, 0, self.width, self.height),
                         QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter,
                         "{:.4g}".format(self.yb))
        painter.drawText(QtCore.QRectF(0, 0, self.width, self.height),
                         QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignHCenter,
                         "{:.4g}".format(self.ya))
        painter.drawText(QtCore.QRectF(0, 0, self.width, self.height),
                         QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft,
                         "{:.4g}".format(self.xa))
        painter.drawText(QtCore.QRectF(0, 0, self.width, self.height),
                         QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignRight,
                         "{:.4g}".format(self.xb))
        painter.end()
        self.setPixmap(QtGui.QPixmap.fromImage(self.image))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        self.origin = event.position().toPoint()
        self.rubberBand.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        self.rubberBand.setGeometry(QtCore.QRect(self.origin, event.position().toPoint()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        self.rubberBand.hide()
        self.resize_region(event.position().toPoint())

    def resize_region(self, pos):
        x1 = self.origin.x()
        x2 = pos.x()
        y1 = self.origin.y()
        y2 = pos.y()
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        self.undo.append((self.xa, self.xb, self.ya, self.yb))
        self.xa, self.xb = self.xa + x1 * (self.xb - self.xa) / self.width, self.xa + x2 * (self.xb - self.xa) / self.width
        self.yb, self.ya = self.yb + y1 * (self.ya - self.yb) / self.height, self.yb + y2 * (self.ya - self.yb) / self.height
        self.update()

    @Slot()
    def action_back(self):
        if self.undo:
            self.xa, self.xb, self.ya, self.yb = self.undo.pop()
            self.update()

    @Slot()
    def action_save(self):
        filename = "fractal_{:%Y-%m-%d_%H-%M-%S}.jpg".format(datetime.datetime.now())
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Select file to save image", filename, "JPEG files (*.jpg)")
        if filename:
            self.image.save(filename, "JPEG", 100)
            print("Image saved as", filename)

    @Slot()
    def action_set_param(self):
        param, ok_pressed = QtWidgets.QInputDialog.getInt(self, "Enter parameter", "", self.param, 32, 256, 1)
        if ok_pressed:
            self.param = param
            self.update()

    def set_fractal_type(self, ftype):
        self.fractal_type = ftype
        self.undo.clear()
        self.xa = -self.width / 320
        self.xb = self.width / 320
        self.ya = -self.height / 320
        self.yb = self.height / 320
        self.update()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fractal Viewer")
        self.viewer = MyWidget()
        self.setCentralWidget(self.viewer)
        self.init_menu()

    def init_menu(self):
        menubar = self.menuBar()

        # Фракталы
        fractal_menu = menubar.addMenu("Выбор фрактала")

        fractal_group = QtGui.QActionGroup(self)
        fractal_group.setExclusive(True)

        action_original = QAction("Муар (не фрактал)", self, checkable=True)
        action_original.setChecked(self.viewer.fractal_type == "original")
        action_original.triggered.connect(lambda: self.viewer.set_fractal_type("original"))
        fractal_group.addAction(action_original)
        fractal_menu.addAction(action_original)

        action_mandelbrot = QAction("Мандельброт", self, checkable=True)
        action_mandelbrot.setChecked(self.viewer.fractal_type == "mandelbrot")
        action_mandelbrot.triggered.connect(lambda: self.viewer.set_fractal_type("mandelbrot"))
        fractal_group.addAction(action_mandelbrot)
        fractal_menu.addAction(action_mandelbrot)
        
        action_newton6 = QAction("Ньютон p(x) = x⁶ - 1", self, checkable=True)
        action_newton6.setChecked(self.viewer.fractal_type == "newton6")
        action_newton6.triggered.connect(lambda: self.viewer.set_fractal_type("newton6"))
        fractal_group.addAction(action_newton6)
        fractal_menu.addAction(action_newton6)

        # Действия
        actions_menu = menubar.addMenu("Действия")

        action_back = QAction("Назад", self)
        action_back.triggered.connect(self.viewer.action_back)
        actions_menu.addAction(action_back)

        action_save = QAction("Сохранить изображение", self)
        action_save.triggered.connect(self.viewer.action_save)
        actions_menu.addAction(action_save)

        action_param = QAction("Задать параметр", self)
        action_param.triggered.connect(self.viewer.action_set_param)
        actions_menu.addAction(action_param)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.resize(INIT_X, INIT_Y)
    win.viewer.update()
    win.show()
    sys.exit(app.exec())
