'''
    __main__: Main thread for the data acquisition software.
'''

from PyQt5 import QtWidgets, QtCore, QtGui, uic
import sys
import os

from MonoCamera import MonoCamera
from distutils.dep_util import newer
from PyQt5 import uic

class Ui(QtWidgets.QMainWindow):

    ui_path = 'ded-2.ui'
    py_file = 'ded-2.py'

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(self.ui_path, self)
        
        self.TBDiagnosticLog.setReadOnly(True)
        self.diagnostic_log = QtGui.QTextDocument()

        self.PBMono1Detect.clicked.connect(self.connect_mcam_1)
        self.PBMono1Enable.clicked.connect(self.enable_mcam_1)
        self.diagnostic_log.setPlainText('Startup Completed.\n')
        self.TBDiagnosticLog.setDocument(self.diagnostic_log)
        
        self.monocams = MonoCamera()
        self.show()
        return

    def connect_mcam_1(self):
        self.append_log('MONO1: Searching USB...')
        self.monocams.detect_devices()
        self.append_log('MONO1: Found device ID: {0}\tModel:{1}'.format(
            self.monocams.camera_id, self.monocams.camera_model
        ))
        self.append_log('MONO1: Exposure: {0}us\tGain: {1}dB'.format(
            self.monocams.exposure_value, self.monocams.amplifier_value
        ))
        self.PBMono1Enable.setEnabled(True)
        self.LEMono1ExposureTime.setText('{0:.1f}'.format(self.monocams.exposure_value))
        
        self.LEMono1AmplifierGain.setText('{0:.1f}'.format(self.monocams.amplifier_value))
        
        self.PBMono1Detect.setText('Redetect')
        self.PBMono1Enable.setText('Stream {0}'.format(self.monocams.camera_id))
        return

    def enable_mcam_1(self):
        self.GVMono1Preview.setEnabled(True)
        self.monocams.toggle_stream()
        if self.monocams.is_streaming:
            self.PBMono1Enable.setText('Stop {0}'.format(self.monocams.camera_id))
            self.append_log('MONO1: Camera has entered stream mode')
            self.append_log('MONO1: Enabling extra ui')
            self.LEMono1ExposureTime.setEnabled(True)
            self.LEMono1AmplifierGain.setEnabled(True)
            self.PBMono1SetExposure.setEnabled(True)
            self.PBMono1SetAmplifierGain.setEnabled(True)
            self.PBMono1AutoExposure.setEnabled(True)
            
        elif not self.monocams.is_streaming:
            self.PBMono1Enable.setText('Stream {0}'.format(self.monocams.camera_id))
            self.append_log('MONO1: Camera has left stream mode')
            self.LEMono1ExposureTime.setEnabled(False)
            self.LEMono1AmplifierGain.setEnabled(False)
            self.PBMono1SetExposure.setEnabled(False)
            self.PBMono1SetAmplifierGain.setEnabled(False)
            self.PBMono1AutoExposure.setEnabled(False)


    def append_log(self, string_to_append):
        cursor = QtGui.QTextCursor(self.diagnostic_log)
        cursor.movePosition(11)     ## 11 is enum value for selecting end of document
        cursor.insertText(string_to_append + '\n')

        self.TBDiagnosticLog.verticalScrollBar().setValue(
            self.TBDiagnosticLog.verticalScrollBar().maximum()
            )
        
        return

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()