# -*- coding: utf-8 -*-

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Slot
from PySide6.QtGui import QAction
from math import sqrt

import sys
import math
import datetime

INIT_X = 640
INIT_Y = 480
EPS = 0.000005


class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __mul__(self, other):
        return self.x * other.x + self.y * other.y
    
    def __xor__(self, other):
        return self.x * other.y - self.y * other.x
    
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)
    
    def __truediv__(self, k):
        return Point(self.x / k, self.y / k)
    
    def len(self):
        return sqrt(self.x ** 2 + self.y ** 2)


def point_on_segment(A, B, P):
    if abs((P - A) ^ (B - A)) > EPS:
        return False
    return ((P - A) * (B - A)) > -EPS and ((P - B) * (A - B)) > -EPS


def sign(x):
    if abs(x) < EPS:
        return 0
    if x > 0:
        return 1
    return -1


def point_in_angle(A, O, B, P):
    a, b, p = A - O, B - O, P - O
    return sign(a ^ p) * sign(a ^ b) >= 0 and sign(b ^ p) * sign(b ^ a) >= 0


def point_in_triangle(A, B, C, P):
    return point_in_angle(A, B, C, P) and point_in_angle(A, C, B, P) and point_in_angle(B, A, C, P)


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
        elif self.fractal_type == 'triangle':
            return self.color_triangle(x, y)
        elif self.fractal_type == '4':
            return self.color_4(x, y)
        else:
            return self.color_grid(x, y)
    
    def color_triangle(self, x, y):
        max_iter = min(64, self.param)
        white = (255 << 16) + (255 << 8) + 255
        black = 0
        p = Point(x, y)
        A = Point(-1.2, -1.2 / sqrt(3))
        B = Point(1.2, -1.2 / sqrt(3))
        C = Point(0, 2.4 / sqrt(3))
        if not point_in_triangle(A, B, C, p):
            return white
        for iteration in range(max_iter):
            if point_on_segment(A, B, p) or point_on_segment(A, C, p) or point_on_segment(B, C, p):
                return black
            pAB = (A + B) / 2
            pAC = (A + C) / 2
            pBC = (B + C) / 2
            if point_in_triangle(pAC, pBC, C, p):
                A = pAC
                B = pBC
            elif point_in_triangle(A, pAB, pAC, p):
                B = pAB
                C = pAC
            elif point_in_triangle(pAB, B, pBC, p):
                A = pAB
                C = pBC
            else:
                return white
        return white
    
    def color_mandelbrot(self, x, y):
        max_iter = self.param
        zx, zy = 0.0, 0.0
        i = 0
        while i < max_iter:
            zx2, zy2 = zx * zx, zy * zy
            if zx2 + zy2 > 4.0:
                break
            zy = 2.0 * zx * zy + y
            zx = zx2 - zy2 + x
            i += 1
        if i == max_iter:
            return 0x000000
        else:
            hue = int(255 * i / max_iter)
            r = hue
            g = 255 - hue
            b = hue // 2
            return (r << 16) + (g << 8) + b
    
    
    def color_4(self, x, y):
        max_iter = self.param
        zx, zy = x, y
        i = 0
        while i < max_iter:
            zx2, zy2 = zx * zx, zy * zy
            if zx2 + zy2 > 4.0:
                break
            zy = 2.0 * zx * zy + 0.179
            zx = zx2 - zy2 + -0.8
            i += 1
        if i == max_iter:
            return 0x000000
        else:
            hue = int(255 * i / max_iter)
            r = hue
            g = 255 - hue
            b = hue // 2
            return (r << 16) + (g << 8) + b

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

        action_triangle = QAction("Треугольник Серпинского", self, checkable=True)
        action_triangle.setChecked(self.viewer.fractal_type == "triangle")
        action_triangle.triggered.connect(lambda: self.viewer.set_fractal_type("triangle"))
        fractal_group.addAction(action_triangle)
        fractal_menu.addAction(action_triangle)

        action_4 = QAction("Жюлиа", self, checkable=True)
        action_4.setChecked(self.viewer.fractal_type == "4")
        action_4.triggered.connect(lambda: self.viewer.set_fractal_type("4"))
        fractal_group.addAction(action_4)
        fractal_menu.addAction(action_4)
        
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
