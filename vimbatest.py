from vimba import *
import numpy as np
import pyqtgraph as pg

def handlerfunction(monocam: Camera, frame: Frame):
    print('grabbing frame')
    pg.show(frame.as_numpy_ndarray())
    monocam.queue_frame(frame)
    return

with Vimba.get_instance() as vi:
    cams = vi.get_all_cameras()
    with cams[0] as camera:
        print('Found ID:{0}\tModel:{1}'.format(camera.get_id(), camera.get_model()))
        print('Starting stream...')
        camera.start_streaming(handlerfunction, 10, AllocationMode.AllocAndAnnounceFrame)

