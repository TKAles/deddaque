from vimba import *
import time
class MonoCamera():

    def __init__(self) -> None:
        self.camera_id = '0'
        self.frame_rate = 100
        self.is_connected = False
        self.camera_context = 0
        self.current_frame = 0
        self.frame_num = 0 
        self.worker_sleep = 0.05
        self.frame_timestamp = 0
        self.old_timestamp = 0
        self.vimba_alloc_mode = AllocationMode.AnnounceFrame
        return

    def detect(self):
        with Vimba.get_instance() as vi:
            cams = vi.get_all_cameras()
            if len(cams) == 1:
                print('id: {0} found'.format(cams[0].get_id()))
                self.camera_id = cams[0].get_id()
    
    def start_camera(self):
        with Vimba.get_instance() as vi:
            with vi.get_camera_by_id(self.camera_id) as cam:
                cam.start_streaming(self.frame_worker, 10, self.vimba_alloc_mode)
                self.is_connected = True
                while self.is_connected:
                    time.sleep(self.worker_sleep)
                cam.stop_streaming()
        
    def frame_worker(self, monocam: Camera, frame: Frame):
        self.current_frame = frame.as_numpy_ndarray()
        self.old_timestamp = self.frame_timestamp
        self.frame_timestamp = frame.get_timestamp()
        self.frame_num += 1
        monocam.queue_frame(frame)
        return