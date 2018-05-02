import numpy as np

import logging
logger = logging.getLogger(__name__)


class MerlinImageReshaper:

    data = None

    def __init__(self, body, frame):
        if frame.raw:
            pass

        else:
            bm = {
                8: '>u1',
                16: '>u2',
                32: '>u4',
            }

            if frame.bit_depth in bm:
                dt = bm[frame.bit_depth]
            else:
                raise Exception('Unknown bitdepth')

            logger.debug('Creating np array of {bd}bit depth'.format(bd=frame.bit_depth))

            self.data = np.frombuffer(body, dtype=dt, offset=frame.offset).reshape((frame.width, frame.height))

            # Merlin data is upside down...
            self.data = np.flip(self.data, 0)
