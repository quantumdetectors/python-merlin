import time

from Merlin import Merlin

import logging
logging.basicConfig(
    # level=logging.DEBUG,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)


mer = Merlin('192.168.160.162')

try:
    mer.connect()

    mer.set('ACQUISITIONTIME', 1)
    mer.set('NUMFRAMESTOACQUIRE', 1000)
    mer.cmd('STARTACQUISITION')

    # This wont work if acq time is really short, as by the time the flag is set it gets unset again
    # Use a small sleep instead
    logging.info('Preparing Acquisition')
    while not mer.acquiring():
        time.sleep(0.1)


    logging.info('Acquiring')
    while mer.acquiring():
        time.sleep(2)
        logging.info('Got {f}/{t} frames'.format(f=mer.acquired(), t=mer.to_acquire()))

    frames = mer.frames()
    logging.info('Finished {fr}'.format(fr=len(frames)))


finally:
    mer.disconnect()



