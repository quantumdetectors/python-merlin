import numpy as np

import logging
logger = logging.getLogger(__name__)


#  Edu ------ > Making changes to add RAw data mode here
from Merlin.Header import ImageHeader
#from connection.MERLIN_connection import ImageHeader

class MerlinImageReshaper:

    data = None                 # main image matrix
    matrices = None             # individual chip matrices
    _isRaw = False
    _raw_process = False        # flag for avoiding processing in raw mode

    def __init__(self, body, frame):
        
        
        self.imgheader =  ImageHeader(body[0:900])
        self._isRaw = frame.raw
        
        if frame.raw:
            bm = {
                1: '>u1',
                6: '>u1',
                12: '>u2',
                24: '>u2',
            }
    
        else:
            bm = {
                1: '>u1',
                6: '>u1',
                12: '>u2',
                24: '>u4',
            }

        self.setProcessRaw()
        
        if self.imgheader.params['bitdepth'] in bm:
            dt = bm[self.imgheader.params['bitdepth'] ]
        else:
            raise Exception('Unknown bitdepth')

        logger.debug('Creating np array of {bd}bit depth'.format(bd=self.imgheader.params['bitdepth']))



        data = np.frombuffer(body, dtype=dt, offset=self.imgheader.params['Offset'])
        
        if self._isRaw:
            if self.imgheader.params['bitdepth'] == 24:
                self.data = self._reshape_raw24(data)
                
            elif self.imgheader.params['bitdepth'] == 1:
                data = np.unpackbits(data)
                self.data = data.reshape((self.imgheader.params['NpixY'] , self.imgheader.params['NpixX']))
        
            else :
                self.data = data.reshape((self.imgheader.params['NpixY'] , self.imgheader.params['NpixX']))
            
            # if I want to avoind processing time I can turn the _raw_process flag to false
            if self._raw_process:
                self._raw_col_reshape()
                    
        else :
            self.data = data.reshape((self.imgheader.params['NpixY'] , self.imgheader.params['NpixX']))


        self._chip_matrix_arrange()



    # oprerations for 24 bit. To be optimised
    def _reshape_raw24(self,data):
        
        imgs = np.hsplit(data,2)
        Npiy = self.imgheader.params['NpixY']   # self.PixelYdim
        Npix = self.imgheader.params['NpixX']/2   #self.PixelXdim/2
        img_raw = np.empty([Npiy , Npix],  dtype ='uint32')


        img_raw = np.empty([Npiy , Npix],  dtype ='uint32')
        most_sig_img = imgs[0].reshape( Npiy, Npix)
        least_sig_img = imgs[1].reshape(Npiy, Npix)

        # Can I do this better/faster ?
        for iy in range(0,Npiy):
            for ix in range(0,Npix):
                img_raw[iy][ix] = most_sig_img[iy][ix]*4096 + least_sig_img[iy][ix]

        return img_raw


    def _raw_col_reshape(self):
        
        col = {
            1: 64,
            6:  8,
            12: 4,
            24: 4,
        }
        
        bm = {
            1: '>u1',
            6: '>u1',
            12: '>u2',
            24: '>u2',
        }
        
        if self.imgheader.params['bitdepth'] in bm:
            dt = bm[self.imgheader.params['bitdepth'] ]
        else:
            raise Exception('Unknown bitdepth')
        
        Npiy = self.imgheader.params['NpixY']   # self.PixelYdim
        Npix = self.imgheader.params['NpixX']   # self.PixelYdim
        
        if self.imgheader.params['bitdepth'] == 24:
            Npix = self.imgheader.params['NpixX']/2   #self.PixelXdim/2
        
        if self.imgheader.params['bitdepth'] in col:
            COLS = col[self.imgheader.params['bitdepth'] ]
        else:
            raise Exception('Unknown bitdepth')

        data = np.empty([Npiy , Npix],  dtype =dt)

        for yi in range(0, Npiy):                   #    Loop over raws
            for ix in range(0, Npix/COLS):             #    Loop over columns

                for subcol in range(0, COLS/2):
            
                    xi = COLS*ix
                    end = COLS - 1 - subcol
                    
                    #print ' xi ', xi ,'  end ', end
                    old = self.data[yi][xi+subcol]
                    data[yi][xi+subcol] = self.data[yi][xi + end]
                    data[yi][xi + end] = old

        self.data = data




    def _chip_matrix_arrange(self):
        #arranging raw data matrices
    
        # List with names of chips
        self.chips = ['Chip1']
        # Directory of lists key = chip name, [sum, matrix]
        self.matrices = {}
    
        if ('1x1' in self.imgheader.params['detLayout']):
            self.chips = ['Chip1']
            # Chip matrix for single
            self.matrices['Chip1'] = self.data

        else:
            self.chips = ['Chip1','Chip2','Chip3','Chip4']
            #print ' here we are with this many chips', self.chips

            if self._isRaw  or ('Nx1' in  self.imgheader.params['detLayout']):
                img_chips = np.hsplit(self.data,4)
                
                if '2x2' in self.imgheader.params['detLayout'] :
                    
                    self.matrices['Chip1'] = img_chips[3]
                    self.matrices['Chip2'] = img_chips[2]
                    self.matrices['Chip3'] = np.flip( np.flip( img_chips[1],1) , 0 )
                    self.matrices['Chip4'] = np.flip( np.flip( img_chips[0],1) , 0 )
            
                    a = np.hstack((self.matrices['Chip1'],self.matrices['Chip2']))
                    b = np.hstack((self.matrices['Chip3'],self.matrices['Chip4']))
        
                    self.data = np.vstack((a,b))
        
                elif 'Nx1' in self.imgheader.params['detLayout'] and  self._isRaw :
                    
                    
                    self.matrices['Chip1'] = img_chips[3]
                    self.matrices['Chip2'] = img_chips[2]
                    self.matrices['Chip3'] = img_chips[1]
                    self.matrices['Chip4'] = img_chips[0]
            
                    a = np.hstack((self.matrices['Chip1'],self.matrices['Chip2']))
                    b = np.hstack((self.matrices['Chip3'],self.matrices['Chip4']))
            
                    self.data = np.hstack((a,b))
        
                else :
                    
                    self.matrices['Chip1'] = img_chips[0]
                    self.matrices['Chip2'] = img_chips[1]
                    self.matrices['Chip3'] = img_chips[2]
                    self.matrices['Chip4'] = img_chips[3]
        

            elif '2x2' in self.imgheader.params['detLayout'] :
                img_chips = np.hsplit(self.data,2)
                
                v_left  = np.vsplit(img_chips[0], 2)
                v_right = np.vsplit(img_chips[1], 2)
                
                self.matrices['Chip1'] = v_left[0]
                self.matrices['Chip2'] = v_right[0]
                self.matrices['Chip3'] = v_left[1]
                self.matrices['Chip4'] = v_right[1]

                



    
    


    def setProcessRaw(self):
        self._raw_process = True
