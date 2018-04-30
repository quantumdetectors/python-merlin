import numpy as np

import logging
logger = logging.getLogger(__name__)

# https://stackoverflow.com/questions/48344108/convert-data-faster-from-byte-to-3d-numpy-array

# dtype = [('headers', np.void, frame_header_size), ('frames', '<u2', (height, width))]
# mmap = np.memmap(filename, dtype, offeset=main_header_size)
# array = mmap['frames']


class MerlinImageReshaper:

    _data = None

    def __init__(self, body, offset, bitdepth, raw=False):
        pass



