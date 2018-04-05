import sys
import time
import logging

from . import KeepAliveThread
from . import XenaPort

logger = logging.getLogger(__name__)


class XenaManager:
    def __init__(self, xsocket, owner, password='xena'):
        self.xsocket = xsocket
        self.ports = {}
        self.keep_alive_thread = None
        # FIXME: This is really weird.  The initialization can fail, which
        # is bad practice.  But rather than do the refactor at the moment,
        # we just set keep_alive_thread to None, and check for it in
        # __del__
        if self.logon(password):
            logger.info("Logged successfully")
        else:
            logger.error("Failed to log in")
            sys.exit(-1)

        self.set_owner(owner)
        self.keep_alive_thread = KeepAliveThread.KeepAliveThread(self.xsocket)
        self.keep_alive_thread.start()

    def __del__(self):
        for pkey in list(self.ports.keys()):
            port_del = self.ports[pkey]
            port_del.reset()
            port_del.release()
            del port_del

        self.ports = {}
        if self.keep_alive_thread:
            self.keep_alive_thread.stop()
        # FIXME: race
        time.sleep(1)
        self.xsocket.sendQueryVerify('c_logoff')
        if self.keep_alive_thread:
            del self.keep_alive_thread

    def _compose_str_command(self, cmd, argument):
        command = cmd + ' \"' + argument + '\"'
        return command

    def logon(self, password):
        command = self._compose_str_command('c_logon', password)
        return self.xsocket.sendQueryVerify(command)

    def set_owner(self, owner):
        # owner is limited to 8 chars
        command = self._compose_str_command('c_owner', owner[:8])
        return self.xsocket.sendQueryVerify(command)

    def add_port(self, module, port):
        if (module, port) in self.ports:
            logger.error("Adding duplicated port")
            return

        port_new = XenaPort.XenaPort(self.xsocket, module, port)
        if not port_new.reserve():
            del port_new
            return None

        port_new.reset()
        self.ports[(module, port)] = port_new
        return port_new

    def get_port(self, module, port):
        if (module, port) in self.ports:
            return self.ports[(module, port)]
        return None

    def remove_port(self, module, port):
        if (module, port) not in self.ports:
            logger.error("Deleting unknown port")
            return

        port_del = self.ports.pop((module, port))
        port_del.reset()
        port_del.release()
        del port_del

    def set_module_port(self, module_port):
        self.xsocket.sendCommand(module_port)

    def load_script(self, filename):
        pass


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
