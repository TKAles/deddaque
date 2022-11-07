import queue
import time
from copy import copy
from threading import Thread

import numpy as np
from vimba import *


class MonoCamera():

    def __init__(self) -> None:

        self.camera_thread = None
        self.camera_id = ''  # String to connect to camera over usb
        self.exposure_value = -1  # Exposure in microseconds
        self.amplifier_value = -1  # Amplifier Gain in dB
        self.camera_model = ''  # Model of camera reported by vimba
        self.is_streaming = False
        self.buffer_size = 10

        self.frame_queue = queue.Queue()
        self.timestamp_queue = queue.Queue()

    def detect_devices(self):
        with Vimba.get_instance() as vi:
            cams = vi.get_all_cameras()
            with cams[0] as camera:
                self.camera_id = camera.get_id()
                self.camera_model = camera.get_model()
                self.exposure_value = camera.get_feature_by_name('ExposureTime').get()  # type: ignore
                self.amplifier_value = camera.get_feature_by_name('Gain').get()  # type: ignore

    def toggle_stream(self):
        if self.is_streaming:
            self.stream_stop()
            self.camera_thread.join()
        elif not self.is_streaming:
            self.camera_thread = Thread(target=self.stream_start)
            self.camera_thread.start()

    def stream_start(self):
        self.is_streaming = True
        with Vimba.get_instance() as vi:
            with vi.get_camera_by_id(self.camera_id) as camera:
                camera.start_streaming(handler=self.stream_callback,
                                       buffer_count=20,
                                       allocation_mode=AllocationMode.AnnounceFrame)
                while self.is_streaming:
                    time.sleep(0.1)

    def stream_stop(self):
        self.is_streaming = False
        return

    def get_frame_rate(self):
        return self.get_camera_feature('AcquisitionFrameRate')

    def set_camera_feature(self, feature_name, feature_value):
        with Vimba.get_instance() as vi:
            with vi.get_camera_by_id(self.camera_id) as cam:
                cam.get_feature_by_name(feature_name).set(feature_value)

    def get_camera_feature(self, feature_name):
        with Vimba.get_instance() as vi:
            with vi.get_camera_by_id(self.camera_id) as cam:
                return cam.get_feature_by_name(feature_name).get()

    def stream_callback(self, mcam: Camera, mframe: Frame):

        self.frame_queue.put(copy(mframe.as_numpy_ndarray()))
        self.timestamp_queue.put(copy(mframe.get_timestamp()))

        mcam.queue_frame(mframe)
