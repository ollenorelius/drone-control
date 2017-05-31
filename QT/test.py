import sys
from PyQt5 import QtCore, QtGui, QtWidgets

from form import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow, UI.MainUI.Ui_MainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindow()
    myapp.show()
    sys.exit(app.exec_())