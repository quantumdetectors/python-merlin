import numpy as np

import logging
logger = logging.getLogger(__name__)


#  Edu ------ > Making changes to add RAw data mode here
from Merlin.Header import ImageHeader
#from connection.MERLIN_connection import ImageHeader

class MerlinImageReshaper:

    data = None

    def __init__(self, body, frame):
        
        
        self.imgheader =  ImageHeader(body[0:900])
        
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


        if self.imgheader.params['bitdepth'] in bm:
            dt = bm[self.imgheader.params['bitdepth'] ]
        else:
            raise Exception('Unknown bitdepth')

        logger.debug('Creating np array of {bd}bit depth'.format(bd=self.imgheader.params['bitdepth']))



        data = np.frombuffer(body, dtype=dt, offset=self.imgheader.params['Offset'])
        
        if frame.raw :
            if self.imgheader.params['bitdepth'] == 24:
                self.data = self._reshape_raw24(data)
                
            if self.imgheader.params['bitdepth'] == 1:
                data = np.unpackbits(data)
                self.data = data.reshape((self.imgheader.params['NpixY'] , self.imgheader.params['NpixX']))

            # Fixing those shifted columns
####### This is failing me
            #self._raw_col_reshape()
                
        else :
            self.data = data.reshape((self.imgheader.params['NpixY'] , self.imgheader.params['NpixX']))





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
        
        
        Npiy = self.imgheader.params['NpixY']   # self.PixelYdim
        Npix = self.imgheader.params['NpixX']   # self.PixelYdim
        
        if self.imgheader.params['bitdepth'] == 24:
            Npix = self.imgheader.params['NpixX']/2   #self.PixelXdim/2
        
        if self.imgheader.params['bitdepth'] in col:
            COLS = col[self.imgheader.params['bitdepth'] ]
        else:
            raise Exception('Unknown bitdepth')


        for yi in range(0, Npiy):                   #    Loop over raws
            for ix in range(0, Npix/COLS):             #    Loop over columns

                for subcol in range(0, COLS/2):
            
                    xi = COLS*ix
                    end = COLS - 1 - subcol
                    
                    #print ' xi ', xi ,'  end ', end
                    old = self.data[yi][xi+subcol]
                    self.data[yi][xi+subcol] = self.data[yi][xi + end]
                    self.data[yi][xi + end] = old

