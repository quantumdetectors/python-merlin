import logging
logger = logging.getLogger(__name__)

from Merlin.Shaper import MerlinImageReshaper

from connection.MERLIN_connection import ImageHeader
from MERLIN_Detector import MERLINDetector



class MerlinDataFrame:

    _quad_data = 'MQ1'
    _acq_header = 'HDR'


    def factory(body):
        if body.find(MerlinDataFrame._quad_data) > -1:
            return MerlinImage(body)

        elif body.find(MerlinDataFrame._acq_header) > -1:
            return MerlinAcqHeader(body)
        
        assert 0, 'Could not create MerlinFrame'


    factory = staticmethod(factory)



class MerlinAcqHeader(MerlinDataFrame):
    _map = {
        'Frames in Acquisition (Number)': 'to_acquire'
    }

    def __init__(self, body):
        for l in body.replace('HDR,', '').split('\n'):
            pairs = l.split(':')

            if len(pairs) > 1:
                if pairs[0] in self._map:
                    key = self._map[pairs[0]]
                    v = int(pairs[1])
                else:
                    key = pairs[0]
                    v = pairs[1].strip()

                setattr(self, key, v)

        logger.info('Parsed Acq Header acquiring {f} frames'.format(f=self.to_acquire))



class MerlinImage(MerlinDataFrame):
    _map = [
        'number',
        'offset',
        'chips',
        'width',
        'height',
    ]    

    _shaper = None

    def __init__(self, body):
        logger.debug('Creating image frame')
        params = body.split(',')

        # logger.debug('Params {p}'.format(p=params))
        for i,p in enumerate(params[1:]):
            if i < len(self._map):
                setattr(self, self._map[i], int(p))

        self.bit_depth = int(params[6][1:])
        self.raw = params[6][0] != 'U'

        self._shaper = MerlinImageReshaper(body, self)

        self.ImgHeader = ImageHeader(body[0:800])
        self.MerlinDet = MERLINDetector( body,  Image = 'img_', Display = 'OFF', fromFile = False,fromSTU = True,  header = self.ImgHeader)

        logger.debug('Parsed Frame {f}'.format(f=self.number))


    @property
    def data(self):
        if self._shaper:
            return self._shaper.data

