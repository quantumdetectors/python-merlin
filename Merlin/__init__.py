import Queue
import socket
import select
import errno
import time
import threading

import logging
logger = logging.getLogger(__name__)

from Merlin.Frame import MerlinDataFrame, MerlinAcqHeader


class Merlin:
    _host = '127.0.0.1'

    _data_port = 6342
    _cmd_port = 6341

    _buffer_size = 4096

    _connected = False
    _acquired = 0

    _header = 'MPX'
    _num_digits = 10


    def __init__(self, host=None):
        if host:
            self._host = host

        self._data_queue = Queue.Queue()
        self._data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._data_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._cmd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._running = threading.Event()
        self._acquiring = threading.Event()
        self._acquired_lock = threading.Lock()


    def connect(self):
        logger.info('Connecting to cmd and data sockets')
        self._cmd_socket.connect((self._host, self._cmd_port))
        self._data_socket.connect((self._host, self._data_port))
        self._connected = True

        self._running.set()
        self._thread = threading.Thread(target=self._read_data)
        self._thread.daemon = True
        self._thread.start()

        # Give a bit of time for socket connection
        time.sleep(1)


    def _send(self, message):
        self._cmd_socket.sendall(message)
        resp = self._cmd_socket.recv(self._buffer_size)
        logger.debug('Response: {resp}'.format(resp=resp))

        return resp


    def _parse_response(self, resp):
        parts = resp.split(',')
        msgs = ['Command OK', 'System Busy', 'Unrecognised Command', 'Param out of range']

        rc = int(parts[5]) if parts[2] == 'GET' else int(parts[4])
        if rc > 0:
            raise Exception(msgs[rc])

        if parts[2] == 'GET':
            return parts[4]


    def _create_cmd(self, type, cmd, value=None):
        string = ''
        if value is not None:
            string = '{ty},{cmd},{val}'.format(ty=type,cmd=cmd,val=value)
        else:
            string = '{ty},{cmd},0'.format(ty=type,cmd=cmd)
        
        msg = '{hdr},{len},{st}'.format(hdr=self._header, len=str(len(string)+1).zfill(self._num_digits), st=string)

        logger.debug('Command: {cmd}'.format(cmd=msg))
        return msg


    def set(self, param, value):
        return self._parse_response(self._send(self._create_cmd('SET', param, value)))

    def get(self, param):
        return self._parse_response(self._send(self._create_cmd('GET', param)))

    def cmd(self, cmd):
        return self._parse_response(self._send(self._create_cmd('CMD', cmd)))


    def _grab_frame(self):
        header_char = 0
        leading = 0

        st = time.time()
        logger.debug('Finding frame start')
        while header_char < len(self._header):
            char = self._data_socket.recv(1)

            # logger.debug('{rc}, {hc}'.format(rc=char, hc=self._header[header_char]))
            if char == self._header[header_char]:
                header_char += 1
            else:
                header_char = 0
                leading += 1

        logger.debug('Found frame start, took {t:.5f}s'.format(t=time.time()-st))

        if leading > 0:
            logger.warning('{b} leading bytes of data discarded'.format(b=leading))


        st = time.time()
        logger.debug('Reading header')
        header = ''
        header_size = len(self._header) + self._num_digits + 2
        while len(header) < (header_size - len(self._header)):
            header += self._data_socket.recv((header_size - len(self._header)) - len(header))

        logger.debug('Read header, took {t:.5f}s'.format(t=time.time()-st))

        # logger.debug('Got header: {hdr}'.format(hdr=header))
        parts = header.split(',')
        body_length = int(parts[1]) - 1

        st = time.time()
        logger.debug('Reading body, {len} bytes'.format(len=body_length))
        body = ''
        iterations = 0
        while len(body) < body_length:
            body += self._data_socket.recv(body_length-len(body))
            iterations += 1


        if len(body) < body_length:
            logger.warning('Body truncated got {len} of {tot} bytes'.format(len=len(body), tot=body_length))

        logger.debug('Read body, took {t:.5f}s over {it} iterations'.format(t=time.time()-st, it=iterations))
        return MerlinDataFrame.factory(body)



    def _read_data(self):
        logger.debug('Running Data Task')
        while self._running.is_set():
            if self._data_socket is not None:
                # logger.debug('Data task looping')

                ready = select.select([self._data_socket], [], [], 0.5)
                # print 'ready', ready
                if ready[0]:
                    logger.debug('Data waiting in socket')

                    frame = self._grab_frame()
                    if frame:
                        if isinstance(frame, MerlinAcqHeader):
                            self._start_time = time.time()
                            with self._acquired_lock:
                                self._to_acquire = frame.to_acquire

                            self._acquiring.set()

                            with self._acquired_lock:
                                self._acquired = 0

                            # Discard any old frames on new acq
                            with self._data_queue.mutex:
                                self._data_queue.queue.clear()

                        else:
                            with self._acquired_lock:
                                self._acquired = frame.number

                            self._data_queue.put(frame)

                            if frame.number == self._to_acquire:
                                self._acquiring.clear()
                                dur = time.time() - self._start_time
                                logger.info('Took {sec:.2f}s, {fps:.2f}fps'.format(sec=dur,fps=self._to_acquire/dur))




    def disconnect(self):
        if self._running.is_set():
            self._running.clear()
            self._thread.join()

        if self._connected:
            self._data_socket.close()
            self._cmd_socket.close()
            self._connected = False


    def acquiring(self):
        return self._acquiring.is_set()


    def to_acquire(self):
        with self._acquired_lock:
            return self._to_acquire


    def acquired(self):
        with self._acquired_lock:
            return self._acquired


    def frames(self):
        frames = []
        for _ in range(self._data_queue.qsize()):
            frames.append(self._data_queue.get_nowait())

        return frames
