import time
from PyQt5 import QtWidgets, QtCore, uic
import pyqtgraph as pg
from vimba import *
from threading import Thread
import sys

from MonoCamera import MonoCamera

class Ui(QtWidgets.QMainWindow):

    def __init__(self) -> None:
        self.ui_path = 'ded-daq.ui'
        self.first_monocam_view = pg.ViewBox()
        self.first_monocam_image = pg.ImageItem()
        self.first_monocam = MonoCamera()
        self.first_monocam_qtimer = QtCore.QTimer()
        self.first_monocam_qtimer.timeout.connect(self.WindowVideoWorker)
        super(Ui, self).__init__()
        uic.loadUi(self.ui_path, self)
        self.PBDetect_Mono1.clicked.connect(self.UIMonoCam1Detect)
        self.PBEnable_Mono1.clicked.connect(self.UIMonoCam1ToggleStream)
        self.showMaximized()
        
    def UIMonoCam1Detect(self):
        self.PBDetect_Mono1.setText('Detecting...')
        self.first_monocam.detect()
        self.PBDetect_Mono1.setText('Found {0}'.format(self.first_monocam.camera_id))
        self.first_monocam.get_exposure()
        self.LEExposure_Mono1.setText('{0:.1f}'.format(self.first_monocam.exposure_time))
        self.PBDetect_Mono1.setEnabled(False)
        return

    def UIMonoCam1ToggleStream(self):
        if self.first_monocam.is_streaming == False:
            self.first_monocam.start_camera()
            self.GVMonoCamera1.setCentralWidget(self.first_monocam_view)
            self.first_monocam_view.addItem(self.first_monocam_image)
            self.first_monocam_qtimer.start(30)
            self.PBEnable_Mono1.setText('End Stream')
            self.first_monocam.is_streaming = True
        elif self.first_monocam.is_streaming == True:
            self.first_monocam.is_streaming = False
            self.first_monocam_qtimer.stop()
            self.PBEnable_Mono1.setText('Start Stream')
        return

    def WindowVideoWorker(self):
        self.first_monocam_image.setImage(self.first_monocam.current_frame, autoLevels=True)
        

    
        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
