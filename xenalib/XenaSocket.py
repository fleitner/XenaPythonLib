import os
import sys
import time
import logging
import threading

import BaseSocket

logger = logging.getLogger(__name__)

class XenaSocket:
    reply_ok = '<OK>'

    def __init__(self, hostname, port = 22611, timeout = 5):
        logger.debug("Initializing")
        self.bsocket = BaseSocket.BaseSocket(hostname, port, timeout)
        self.access_semaphor = threading.Semaphore(1)

    def set_dummymode(self, enable = True):
        logger.debug("Enabling dummymode")
        self.bsocket.set_dummymode(enable)

    def is_connected(self):
        return self.bsocket.is_connected()

    def connect(self):
        logger.debug("Connect()")
        self.access_semaphor.acquire()
        self.bsocket.connect()
        self.bsocket.set_keepalives()
        self.access_semaphor.release()
        cted = self.is_connected()
        if cted:
            logger.info("Connected")
        else:
            logger.error("Fail to connect")
        return cted

    def disconnect(self):
        logger.debug("Disconnect()")
        self.access_semaphor.acquire()
        self.bsocket.disconnect()
        self.access_semaphor.release()

    def __del__(self):
        self.access_semaphor.acquire()
        self.bsocket.disconnect()
        self.access_semaphor.release()

    def sendCommand(self, cmd):
        logger.debug("sendCommand(%s)", cmd)
        if not self.is_connected():
            logger.warning("sendCommand on a disconnected socket")
            return

        self.access_semaphor.acquire()
        self.bsocket.sendCommand(cmd)
        self.access_semaphor.release()
        logger.debug("sendCommand(%s) returning", cmd)

    def __sendQueryReplies(self, cmd):
        # send the command followed by cmd SYNC to find out
        # when the last reply arrives.
        self.access_semaphor.acquire()
        self.bsocket.sendCommand(cmd.strip('\n'))
        self.bsocket.sendCommand('SYNC')
        replies = []
        msg = self.bsocket.readReply()
        while True:
            if '\n' in msg:
                (reply, msgleft) = msg.split('\n', 1)
                # check for syntax problems
                if reply.rfind('Syntax') != -1:
                    logger.warning("Multiline: syntax error")
                    self.access_semaphor.release()
                    return []

                if reply.rfind('<SYNC>') == 0:
                    logger.debug("Multiline EOL SYNC message")
                    self.access_semaphor.release()
                    return replies

                logger.debug("Multiline reply: %s", reply)
                replies.append(reply + '\n')
                msg = msgleft
            else:
                # more bytes to come
                msgnew = self.bsocket.readReply()
                msg = msgleft + msgnew

    def __sendQueryReply(self, cmd):
        self.access_semaphor.acquire()
        reply = self.bsocket.sendQuery(cmd).strip('\n')
        self.access_semaphor.release()
        return reply

    def sendQuery(self, cmd, multilines=False):
        logger.debug("sendQuery(%s)", cmd)
        if not self.is_connected():
            logger.warning("sendQuery on a disconnected socket")
            return

        if multilines:
            replies = self.__sendQueryReplies(cmd)
            logger.debug("sendQuery(%s) -- Begin", cmd)
            for l in replies:
                logger.debug("%s", l)
            logger.debug("sendQuery(%s) -- End", cmd)
            return replies

        reply = self.__sendQueryReply(cmd)
        logger.debug("sendQuery(%s) reply(%s)", cmd, reply)
        return reply

    def sendQueryVerify(self, cmd):
        logger.debug("sendQueryVerify(%s)", cmd)
        if not self.is_connected():
            logger.warning("sendQueryVerify on a disconnected socket")
            return False

        resp = self.__sendQueryReply(cmd)
        if resp == self.reply_ok:
            logger.debug("SendQueryVerify(%s) Succeed", cmd)
            return True
        logger.debug("SendQueryVerify(%s) Fail", cmd)
        return False



def testsuite():
    import KeepAliveThread
    import XenaSocket

    hostname = "10.16.46.156"
    port = 22611
    interval = 2
    test_result = False
    logging.basicConfig(level=logging.DEBUG)
    s = XenaSocket.XenaSocket(hostname, port)
    s.set_dummymode(True)
    s.connect()
    if s.is_connected():
        print "Connected"
        keep_alive_thread = KeepAliveThread.KeepAliveThread(s, interval)
        print "Starting Keep Alive Thread"
        keep_alive_thread.start()
        time.sleep(1)
        print "Sending a command"
        s.sendCommand("Hello World!")
        print "Sending a query"
        reply = s.sendQuery("Xena Command")
        if reply != '<OK>':
            print "sendQuery failed"
            sys.exit(-1)

        print "Sending a query with check enabled"
        if not s.sendQueryVerify("Xena Command"):
            print "sendQuery failed"
            sys.exit(-1)

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
