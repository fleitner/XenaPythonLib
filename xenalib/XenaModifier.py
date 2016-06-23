import logging

logger = logging.getLogger(__name__)
class XenaModifier:
    def __init__(self, xsocket, port, stream, modifier_id):
        self.xsocket = xsocket
        self.port = port
        self.stream = stream
        self.mid = modifier_id

    def __del__(self):
        pass

    def __build_cmd_str(self, cmd, arg):
        return "%s %s [%s,%d] %s" % (self.port.port_str(), cmd,
                                     self.stream.stream_str(),
                                     self.mid, arg)

    def __sendCommand(self, cmd, arg):
        cmd_str = self.__build_cmd_str(cmd, arg)
        return self.xsocket.sendQueryVerify(cmd_str)

    def __sendQuery(self, cmd, arg):
        cmd_str = self.__build_cmd_str(cmd, arg)
        return self.xsocket.sendQuery(cmd_str)

    def set_modifier(self, headerpos, headermask, action='inc', repeat=1):
        if action != 'inc' and action != 'dec' and action != 'random':
            logger.error('set_modified: invalid action: %s', action)
            return -1

        if headermask > 0xffffffff:
            logger.error('set_modified: invalid mask: %x', headermask)
            return -1

        arg_str = "%d 0x%08X %s %d" % (headerpos, headermask, action, repeat)
        return self.__sendCommand('ps_modifier', arg_str)

    def set_modifier_range(self, start, step, stop):
        arg_str = "%d %d %d" % (start, step, stop)
        return self.__sendCommand('ps_modifierrange', arg_str)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
