
# Class for connecting to optris xi 400 thermal
# camera. Code taken from:
# https://uia.brage.unit.no/uia-xmlui/bitstream/handle/11250/2826476/MAS500%20Nilsen.pdf
import ctypes as ct
import numpy as np

class ThermalCamera:

    def __init__(self):
        self.IRLib = ct.CDLL('./libirimager.dll')
        self.xmlpath = ct.c_char_p(b'21114001.xml')
        self.formatpath = ct.c_char_p(b'./')
        self.logpath = ct.c_char_p(b'./thermal')
        self.camera_sn = ct.c_ulong()
        self.metadata = ThermalMetadata();

        # camera configuration parameters
        self.optical_data = {'focal_length': 0.0127,
                             'true_w': 382,
                             'true_h': 288}

        self.thermal_w = ct.c_int()
        self.thermal_h = ct.c_int()
        self.palette_w = ct.c_int()
        self.palette_h = ct.c_int()

    def initialize(self):
        # Initialize over usb and check for errors.
        retv = self.IRLib.evo_irimager_usb_init(self.xmlpath,
                                                self.formatpath, self.logpath)
        if retv != 0:
            print('Error during initialization of library. Check configuration.')
            exit()  # bail}|
        # Get the SN of the connected camera.
        self.IRLib.evo_irimager_get_serial(ct.byref(self.camera_sn))
        self.IRLib.evo_irimager_get_thermal_image_size(
                ct.byref(self.thermal_w), ct.byref(self.thermal_h))
        self.IRLib.evo_irimager_get_palette_image_size(
                ct.byref(self.palette_w), ct.byref(self.palette_h))
        
        return

    def get_image(self):
        # Preallocate containers for the 'thermal' image and the 'palette' image
        #                                (h, w, 1)                (h, w, 3)

        thermal_container = np.zeros([self.thermal_h.value * self.thermal_w.value],
                            dtype=np.ushort)
        thermal_ptr = thermal_container.ctypes.data_as(ct.POINTER(ct.c_ushort))
        # Create an empty metadata struct to copy into
        metadata = ThermalMetadata()
        self.IRLib.evo_irimager_get_thermal_image_metadata(ct.byref(self.thermal_w), ct.byref(self.thermal_h), 
                                                           thermal_ptr, ct.byref(metadata))
        return thermal_container.reshape((self.thermal_h.value, self.thermal_w.value)), metadata
        
    def disconnect(self):
        self.IRLib.evo_irimager_terminate()
        return
    

# Create class for metadata struct
class ThermalMetadata(ct.Structure):
    _fields_ = [
                ('counter', ct.c_uint),
                ('counterHW', ct.c_uint),
                ('timestamp', ct.c_longlong),
                ('timestampMedia', ct.c_longlong),
                ('flagState', ct.c_int),
                ('tempChip', ct.c_float),
                ('tempFlag', ct.c_float),
                ('tempBox', ct.c_float)
                ]
