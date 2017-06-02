# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.8
#
# WARNING! All changes made in this file will be lost!

import os.path, PIL
from PyQt5 import QtCore, QtGui, QtWidgets
import socket
import struct
from PIL import Image, ImageQt, ImageDraw, ImageFont
import os, sys
import time
import pickle
import threading
import io
import resources
import numpy as np
class Ui_MainWindow(object):

    RC_socket = socket.socket()
    RC_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    RC_socket.connect(('dronepi.local', 8002))
    RC_connection = RC_socket.makefile('rwb')

    NN_socket = socket.socket()
    NN_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    NN_socket.connect(('biffen.local', 8001))
    NN_connection = NN_socket.makefile('rwb')

    image_lock = threading.Lock()
    pickle_stream = io.BytesIO()
    image_stream = io.BytesIO()
    yaw_pid_active = False
    pos_pid_active = False

    bbox_time = time.time()
    bbox_lock = threading.Lock()

    picSize = (640, 480)

    def __init__(self):
        threading.Thread(target=self.yaw_pid_thread, daemon=True).start()
        threading.Thread(target=self.pos_pid_thread, daemon=True).start()
        threading.Thread(target=self.camera_thread, daemon=True).start()

    def draw_boxes(self, boxes):
        mask = Image.new('RGBA', self.picSize, (255,255,255,0))
        d = ImageDraw.Draw(mask)
        fnt = ImageFont.truetype('/usr/share/fonts/truetype/ubuntu-font-family/UbuntuMono-R.ttf', 12)
        txt_offset_x = 0
        txt_offset_y = 20
        for box in boxes:
            p_coords = [box.coords[0]*self.picSize[0],
                        box.coords[1]*self.picSize[1],
                        box.coords[2]*self.picSize[0],
                        box.coords[3]*self.picSize[1]]
            d.rectangle(p_coords, outline='red')
            #print('drawing box at ', end='')
            #print([x for x in box.coords])
            textpos = (p_coords[0] - txt_offset_x, p_coords[1] - txt_offset_y)
            d.text(textpos, 'Class %s at %s confidence'%(box.classification,box.confidence), font=fnt, fill='red')

        return mask

    def send_command(self, cmd, arg=None):
        self.RC_connection.write(struct.pack('<c', bytes(cmd, encoding='ascii')))
        if arg != None:
            if type(arg) == str:
                self.RC_connection.write(struct.pack('<L', len(arg)))
                self.RC_connection.write(
                            struct.pack('<%ds'%len(arg),
                                bytes(arg, encoding='ascii')))
            elif type(arg) == float:
                self.RC_connection.write(struct.pack('<L', struct.calcsize('<f')))
                self.RC_connection.write(struct.pack('<f', arg))
            elif type(arg[0]) == float and type(arg[1]) == float:
                self.RC_connection.write(struct.pack('<L', struct.calcsize('<ff')))
                self.RC_connection.write(struct.pack('<ff', arg[0], arg[1]))
            else:
                print('Invalid argument: ', end='')
                print(arg[0])

        self.RC_connection.flush()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(640, 950)
        MainWindow.setMinimumSize(QtCore.QSize(480, 768))
        MainWindow.setMaximumSize(QtCore.QSize(16777215, 16777215))
        MainWindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        MainWindow.setAutoFillBackground(False)
        MainWindow.setStyleSheet("QWidget#centralWidget {    \n"
"    padding: 0;\n"
"    background-color: #f3f3f3; \n"
"}\n"
"\n"
"QWidget#cameraView{ \n"
"background-color: #cccccc; \n"
"background-position: center center;\n"
"background-repeat: no-repeat;\n"
"background-origin: content;\n"
"background-image: url(\":/images/camera_small.png\");\n"
"}\n"
"QPushButton {\n"
"background-color: #31bdd8;\n"
"border: none;\n"
"padding: 10px;\n"
"border-radius: 3px;\n"
"text-align: right;\n"
"color: white;\n"
"font: 20px \"Arial\";\n"
"background-position: left center;\n"
"background-repeat: no-repeat;\n"
"background-origin: content;\n"
"}\n"
"\n"
"QPushButton::pressed {\n"
"background-color: #89e7f9;\n"
"}\n"
"\n"
"QCheckBox {\n"
"    font: 16px \"Arial\" Bold;\n"
"    spacing: 10px;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked {\n"
"    image: url(:/images/checkbox_unchecked.png);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"    image: url(:/images/checkbox_checked.png);\n"
"}")
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setStyleSheet("")
        self.centralWidget.setObjectName("centralWidget")

        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")

        self.cameraView = QtWidgets.QLabel(self.centralWidget)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cameraView.sizePolicy().hasHeightForWidth())

        self.cameraView.setSizePolicy(sizePolicy)
        self.cameraView.setMinimumSize(QtCore.QSize(0, 0))
        self.cameraView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.cameraView.setSizeIncrement(QtCore.QSize(0, 0))
        self.cameraView.setObjectName("cameraView")

        self.verticalLayout.addWidget(self.cameraView)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.disarmBtn = QtWidgets.QPushButton(self.centralWidget)
        self.disarmBtn.setMinimumSize(QtCore.QSize(160, 90))
        self.disarmBtn.setMaximumSize(QtCore.QSize(300, 90))
        self.disarmBtn.setStyleSheet("QPushButton#disarmBtn {\n"
"background-image: url(\":/images/stop.png\");\n"
"}")
        self.disarmBtn.setFlat(True)
        self.disarmBtn.setObjectName("disarmBtn")
        self.gridLayout.addWidget(self.disarmBtn, 1, 1, 1, 1)
        self.landBtn = QtWidgets.QPushButton(self.centralWidget)
        self.landBtn.setMinimumSize(QtCore.QSize(160, 90))
        self.landBtn.setMaximumSize(QtCore.QSize(300, 90))
        self.landBtn.setStyleSheet("QPushButton#landBtn {\n"
"background-image: url(\":/images/land.png\");\n"
"}")
        self.landBtn.setFlat(True)
        self.landBtn.setObjectName("landBtn")
        self.gridLayout.addWidget(self.landBtn, 0, 1, 1, 1)
        self.posHoldBtn = QtWidgets.QPushButton(self.centralWidget)
        self.posHoldBtn.setMinimumSize(QtCore.QSize(160, 90))
        self.posHoldBtn.setMaximumSize(QtCore.QSize(300, 90))
        self.posHoldBtn.setStyleSheet("QPushButton#posHoldBtn {\n"
"background-image: url(\":/images/pos_hold.png\");\n"
"}")
        self.posHoldBtn.setFlat(True)
        self.posHoldBtn.setObjectName("posHoldBtn")
        self.gridLayout.addWidget(self.posHoldBtn, 2, 1, 1, 1)
        self.armBtn = QtWidgets.QPushButton(self.centralWidget)
        self.armBtn.setMinimumSize(QtCore.QSize(160, 90))
        self.armBtn.setStyleSheet("QPushButton#armBtn {\n"
"background-image: url(\":/images/propeller.png\");\n"
"}")
        self.armBtn.setFlat(True)
        self.armBtn.setObjectName("armBtn")
        self.gridLayout.addWidget(self.armBtn, 1, 0, 1, 1)
        self.takeOffBtn = QtWidgets.QPushButton(self.centralWidget)
        self.takeOffBtn.setMinimumSize(QtCore.QSize(160, 90))
        self.takeOffBtn.setMaximumSize(QtCore.QSize(300, 90))
        self.takeOffBtn.setStyleSheet("QPushButton#takeOffBtn {\n"
"background-image: url(\":/images/takeoff.png\");\n"
"}")
        self.takeOffBtn.setFlat(True)
        self.takeOffBtn.setObjectName("takeOffBtn")
        self.gridLayout.addWidget(self.takeOffBtn, 0, 0, 1, 1)
        self.guidedBtn = QtWidgets.QPushButton(self.centralWidget)
        self.guidedBtn.setMinimumSize(QtCore.QSize(160, 90))
        self.guidedBtn.setMaximumSize(QtCore.QSize(300, 90))
        self.guidedBtn.setStyleSheet("QPushButton#guidedBtn {\n"
"background-image: url(\":/images/forward.png\");\n"
"}")
        self.guidedBtn.setFlat(True)
        self.guidedBtn.setObjectName("guidedBtn")
        self.gridLayout.addWidget(self.guidedBtn, 2, 0, 1, 1)
        self.posCheckBox = QtWidgets.QCheckBox(self.centralWidget)
        self.posCheckBox.setChecked(True)
        self.posCheckBox.setObjectName("posCheckBox")
        self.gridLayout.addWidget(self.posCheckBox, 3, 0, 1, 1)
        self.yawCheckBox = QtWidgets.QCheckBox(self.centralWidget)
        self.yawCheckBox.setObjectName("yawCheckBox")
        self.gridLayout.addWidget(self.yawCheckBox, 3, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 640, 22))
        self.menuBar.setObjectName("menuBar")
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QtWidgets.QToolBar(MainWindow)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Quad Copter Control"))
        self.disarmBtn.setText(_translate("MainWindow", "Disarm"))
        self.landBtn.setText(_translate("MainWindow", "Land"))
        self.posHoldBtn.setText(_translate("MainWindow", "Position\n"
"Hold Mode"))
        self.armBtn.setText(_translate("MainWindow", "Arm"))
        self.takeOffBtn.setText(_translate("MainWindow", "Take Off"))
        self.guidedBtn.setText(_translate("MainWindow", "Guided\n"
"Mode"))
        self.posCheckBox.setText(_translate("MainWindow", "Position PID Active"))
        self.yawCheckBox.setText(_translate("MainWindow", "Yaw PID Active"))
        self.takeOffBtn.clicked.connect(self.takeOff)
        self.landBtn.clicked.connect(self.land)
        self.armBtn.clicked.connect(self.arm)
        self.disarmBtn.clicked.connect(self.disarm)
        self.posHoldBtn.clicked.connect(self.positionHold)
        self.guidedBtn.clicked.connect(self.loadStream)
        self.posCheckBox.stateChanged.connect(self.pos_check)
        self.yawCheckBox.stateChanged.connect(self.yaw_check)

    def yaw_check(self, state):
        print(state)
        self.yaw_pid_active = (state == QtCore.Qt.Checked)
    def pos_check(self, state):
        self.pos_pid_active = (state == QtCore.Qt.Checked)

    def takeOff(self):
        #self.takeOffBtn.setText("Taking off")
        self.send_command(cmd='t', arg=1.0)

    def land(self):
        #self.landBtn.setText("Landing")
        self.send_command(cmd='m', arg='LAND')

    def arm(self):
        #self.armBtn.setText("Running")
        self.send_command(cmd='b')

    def disarm(self):
        #self.disarmBtn.setText("Propellers\nstopped")
        self.send_command(cmd='n')

    def positionHold(self):
        #self.posHoldBtn.setText("Holding\nPosition")
        self.send_command(cmd='m', arg='POSHOLD')

    def guidedMode(self):
        #self.guidedBtn.setText("Scanning")
        self.send_command(cmd='m', arg='GUIDED')

    def loadStream(self):
        if (os.path.isfile("/Users/Markus/Infotiv/QuadCopterQT/QuadCopter/stream.jpg")):
            img = Image.open("/Users/Markus/Infotiv/QuadCopterQT/QuadCopter/stream.jpg")
            self.cameraView.setStyleSheet(
                "background-image: url(/Users/Markus/Infotiv/QuadCopterQT/QuadCopter/stream.jpg);")

    def yaw_pid_thread(self):
        angle_to_car = 0
        yaw_pid = PID(kp=200, kd=0, ki=0)
        dt = 0.1
        while True:
            time.sleep(dt) #only run PID loop every dt seconds
            if self.yaw_pid_active:
                #if bboxes are older than dt, we processed them last frame.
                if time.time()-self.bbox_time < dt:
                    with self.bbox_lock:
                        if len(self.bboxes) > 0:
                            best_box = self.bboxes[0]
                            for box in self.bboxes:
                                if box.confidence > best_box.confidence:
                                    best_box = box

                            box_center_x = (best_box.coords[0] + best_box.coords[2]) / 2
                            box_center_x = box_center_x - 0.5
                            cam_x_fov = 62.2*np.pi/180
                            angle_to_car = box_center_x * cam_x_fov

                            pid_out = yaw_pid.update(angle_to_car)

                            print('Angle PID: %s'%pid_out)
                            self.send_command(cmd='x', arg=(float(pid_out), float(dt)))

    def pos_pid_thread(self):
        pos_pid = PID(kp=10, kd=0, ki=0)
        dt = 0.1
        while True:
            time.sleep(dt) #only run PID loop every dt seconds
            if self.pos_pid_active:
                #if bboxes are older than dt, we processed them last frame.
                if time.time()-self.bbox_time < dt:
                    with self.bbox_lock:
                        if len(self.bboxes) > 0:
                            best_box = self.bboxes[0]
                            for box in self.bboxes:
                                if box.confidence > best_box.confidence:
                                    best_box = box

                            pos = self.get_relative_target_coords_fixed_drone([best_box.coords])
                            dist_to_car = pos[0][1]

                            if dist_to_car > 2:
                                dist_to_car = 2

                            pid_out = pos_pid.update(dist_to_car)
                            print('car pos is: ', end='')
                            print(pos)
                            print('Pos PID: %s'%pid_out)
                            self.send_command(cmd='v', arg=(float(-pid_out), float(dt)))


    def camera_thread(self):
        while True:
            self.NN_connection.write(struct.pack('<c', b'c'))
            self.NN_connection.flush()
            pickle_len = struct.unpack('<L', self.NN_connection.read(struct.calcsize('<L')))[0]
            self.pickle_stream.seek(0)
            self.pickle_stream.write(self.NN_connection.read(pickle_len))
            self.pickle_stream.seek(0)
            with self.bbox_lock:
                self.bboxes = pickle.loads(self.pickle_stream.read())

            self.NN_connection.write(struct.pack('<c', b'p'))
            self.NN_connection.flush()

            image_len = struct.unpack('<L', self.NN_connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                break
            # Construct a stream to hold the image data and read the image
            # data from the NN_connection
            self.image_stream.seek(0)
            self.image_stream.write(self.NN_connection.read(image_len))
            # Rewind the stream, open it as an image with PIL and do some
            # processing on it
            self.image_stream.seek(0)
            temp_image = Image.open(self.image_stream)
            self.picSize = (self.cameraView.size().width(), self.cameraView.size().height())
            temp_image = temp_image.resize(self.picSize)

            temp_image = temp_image.convert('RGBA')
            mask = self.draw_boxes(self.bboxes)
            temp_image = Image.alpha_composite(temp_image, mask)
            with self.image_lock:
                self.bbox_time = time.time()
                image = temp_image.convert('RGB')
                self.cameraView.setPixmap(QtGui.QPixmap.fromImage(ImageQt.ImageQt(image)))

    def get_relative_target_coords_fixed_drone(self, centers):

        '''
        NOTE: This version assumes the drone is level, and so will not give accurate results.
        If pose can be retreived, prefer the version in test_scripts/utils.py

        Transforms picture coordinates to local coordinate system.
        This assumes camera is mounted at 45 degrees to the vertical, but angle can
        be modified by cam_mount_angle.
        Input:
            centers: list of coord tuples in [0,1] representing found objects in image
        returns:
            positions: coord tuples for all objects found: (x,y) in meters from drone along ground level
        '''

        pi = 3.14159265
        pitch = 0
        roll = 0

        h = 1

        cam_mount_angle = pi/4
        cam_x_fov = 62.2*pi/180
        cam_y_fov = 48.8*pi/180
        positions = []
        for c in centers:
            phi_x = (c[0]-0.5)*cam_x_fov
            phi_y = -(c[1]-0.5)*cam_y_fov

            theta_y = pitch + cam_mount_angle + phi_y
            theta_x = phi_x


            y = np.tan(theta_y) * h
            r = np.sqrt(y**2+h**2)
            x = r * np.tan(theta_x)
            '''print('phi = %s,%s'%(phi_x, phi_y))
            print('pitch = %s, roll = %s'%(pitch, roll))
            print('theta = %s,%s'%(theta_x, theta_y))
            print('x,y,r,h = %s,%s,%s,%s'%(x,y,r,h))'''
            positions.append((x,y))
        return positions

class PID():
    var = 0
    accumulated_error = 0
    last_error = 0
    kp = 100
    kd = 0
    ki = 0
    i_max = 100
    setpoint = 0
    last_loop = 0
    first_run = True

    def __init__(self, kp, kd, ki, setpoint=0):
        self.kp = kp
        self.kd = kd
        self.ki = ki
        self.setpoint = setpoint

    def update(self, value):
        self.var = value
        error = self.var - self.setpoint
        dt = time.time() - self.last_loop
        D = (error - self.last_error)/dt
        I = error * dt + self.accumulated_error
        if I > self.i_max:
            I = self.i_max
        elif I < -self.i_max:
            I = -self.i_max
        pid_out = error * self.kp + self.kd * D + self.ki * I
        self.last_error = error
        self.last_loop = time.time()

        if not self.first_run:
            return pid_out
        else:
            self.first_run = False
            return 0




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
