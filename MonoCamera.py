from threading import Thread
import time
from vimba import Vimba, Camera, AllocationMode, Frame, FrameHandler    

class MonoCamera():

    def __init__(self) -> None:
        self.camera_id = ''
        self.exposure_value = -1
        self.amplifier_value = -1
        self.camera_model = ''
        self.current_frame = ''
        self.current_timestamp = ''
        self.is_streaming = False
        self.feature_request = False
        self.feature_data = {'name': '', 'value': ''}
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
            pass
        print('returning frame')
        mcam.queue_frame(mframe)