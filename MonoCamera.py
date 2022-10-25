from vimba import *
import time
class MonoCamera():

    def __init__(self) -> None:
        self.camera_id = '0'
        self.frame_rate = 100
        self.is_connected = False
        self.is_streaming = False
        self.camera_context = 0
        self.current_frame = 0
        self.frame_num = 0 
        self.worker_sleep = 0.05
        self.frame_timestamp = 0
        self.old_timestamp = 0
        self.exposure_time = -1.0
        self.vimba_alloc_mode = AllocationMode.AnnounceFrame
        return

    def detect(self):
        with Vimba.get_instance() as vi:
            cams = vi.get_all_cameras()
            if len(cams) == 1:
                print('id: {0} found'.format(cams[0].get_id()))
                self.camera_id = cams[0].get_id()
            else:
                print('error, {0}'.format(cams.__len__()))
    
    def start_camera(self):
        with Vimba.get_instance() as vi:
            with vi.get_camera_by_id(self.camera_id) as cam:
                self.frame_num = 0
                cam.start_streaming(self.frame_worker, 10, self.vimba_alloc_mode)
                self.is_connected = True
                self.is_streaming = True
                print('Done!')
        
    def stop_camera(self):
        with Vimba.get_instance() as vi:
            with vi.get_camera_by_id(self.camera_id) as cam:
                cam.stop_streaming()
                self.is_streaming = False
                
    def get_exposure(self):
        with Vimba.get_instance() as vi:
            with vi.get_camera_by_id(self.camera_id) as cam:
                float_feature = cam.get_feature_by_name('ExposureTime')
                self.exposure_time = float_feature.get()

                
                print(self.exposure_time)

    def frame_worker(self, monocam: Camera, frame: Frame):
        self.current_frame = frame.as_numpy_ndarray()
        self.old_timestamp = self.frame_timestamp
        self.frame_timestamp = frame.get_timestamp()
        self.frame_num += 1
        monocam.queue_frame(frame)
        return