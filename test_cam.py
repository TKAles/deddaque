import os
import sys
import time
from threading import Thread
from PyQt5 import QtWidgets, uic, QtCore
from MonoCamera import MonoCamera
import pyqtgraph as pg

class Ui(QtWidgets.QMainWindow):
    
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('test_camera.ui', self)
        
        self.pushButton.clicked.connect(self.toggle_camera_test)
        self.MonoCamClass = MonoCamera()
        self.MonoWorker = Thread()
        self.show()
        return

    def toggle_camera_test(self):
        if self.MonoCamClass.is_connected == False:
            self.MonoCamClass.detect()
            self.MonoWorker = Thread(target=self.MonoCamClass.start_camera)
            self.ImageWorker = Thread(target=self.imageview_update_worker)
            self.pushButton.setText('Connected to {0}'.format(self.MonoCamClass.camera_id))
            self.MonoWorker.start()
            self.ImageWorker.start()
        elif self.MonoCamClass.is_connected == True:
            self.MonoCamClass.is_connected = False
            self.MonoWorker.join()
            self.ImageWorker.join()
            self.pushButton.setText('Connect to Camera')
            
    def imageview_update_worker(self):
        time.sleep(1.0)
        while self.MonoCamClass.is_connected:
            self.graphicsView.setImage(self.MonoCamClass.current_frame, autoLevels=False)
            self.fcounter.setText('FrameNo: {0:04d}'.format(self.MonoCamClass.frame_num))
            self.delta.setText('Old TS: {0:d}  Current TS: {1:d}  Delta: {2:d}'.format(
                self.MonoCamClass.old_timestamp, self.MonoCamClass.frame_timestamp,
                self.MonoCamClass.frame_timestamp - self.MonoCamClass.old_timestamp
            ))
            time.sleep(0.025)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()