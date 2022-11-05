from threading import Thread
import time
from vimba import Vimba, Camera, AllocationMode, Frame, FrameHandler    
import numpy as np
from copy import copy

class MonoCamera():

    def __init__(self) -> None:
        self.camera_id = ''
        self.exposure_value = -1
        self.amplifier_value = -1
        self.camera_model = ''
        self.current_frame = np.zeros((5,5))
        self.current_timestamp = 0
        self.previous_timestamp = 0
        self.timestamp_delta = 0
        self.fps_value = 0
        self.is_streaming = False
        self.feature_request = False
        self.feature_data = {'name': '', 'set': False, 'value': ''}
        self.buffer_size = 10
        
        pass

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
                                        buffer_count=10,
                                        allocation_mode=AllocationMode.AnnounceFrame)
                while self.is_streaming:
                    time.sleep(0.1)

    def stream_stop(self):
        self.is_streaming = False
        return

    def stream_callback(self, mcam: Camera, mframe: Frame):
        if self.feature_request:
            self.feature_request = False
            if self.feature_data['set']:
                mcam.get_feature_by_name(self.feature_data['name']).set(self.feature_data['value'])
            elif not self.feature_data['set']:
                self.feature_data['value'] = mcam.get_feature_by_name(self.feature_data['name'])
            pass

        self.previous_timestamp = copy(self.current_timestamp)
        self.current_frame = copy(mframe.as_numpy_ndarray())
        self.current_timestamp = copy(mframe.get_timestamp())
        self.timestamp_delta = (self.current_timestamp - self.previous_timestamp) / (10**6)
        self.fps_value = 1000.0 / self.timestamp_delta
        mcam.queue_frame(mframe)