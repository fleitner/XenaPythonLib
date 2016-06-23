import os
import time
import threading
import logging

logger = logging.getLogger(__name__)
class KeepAliveThread(threading.Thread):
    def __init__(self, basesocket, interval = 10):
        threading.Thread.__init__(self)
        self.message = ''
        self.nr_sent = 0
        self.basesocket = basesocket
        self.interval = interval
        self.finished = threading.Event()
        self.setDaemon(True)
        logger.debug("Initiated")

    def get_nr_sent(self):
        return self.nr_sent

    def stop (self):
        logger.debug("Stopping")
        self.finished.set()
        self.join()

    def run (self):
        while not self.finished.isSet():
            self.finished.wait(self.interval)
            logger.debug("Pinging")
            self.basesocket.sendQuery(self.message)
            self.nr_sent += 1



def testsuite():
    import sys
    import BaseSocket

    hostname = "127.0.0.1"
    port = 22
    interval = 2
    test_result = False
    logging.basicConfig(level=logging.DEBUG)

    s = BaseSocket.BaseSocket(hostname, port, 1)
    print "Setting dummy mode"
    s.set_dummymode(True)
    print "Connecting to %s port %d" % ( hostname, port)
    s.connect()
    if s.is_connected():
        print "Connected"
        keep_alive_thread = KeepAliveThread(s, interval)
        print "Starting Keep Alive Thread"
        keep_alive_thread.start()
        time.sleep(3 * interval)
        keep_alive_thread.stop()
        nr_sent = keep_alive_thread.get_nr_sent()
        if nr_sent > 3 and nr_sent < 5:
            keep_alive_thread.stop()
            del keep_alive_thread
            del s
            test_result = True

    if test_result:
        print "All tests succeed"
        sys.exit(0)
    else:
        print "Fail, please review the output"
        sys.exit(-1)


if __name__ == '__main__':
    testsuite()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
