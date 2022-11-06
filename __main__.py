'''
    __main__: Main thread for the data acquisition software.
'''

from multiprocessing.util import is_abstract_socket_namespace
import time
from tkinter import OFF
from PyQt5 import QtWidgets, QtCore, QtGui, uic
import sys
import os
import numpy as np
from MonoCamera import MonoCamera
from distutils.dep_util import newer
from PyQt5 import uic
import pyqtgraph as pg

class Ui(QtWidgets.QMainWindow):

    ui_path = 'ded-2.ui'
    py_file = 'ded-2.py'

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(self.ui_path, self)

        self.image_worker_timer = QtCore.QTimer()
        self.image_worker_timer.timeout.connect(self.mcam1_graphics_worker)
        # Setup the output log
        self.TBDiagnosticLog.setReadOnly(True)
        self.diagnostic_log = QtGui.QTextDocument()
        # UI event callbacks are here
        self.PBMono1Detect.clicked.connect(self.connect_mcam_1)
        self.PBMono1Enable.clicked.connect(self.enable_mcam_1)
        self.PBMono1AutoExposure.clicked.connect(self.trigger_mcam_1_aelock)
        self.PBMono1SetExposure.clicked.connect(self.mcam1_set_exposure)
        self.PBMono1SetAmplifierGain.clicked.connect(self.mcam1_set_amplifier)
        self.monocam_one = MonoCamera()
        self.show()
        self.diagnostic_log.setPlainText('Startup Completed.\n')
        self.TBDiagnosticLog.setDocument(self.diagnostic_log)
        
        return

    def connect_mcam_1(self):
        '''
        connect_mcam_1: UI event handler to look for a AlliedVision camera on 
                        the usb bus.
        '''

        self.append_log('MONO1: Searching USB...')
        try:
            self.monocam_one.detect_devices()
            self.append_log('MONO1: Found device ID: {0}\tModel:{1}'.format(
                self.monocam_one.camera_id, self.monocam_one.camera_model
            ))
            self.append_log('MONO1: Exposure: {0}us\tGain: {1}dB'.format(
                self.monocam_one.exposure_value, self.monocam_one.amplifier_value
            ))
            # Enable the stream button and grab the exposure time + amp gain values off the camera
            self.PBMono1Enable.setEnabled(True)
            self.LEMono1ExposureTime.setText('{0:.1f}'.format(self.monocam_one.exposure_value))
            self.LEMono1AmplifierGain.setText('{0:.1f}'.format(self.monocam_one.amplifier_value))
            self.PBMono1Detect.setText('Redetect')
            self.PBMono1Enable.setText('Stream {0}'.format(self.monocam_one.camera_id))
            self.append_log('MONO1: Creating ViewBox and ImageItem for display.')
            self.mcam1_viewbox = pg.ViewBox()
            self.mcam1_imageitem = pg.ImageItem()
            self.GVMono1Preview.setCentralItem(self.mcam1_viewbox)
            self.mcam1_viewbox.addItem(self.mcam1_imageitem)
            self.append_log('MONO1: Detection done for {0}'.format(self.monocam_one.camera_id))
        except IndexError:
                self.append_log('MONO1: IndexError! There were no cameras found. Check the USB cable and try again!')
        return

    def enable_mcam_1(self):
        self.GVMono1Preview.setEnabled(True)
        self.monocam_one.toggle_stream()
        if self.monocam_one.is_streaming:
            # If the camera is in streaming mode after the toggle
            # update the UI and add to the log
            self.PBMono1Enable.setText('Stop {0}'.format(self.monocam_one.camera_id))
            self.append_log('MONO1: Camera has entered stream mode')
            self.append_log('MONO1: Enabling extra ui')
            self.LEMono1ExposureTime.setEnabled(True)
            self.LEMono1AmplifierGain.setEnabled(True)
            self.PBMono1SetExposure.setEnabled(True)
            self.PBMono1SetAmplifierGain.setEnabled(True)
            
            self.PBMono1AutoExposure.setEnabled(True)
            self.image_worker_timer.start(16)
            
        elif not self.monocam_one.is_streaming:
            # If the streaming mode hasn't started, start it.

            self.PBMono1Enable.setText('Stream {0}'.format(self.monocam_one.camera_id))
            self.append_log('MONO1: Camera has left stream mode')
            self.append_log('MONO1: Disabling extra UI controls')
            self.LEMono1ExposureTime.setEnabled(False)
            self.LEMono1AmplifierGain.setEnabled(False)
            self.PBMono1SetExposure.setEnabled(False)
            self.PBMono1SetAmplifierGain.setEnabled(False)
            self.PBMono1AutoExposure.setEnabled(False)
            self.image_worker_timer.stop()


    def trigger_mcam_1_aelock(self):
        '''
        trigger_mcam_1_aelock: Commands the connected camera to do 
                                a single shot AutoExposure. Updates UI with
                                new ExposureTime in microseconds.
        '''
        if self.monocam_one.is_streaming:
            self.monocam_one.set_camera_feature('ExposureAuto', 'Once')
            time.sleep(0.2)
            self.LEMono1ExposureTime.setText('{0:.2f}'.format(
                self.monocam_one.get_camera_feature('ExposureTime')
            ))
            self.monocam_one.set_camera_feature('ExposureAuto', 'Off')

    def mcam1_set_exposure(self):
        if self.monocam_one.is_streaming:
            self.monocam_one.set_camera_feature('ExposureTime', self.LEMono1ExposureTime.text())
        return

    def mcam1_set_amplifier(self):
        if self.monocam_one.is_streaming:
            self.monocam_one.set_camera_feature('Gain', self.LEMono1AmplifierGain.text())
        return
    
    def mcam1_graphics_worker(self):
        frame_is_all_zeros = not np.any(self.monocam_one.current_frame)
        if frame_is_all_zeros:
            pass
        else:
            self.mcam1_imageitem = pg.ImageItem(self.monocam_one.current_frame)
            self.mcam1_viewbox.clear()
            self.mcam1_viewbox.addItem(self.mcam1_imageitem)
            self.LMono1TimeDelta.setText('{0:0.4f}ms'.format(self.monocam_one.timestamp_delta))
            self.LMono1FPS.setText('{0:.2f} fps'.format(self.monocam_one.fps_value))
        return
        
    def append_log(self, string_to_append):
        '''
        append_log(string_to_append): Function that adds to the end of 
                                      the QTextDocument that is the session log.
                                      string_to_append - a string you want to add.
        '''
        # Need to create a TextCursor to traverse the document
        cursor = QtGui.QTextCursor(self.diagnostic_log)
        # Move to the end of the document and append the string passed in with a newline.
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(string_to_append + '\n')
        # Scroll so that the bottom (most recent) messages are visible.
        self.TBDiagnosticLog.verticalScrollBar().setValue(
            self.TBDiagnosticLog.verticalScrollBar().maximum()
            )
        return

    def cleanup(self):
        '''
        cleanup: Runs when the QApplication is closed. Tries to close any threads if open, 
                 silently catches the exceptions if there are no threads.
        '''
        try:
            self.monocam_one.is_streaming = False
            self.monocam_one.camera_thread.join()
        except:
            pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.aboutToQuit.connect(window.cleanup)
    app.exec()