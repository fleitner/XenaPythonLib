import socket
import sys
import logging

class BaseSocket:

    def __init__(self, hostname, port = 5025, timeout = 1):
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self.connected = False
        self.sock = None
        self.dummymode = False

    def __del__(self):
        self.disconnect()

    def is_connected(self):
        return self.connected;

    def __connect(self):
        logging.debug("BaseSocket: connecting")
        if self.dummymode:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            logging.error("Fail to create a socket: host %s:%d, error:%s",
                          self.hostname, self.port, msg[0])
            return False

        self.sock.settimeout(self.timeout)

        try:
	       self.sock.connect((self.hostname, self.port))
        except socket.error, msg:
            logging.error("Fail to connect to host %s:%d, error:%s",
                          self.hostname, self.port, msg[0])
            return False

        return True

    def connect(self):
        if self.connected:
            logging.error("BaseSocket: connect() on a connected socket")
            return

        if self.__connect():
            self.connected = True

    def disconnect(self):
        logging.debug("BaseSocket: disconnecting")
        if not self.connected:
            return

        self.connected = False
        if not self.dummymode:
            self.sock.close()

    def sendCommand(self, cmd):
        logging.debug("BaseSocket: sendCommand(%s)", cmd)
        if not self.connected:
            logging.error("BaseSocket: sendCommand() on a disconnected socket")
            return -1

        if self.dummymode:
            return 0

        try:
            if not self.sock.send(cmd + '\n'):
                return -1
        except socket.error, msg:
            logging.error("Fail to send a cmd, error:%s\n", msg[0])
            self.disconnect()
            return -1

        return 0

    def readReply(self):
        if not self.connected:
            logging.error("BaseSocket: readReply() on a disconnected socket")
            return -1

        if self.dummymode:
            return '<OK>'

        reply = self.sock.recv(1024)
        if reply.find("---^") != -1:
            logging.debug("BaseSocket: receiving a syntax error message")
            # read again the syntax error msg
            reply = self.sock.recv(1024)

        logging.debug("BaseSocket: reply message(%s)", reply.strip('\n'))
        return reply

    def sendQuery(self, query):
        logging.debug("BaseSocket: sendQuery(%s)", query)
        self.sendCommand(query)
        reply = self.readReply()
        return reply

    def set_keepalives(self):
        logging.debug("BaseSocket: setting socket keepalive")
        if self.dummymode:
            return

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    def set_dummymode(self, enable=True):
        logging.debug("BaseSocket: dummy mode was %s, request to %s",
                      self.dummymode, enable)

        if self.dummymode is enable:
            return

        was_connected = self.is_connected()
        logging.warning("BaseSocket: enabling dummy mode")
        self.disconnect()
        if enable:
            self.dummymode = True
        else:
            self.dummymode = False

        if was_connected:
            self.connect()



def testsuite():
    hostname = "127.0.0.1"
    port = 22

    test_result = False
    dummy_test_result = False
    logging.basicConfig(level=logging.DEBUG)
    s = BaseSocket(hostname, port, 1)
    print "Connecting to %s port %d" % ( hostname, port)
    s.connect()
    if s.is_connected():
        print "Internal Status: connected"
        s.set_keepalives()
        print "keepalive set"
        s.disconnect()
        print "disconnected"
        print "BasicSocket test succeed"
        test_result = True
    else:
        print "Error: not connected"

    print "Setting dummy mode"
    s.set_dummymode(True)
    print "Connecting to %s port %d" % ( hostname, port)
    s.connect()
    if s.is_connected():
        print "Connected, sending query"
        reply = s.sendQuery("any string")
        if reply == '<OK>':
            print "Reply is correct, sending command"
            s.sendCommand("SYNC")
            reply = s.readReply()
            if reply == '<OK>':
                print "Reply is correct, disconnecting"
                dummy_test_result = True
                print "Dummy test succeed"
            s.disconnect()
        else:
            print "Error: reply is wrong"
    else:
        print "Error: not connected"

    del s
    if test_result and dummy_test_result:
        print "All tests succeed"
        sys.exit(0)
    else:
        print "Fail, please review the output"
        sys.exit(-1)

if __name__ == '__main__':
    testsuite()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
