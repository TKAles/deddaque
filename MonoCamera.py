from vimba import *

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
                self.exposure_value = camera.get_feature_by_name('ExposureTime').get()
                self.amplifier_value = camera.get_feature_by_name('Gain').get()

    def stream_callback(self, mcam: Camera, mframe: Frame):
        if self.feature_request:
            mcam.
        mcam.queue_frame(mframe)