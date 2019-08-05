import socket
import select
from time import time
import sys
import re   
from time import * 
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import struct



class ImageHeader:
    
    def __init__(self, header_str='',dac=-1,TH='0'):
        ''' LALALA. If DAC=1 if we are using this from DAC scan. It does not seem as if
        we are getting data aproproately from TCP as the DAC that is running is set to zero'''


        list = header_str.split(',')
        
        self.params = {}
        chips = []
    
        if len(list) > 13:
            self._Params(list, dac)

    
    def _Params(self, list, dac):
        
        
        
        self.params['acqNumber'] = int(list[1])
        self.params['Offset'] = int(list[2])
        self.params['Nchips'] = int(list[3])
        self.params['NpixX'] = int(list[4])
        self.params['NpixY'] = int(list[5])
        self.params['dataType'] = list[6]
        self.params['detLayout'] = list[7]
        self.params['TimeStamp'] = list[9]
        self.params['FrameTime'] = float(list[10])    # in secodns
        self.params['Counter'] = int(list[11])    # in secodns
        self.params['Colour'] = int(list[12])    # in secodns
        self.params['Gain'] = int(list[13])    # in secodns


        self.params['Threshold_DACS'] = {}
        self.params['DACs'] = {}
        self.params['Thresholds'] = {}
        
        if '1x1' in self.params['detLayout'] :
            chips = ['Chip1']
        
        if ('2x2' in self.params['detLayout'] ) or ('Nx1G' in self.params['detLayout'] ) or ('Nx1' in self.params['detLayout'] ):
            chips = ['Chip1','Chip2','Chip3','Chip4']

        intdict = {}
        
        counter = 15
        
        if 'U' in self.params['dataType']:
            #print " Getting through here "
            self.params['Thresholds'] = list[14:22]
           
            
            counter = 22
            
            for i, chip in enumerate(chips):

                intdict[chip] = []
                initial = counter
                
                for j in  range(initial, initial+28):
                    
                    item = list[j]

                    if int(j) == initial :
                        intdict[chip].append(item)
                    else :
                        intdict[chip].append(int(item))
                
                    counter+=1
                
                self.params['DACs'][chip] = intdict[chip]
                self.params['Threshold_DACS'][chip] = intdict[chip][1:9]
            
                # trick for DAC scans via TCP ip
                if dac > -1: self.params['Threshold_DACS'][chip][self.params['Counter']] = dac

        self.params['head_extens'] = list[counter]
        self.params['TimeStamp_ext'] = list[counter+1]
        self.params['FrameTimens'] = list[counter+3]
        self.params['bitdepth'] = int(list[counter+3])




    def Print(self):
        for param, value in self.params.items():
            print " - INFO  ************ : ", param , " = ", value


        return

