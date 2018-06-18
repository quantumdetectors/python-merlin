import time
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.cm as cm

from Merlin import Merlin

import logging
logging.basicConfig(
    # level=logging.DEBUG,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)


mer = Merlin('10.0.0.222')

try:
    
    Flag = True
    counter = 0
    
    mer.connect()
  

    logging.info(' Here buffer should be empty')

    mer.set('ACQUISITIONTIME', 100)
    mer.set('NUMFRAMESTOACQUIRE', 1070)
    mer.set('NUMFRAMESPERTRIGGER',107)
    mer.set('TRIGGERSTART',5)
   
    time.sleep(1.0)
    mer.cmd('STARTACQUISITION')
    logging.info('Acqu started')
    

    # This wont work if acq time is really short, as by the time the flag is set it gets unset again
    # Use a small sleep instead
    logging.info('Preparing Acquisition')
    
    logging.info('Soft trigger sent')
    mer.cmd('SOFTTRIGGER')
    
    while not mer.acquiring():
        time.sleep(0.1)
        logging.info('Sleeping')


    logging.info('Acquiring')
    while mer.acquiring():
        
        logging.info('Got {f}/{t} frames'.format(f=mer.acquired(), t=mer.to_acquire()))
        
        print mer.acquired() , '     ' , mer.acquired()/107.0 ,'      ' , int(mer.acquired()/107.)
        testing = mer.acquired()/107.
        intT = int(testing)
        if ( testing - intT) == 0 :
            mer.cmd('SOFTTRIGGER')
            logging.info('Got {f}/{t} frames'.format(f=mer.acquired(), t=mer.to_acquire()))
            logging.info('Sending Softrigger')

        time.sleep(0.2)


    frames = mer.frames()
    logging.info('Finished {fr}'.format(fr=len(frames)))


#for frame in frames :
#        plot = plt.imshow(frames[0].data)
#        plt.show()#

#        for ch, mat in frame.MerlinDet.matrices.items():
#            imgplot = plt.imshow(mat ,origin='lower', cmap = cm.jet,interpolation='nearest', aspect='auto', clim = (0, 4094))
#            plt.show()




finally:
    mer.disconnect()



