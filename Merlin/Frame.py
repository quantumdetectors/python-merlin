import logging
logger = logging.getLogger(__name__)

from Merlin.Shaper import MerlinImageReshaper
from Merlin.Header import ImageHeader
#from connection.MERLIN_connection import ImageHeader
from MERLIN_Detector import MERLINDetector


class MerlinDataFrame:

    _quad_data = 'MQ1'
    _acq_header = 'HDR'
    #_moduleName = 'None'


    def factory(body):
        if body.find(MerlinDataFrame._quad_data) > -1:
            return MerlinImage(body)

        elif body.find(MerlinDataFrame._acq_header) > -1:
            return MerlinAcqHeader(body)
        
        assert 0, 'Could not create MerlinFrame'


    factory = staticmethod(factory)


#  Put though test
class MerlinAcqHeader(MerlinDataFrame):
    _map = {
        'Frames in Acquisition (Number)': 'to_acquire',
        #'Chip ID':  'chipNames',
        #'Assembly Size (1X1, 2X2)': 'Layout',
        #'Gain':    'gain'
    }
    _Name = None

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

                setattr(self, key.replace(' ','_'), v)


        self._get_chips()
        logger.info('Parsed Acq Header acquiring {f} frames'.format(f=self.to_acquire))


    # Gets the number of chips and
    def _get_chips(self) :

        Chips = ['Chip1','Chip2','Chip3','Chip4']
        self.Name = {}
        
        
        modlist = self.Chip_ID.split(',')
        module=''

        #print ' moooofList ', modlist
        for i,chip in enumerate(modlist):
            if '-' not in chip:
                if i==0:
                    module= chip
                else:
                    module = module + '-'+chip
                self.Name[Chips[i]] =  chip

        setattr(self, '_moduleName', module)


class MerlinImage(MerlinDataFrame):
    _map = [
        'number',
        'offset',
        'chips',
        'width',
        'height',
    ]    

    _shaper = None
    #_matrices = None

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
        
        self._get_chips()

    @property
    def data(self):
        if self._shaper:
            return self._shaper.data


    # Gets the number of chips and
    def _get_chips(self) :
    
        self.chips = []
        if '1x1' in self.ImgHeader.params['detLayout']:
            self.chips = ['Chip1']

        else :
            self.chips = ['Chip1','Chip2','Chip3','Chip4']

