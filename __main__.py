from enum import auto
from functools import partial
import os
import sys
import time
import ctypes as ct
from turtle import update
from PyQt5 import QtWidgets, uic, QtCore
import libirimager
import pyqtgraph as pg
from vimba import *
ui_path = './deddaq.ui'

class Ui(QtWidgets.QMainWindow):

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(ui_path, self)
        self.ir_camera_object = libirimager.ThermalCamera()
        self.ir_running = False
        self.mono_running = False
        self.mono_frame = ''
        self.le_irimager_usb_sn.setText('21114001')
        self.b_toggle_usb_conn.clicked.connect(self.connect_ir)
        self.b_mono_toggle.clicked.connect(self.autoconnect_mono)
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.ir_worker)
        self.update_timer.timeout.connect(self.mono_worker)
        self.update_timer.start()
        self.cbox_hw_temp_range.currentIndexChanged.connect(self.temperature_combobox_changed)
        self.populate_combobox()
        self.blank_metadata()
        self.gfx_thermal.hideAxis('bottom')
        self.gfx_thermal.hideAxis('left')
        self.gfx_monoc.hideAxis('bottom')
        self.gfx_monoc.hideAxis('left')
        self.show()

    def autoconnect_mono(self):
        if self.mono_running == False:
            self.b_mono_toggle.setChecked(True)
            self.b_mono_toggle.setText('Connected')
            self.mono_running = True

        elif self.mono_running == True:
            self.b_mono_toggle.setChecked(False)
            self.b_mono_toggle.setText('Autodetect')
            self.mono_running = False

        
    def connect_ir(self):
        if self.ir_running == False:
            self.b_toggle_usb_conn.setText('Disconnect')
            self.ir_instance = libirimager.ThermalCamera()
            self.ir_instance.initialize()
            time.sleep(0.5)
            f_thermal, f_metadata = self.ir_instance.get_image()
            self.imgItem = pg.ImageItem(f_thermal)
            self.gfx_thermal.addItem(self.imgItem)
            self.gfx_thermal.hideAxis('bottom')
            self.gfx_thermal.hideAxis('left')
            self.ir_running = True
            #self.update_timer.start()
            return
        else:
            self.b_toggle_usb_conn.setText('Connect via USB')
            self.ir_instance.disconnect()
            #self.update_timer.stop()
            self.imgItem.clear()
            self.ir_running = False
            return

    def blank_metadata(self):
        self.l_counter.setText('--')
        self.l_counterHW.setText('--')
        self.l_flagstate.setText('--')
        self.l_tempbox.setText('--')
        self.l_tempflag.setText('--')
        self.l_timestamp.setText('--')
        return

    def ir_worker(self):
        if self.ir_running == True:
            self.thermal_data, self.meta_data = self.ir_instance.get_image()
            self.imgItem.setImage(self.thermal_data)
            self.l_counter.setText('{0}'.format(self.meta_data.counter))
            self.l_counterHW.setText('{0}'.format(self.meta_data.counterHW))
            match self.meta_data.flagState:
                case 0:
                    self.l_flagstate.setText('Open')
                case 1:
                    self.l_flagstate.setText('Closed')
                case _:
                    self.l_flagstate.setText('{0}'.format(self.meta_data.flagState))

            self.l_tempbox.setText('{0:0.1f}C'.format(self.meta_data.tempBox))
            self.l_tempflag.setText('{0:0.1f}C'.format(self.meta_data.tempFlag))
            self.l_timestamp.setText('{0:0.3f}s'.format(self.meta_data.timestamp / 10000000.0))
        return

    def populate_combobox(self):
        self.cbox_hw_temp_range.addItem('-20 to 100')
        self.cbox_hw_temp_range.addItem('0 to 250')
        self.cbox_hw_temp_range.addItem('150 to 900')
        self.cbox_hw_temp_range.setCurrentIndex(0)
        return

    def temperature_combobox_changed(self):
        current_index = self.cbox_hw_temp_range.currentIndex()
        match current_index:
            case 0:
                t_min = -20
                t_max = 100
            case 1:
                t_min = 0
                t_max = 250
            case 2:
                t_min = 150
                t_max = 900
        
        if self.ir_running == True:
            ret = self.ir_instance.IRLib.evo_irimager_set_temperature_range(
                                            ct.c_uint(t_min), ct.c_uint(t_max))
            if ret != 0:
                print('Temperature change request failed.')
            elif ret == 0:
                print('Hardware temperature limits changed to {0} to {1} degC'.format(t_min, t_max))

    def mono_worker(self):
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras()
            while self.mono_running == True:
                with cams[0] as cam:
                    cam.ExposureAuto.set('Once')
                    mono_frame = cam.get_frame()
                    self.mono_frame = mono_frame.as_numpy_ndarray()
                    self.MonoImgItem = pg.ImageItem(self.mono_frame)
                    self.MonoImgItem.setImage(self.mono_frame, autoLevels=True)
                    self.gfx_monoc.addItem(self.MonoImgItem)
    
            
                


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
    