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


mer = Merlin('10.0.0.100')

try:
    mer.connect()

    mer.set('ACQUISITIONTIME', 100)
    mer.set('NUMFRAMESTOACQUIRE', 1)
    mer.set('NUMFRAMESPERTRIGGER',1)
    
    
    time.sleep(1.0)
    mer.cmd('STARTACQUISITION')


    # This wont work if acq time is really short, as by the time the flag is set it gets unset again
    # Use a small sleep instead
    logging.info('Preparing Acquisition')
    while not mer.acquiring():
        time.sleep(0.001)


    logging.info('Acquiring')
    while mer.acquiring():
        time.sleep(0.1)
        logging.info('Got {f}/{t} frames'.format(f=mer.acquired(), t=mer.to_acquire()))

    logging.info('Finished')
    frames = mer.frames()
    logging.info('Finished {fr}'.format(fr=len(frames)))

#time.sleep(1.0)
    #print '  Now about to loop through frames ', frames
    for frame in frames :
        print ' Looping throught frames '
        plt.figure('Frame')
        plot = plt.imshow(frame.data, clim = (0, 4))
        plt.show()#

        for chips, img in frame._shaper.matrices.items():
            print ' Yeah man passsing by here '
            plt.figure(chips)
            plot = plt.imshow(img, clim = (0, 4))
            plt.show()

    print ' And I have gone by '

finally:
    mer.disconnect()



