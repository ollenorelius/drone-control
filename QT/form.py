# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.8
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import resources

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(480, 768)
        MainWindow.setMinimumSize(QtCore.QSize(480, 768))
        MainWindow.setMaximumSize(QtCore.QSize(1080, 1920))
        MainWindow.setStyleSheet("QWidget#centralWidget {    background-color: #f3f3f3; }\n"
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
        self.centralWidget.setObjectName("centralWidget")
        self.cameraView = QtWidgets.QWidget(self.centralWidget)
        self.cameraView.setGeometry(QtCore.QRect(0, 0, 480, 320))
        self.cameraView.setObjectName("cameraView")
        self.takeOffBtn = QtWidgets.QPushButton(self.centralWidget)
        self.takeOffBtn.setGeometry(QtCore.QRect(20, 340, 210, 90))
        self.takeOffBtn.setStyleSheet("QPushButton#takeOffBtn {\n"
"background-image: url(\":/images/takeoff.png\");\n"
"}")
        self.takeOffBtn.setFlat(True)
        self.takeOffBtn.setObjectName("takeOffBtn")
        self.landBtn = QtWidgets.QPushButton(self.centralWidget)
        self.landBtn.setGeometry(QtCore.QRect(250, 340, 210, 90))
        self.landBtn.setStyleSheet("QPushButton#landBtn {\n"
"background-image: url(\":/images/land.png\");\n"
"}")
        self.landBtn.setFlat(True)
        self.landBtn.setObjectName("landBtn")
        self.armBtn = QtWidgets.QPushButton(self.centralWidget)
        self.armBtn.setGeometry(QtCore.QRect(20, 450, 210, 90))
        self.armBtn.setStyleSheet("QPushButton#armBtn {\n"
"background-image: url(\":/images/propeller.png\");\n"
"}")
        self.armBtn.setFlat(True)
        self.armBtn.setObjectName("armBtn")
        self.disarmBtn = QtWidgets.QPushButton(self.centralWidget)
        self.disarmBtn.setGeometry(QtCore.QRect(250, 450, 210, 90))
        self.disarmBtn.setStyleSheet("QPushButton#disarmBtn {\n"
"background-image: url(\":/images/stop.png\");\n"
"}")
        self.disarmBtn.setFlat(True)
        self.disarmBtn.setObjectName("disarmBtn")
        self.posHoldBtn = QtWidgets.QPushButton(self.centralWidget)
        self.posHoldBtn.setGeometry(QtCore.QRect(250, 560, 210, 90))
        self.posHoldBtn.setStyleSheet("QPushButton#posHoldBtn {\n"
"background-image: url(\":/images/pos_hold.png\");\n"
"}")
        self.posHoldBtn.setFlat(True)
        self.posHoldBtn.setObjectName("posHoldBtn")
        self.guidedBtn = QtWidgets.QPushButton(self.centralWidget)
        self.guidedBtn.setGeometry(QtCore.QRect(20, 560, 210, 90))
        self.guidedBtn.setStyleSheet("QPushButton#guidedBtn {\n"
"background-image: url(\":/images/forward.png\");\n"
"}")
        self.guidedBtn.setFlat(True)
        self.guidedBtn.setObjectName("guidedBtn")
        self.yawCheckBox = QtWidgets.QCheckBox(self.centralWidget)
        self.yawCheckBox.setGeometry(QtCore.QRect(20, 680, 211, 30))
        self.yawCheckBox.setObjectName("yawCheckBox")
        self.posCheckBox = QtWidgets.QCheckBox(self.centralWidget)
        self.posCheckBox.setGeometry(QtCore.QRect(250, 680, 211, 30))
        self.posCheckBox.setChecked(True)
        self.posCheckBox.setObjectName("posCheckBox")
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 480, 22))
        self.menuBar.setObjectName("menuBar")
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QtWidgets.QToolBar(MainWindow)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.takeOffBtn.setText(_translate("MainWindow", "Take Off"))
        self.landBtn.setText(_translate("MainWindow", "Land"))
        self.armBtn.setText(_translate("MainWindow", "Arm"))
        self.disarmBtn.setText(_translate("MainWindow", "Disarm"))
        self.posHoldBtn.setText(_translate("MainWindow", "Position\n"
"Hold Mode"))
        self.guidedBtn.setText(_translate("MainWindow", "Guided\n"
"Mode"))
        self.yawCheckBox.setText(_translate("MainWindow", "Yaw PID Active"))
        self.posCheckBox.setText(_translate("MainWindow", "Position PID Active"))

