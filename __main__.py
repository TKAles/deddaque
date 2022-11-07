"""
    __main__: Main thread for the data acquisition software.
"""

import copy
import time
from threading import Thread

from PyQt5 import QtWidgets, QtGui, uic
import sys
from MonoCamera import MonoCamera
import queue
import pyqtgraph as pg


class Ui(QtWidgets.QMainWindow):
    ui_path = 'ded-2.ui'
    py_file = 'ded-2.py'

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(self.ui_path, self)

        # Setup the output log
        self.TBDiagnosticLog.setReadOnly(True)
        self.diagnostic_log = QtGui.QTextDocument()
        # UI event callbacks are here
        self.PBMono1Detect.clicked.connect(self.connect_mcam_1)
        self.PBMono1Enable.clicked.connect(self.enable_mcam_1)
        self.PBMono1AutoExposure.clicked.connect(self.trigger_mcam_1_aelock)
        self.PBMono1SetAmplifierGain.clicked.connect(self.mcam1_set_amplifier)
        # encoder queue and other junk
        self.encoder_queue_size = 5000  # num of frames to store before dumping to disk
        self.encoder_queue_one = queue.Queue(maxsize=self.encoder_queue_size)
        # First camera object and its viewbox, imageitem & worker thread for display
        self.monocam_one = MonoCamera()
        self.monocam_one_viewbox = pg.ViewBox()
        self.mcam1_imageitem = pg.ImageItem()
        self.mcam1_preview_update_thread = Thread()
        self.show()
        # Log setup and frame_data dict definition
        self.diagnostic_log.setPlainText('Startup Completed.\n')
        self.TBDiagnosticLog.setDocument(self.diagnostic_log)
        self.frame_data = {'old_ts': 0, 'current_ts': 0, 'delta_ts': 0, 'fps': 0.0}

        return

    def connect_mcam_1(self):
        """
        connect_mcam_1: UI event handler to look for a AlliedVision camera on
                        the usb bus.
        """

        self.append_log('MONO1: Looking at USB connections.')
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
            self.LEMono1AmplifierGain.setText('{0:.1f}'.format(self.monocam_one.amplifier_value))
            self.PBMono1Detect.setText('Redetect')
            self.PBMono1Enable.setText('Stream {0}'.format(self.monocam_one.camera_id))
            self.append_log('MONO1: Creating ViewBox and ImageItem for display.')
            # Create the viewbox and place and imageitem into it so you can display the 
            # camera image. GraphicsView is locked to 25% of native resolution of CCD.

            self.GVMono1Preview.setCentralItem(self.monocam_one_viewbox)
            self.monocam_one_viewbox.addItem(self.mcam1_imageitem)

            self.append_log('MONO1: Detection done for {0}'.format(self.monocam_one.camera_id))
        except IndexError:
            self.append_log('MONO1: IndexError! There were no cameras found. Check the USB cable and try again!')
            index_error_box = QtWidgets.QMessageBox()
            index_error_box.about(self, 'VIMBA IndexError!',
                                  'There were no cameras found. Check the USB cable and try scanning again.')
            index_error_box.setIcon(QtWidgets.QMessageBox.Critical)
            index_error_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
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
            self.LEMono1AmplifierGain.setEnabled(True)
            self.PBMono1SetAmplifierGain.setEnabled(True)
            self.PBMono1AutoExposure.setEnabled(True)
            self.mcam1_preview_update_thread = Thread(
                    target=self.mcam1_graphics_worker)
            self.mcam1_preview_update_thread.start()

        elif not self.monocam_one.is_streaming:
            # If the streaming mode hasn't started, start it.
            self.PBMono1Enable.setText('Stream {0}'.format(self.monocam_one.camera_id))
            self.append_log('MONO1: Camera has left stream mode')
            self.append_log('MONO1: Disabling extra UI controls')
            self.LEMono1AmplifierGain.setEnabled(False)
            self.PBMono1SetAmplifierGain.setEnabled(False)
            self.PBMono1AutoExposure.setEnabled(False)
            self.monocam_one.is_streaming = False
            self.mcam1_preview_update_thread.join(1.0)

    def trigger_mcam_1_aelock(self):
        """
        trigger_mcam_1_aelock: Commands the connected camera to do
                                a single shot AutoExposure. Updates UI with
                                new ExposureTime in microseconds.
        """
        if self.monocam_one.is_streaming:
            self.monocam_one.set_camera_feature('ExposureAuto', 'Once')
            time.sleep(0.2)

            self.monocam_one.set_camera_feature('ExposureAuto', 'Off')

    def mcam1_set_amplifier(self):
        if self.monocam_one.is_streaming:
            self.monocam_one.set_camera_feature('Gain',
                                                self.LEMono1AmplifierGain.text())
        return

    def mcam1_graphics_worker(self):
        """
        mcam1_graphics_worker: Updates the ImageItem that is used to display the
                               CCD preview. Should be started as it's own thread.
        """
        while self.monocam_one.is_streaming:
            while self.monocam_one.frame_queue.empty():
                time.sleep(0.01)
            new_frame = self.monocam_one.frame_queue.get_nowait()
            new_metadata = self.monocam_one.timestamp_queue.get(block=True)
            # Copy into the encoder queue
            if self.encoder_queue_one.not_full and self.is_recording_to_disk:
                print('adding frame. Queue size {0}'.format(
                    self.encoder_queue_one.qsize()
                ))
                self.encoder_queue_one.put_nowait(new_frame)

            if self.encoder_queue_one.full() and self.is_recording_to_disk:
                self.append_log('ENC1: Encoder Queue is Full!! Dumping!')
                self.encoder_queue_one.queue.clear()

            # Calculate the timestamp information and shuffle the timestamps
            # along with the FPS
            self.frame_data['old_ts'] = copy.copy(self.frame_data['current_ts'])
            self.frame_data['current_ts'] = new_metadata
            self.frame_data['delta_ts'] = (self.frame_data['current_ts'] - self.frame_data['old_ts']) / 10**6
            self.frame_data['fps'] = 1000.0 / self.frame_data['delta_ts']
            self.LMono1TimeDelta.setText('{0:.2f}ms'
                                         .format(self.frame_data['delta_ts']))
            self.LMono1FPS.setText('{0:.2f}fps'.format(self.frame_data['fps']))

            self.mcam1_imageitem.setImage(new_frame)

    def append_log(self, string_to_append):
        """
        append_log(string_to_append): Function that adds to the end of
                                      the QTextDocument that is the session log.
                                      string_to_append - a string you want to add.
        """
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
        """
        cleanup: Runs when the QApplication is closed. Tries to close any threads if open,
                 silently catches the exceptions if there are no threads.
        """
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
