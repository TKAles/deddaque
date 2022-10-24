import time
from PyQt5 import QtWidgets, QtCore, uic
import pyqtgraph as pg
from vimba import *
import sys

from MonoCamera import MonoCamera

class Ui(QtWidgets.QMainWindow):

    def __init__(self) -> None:
        self.ui_path = 'ded-daq.ui'
        self.first_monocam = MonoCamera()
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
        if self.first_monocam.is_connected == True:
            self.first_monocam.start_camera()
        return

    def WindowVideoWorker(self):
        while self.first_monocam.is_connected:
            self.GVMonoCamera1.setImage(self.first_monocam.current_frame)
    
        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
