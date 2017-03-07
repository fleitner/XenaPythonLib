import logging

import XenaModifier

logger = logging.getLogger(__name__)

class XenaStream:
    def __init__(self, xsocket, port, stream_id):
        self.xsocket = xsocket
        self.port = port
        self.sid = stream_id
        self.modifiers = {}

    def __del__(self):
        pass

    def stream_str(self):
        return "%d" % self.sid

    def __build_cmd_str(self, cmd, arg):
        return "%s %s [%d] %s" % (self.port.port_str(), cmd, self.sid, arg)

    def __sendCommand(self, cmd, arg):
        cmd_str = self.__build_cmd_str(cmd, arg)
        return self.xsocket.sendQueryVerify(cmd_str)

    def __sendQuery(self, cmd, arg):
        cmd_str = self.__build_cmd_str(cmd, arg)
        return self.xsocket.sendQuery(cmd_str)

    def set_stream_on(self):
        return self.__sendCommand('ps_enable', 'on')

    def set_stream_off(self):
        return self.__sendCommand('ps_enable', 'off')

    def set_stream_suppress(self):
        return self.__sendCommand('ps_enable', 'suppress')

    def get_stream_status(self):
        reply = self.__sendQuery('ps_enable', '?')
        return reply.split()[-1]

    def set_packet_limit(self, count):
        return self.__sendCommand('ps_packetlimit', '%d' % count)

    def disable_packet_limit(self):
        return self.__sendCommand('ps_packetlimit', '-1')

    def set_rate_fraction(self, fraction=1000000):
        return self.__sendCommand('ps_ratefraction', '%d' % fraction)

    def set_rate_pps(self, pps):
        return self.__sendCommand('ps_ratepps', '%d' % pps)

    def get_rate_pps(self):
        reply = self.__sendQuery('ps_ratepps', '?')
        return reply.split()[-1]

    def set_packet_header(self, header):
        return self.__sendCommand('ps_packetheader', '%s' % header)

    def set_packet_protocol(self, seg1, seg2='', seg3='', seg4='', seg5=''):
        seg_str = "%s" % seg1
        if seg2:
            seg_str += ' %s' % seg2
            if seg3:
                seg_str += ' %s' % seg3
                if seg4:
                    seg_str += ' %s' % seg4
                    if seg5:
                        seg_str += ' %s' % seg5
        return self.__sendCommand('ps_headerprotocol', '%s' % seg_str)

    def set_packet_length_fixed(self, min_len, max_len):
        cmd_str = "fixed %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_length_incrementing(self, min_len, max_len):
        cmd_str = "incrementing %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_length_butterfly(self, min_len, max_len):
        cmd_str = "butterfly %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_length_random(self, min_len, max_len):
        cmd_str = "random %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_length_mix(self, min_len, max_len):
        cmd_str = "mix %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_payload_pattern(self, hexdata):
        cmd_str = "pattern %s" % hexdata
        return self.__sendCommand('ps_payload', cmd_str)

    def set_packet_payload_incrementing(self, hexdata):
        cmd_str = "incrementing %s" % hexdata
        return self.__sendCommand('ps_payload', cmd_str)

    def set_packet_payload_prbs(self, hexdata):
        cmd_str = "prbs %s" % hexdata
        return self.__sendCommand('ps_payload', cmd_str)

    def disable_test_payload_id(self):
        return self.__sendCommand('ps_tpldid', -1)

    def set_test_payload_id(self, tpldid):
        return self.__sendCommand('ps_tpldid', '%d' % tpldid)

    def set_frame_csum_on(self):
        return self.__sendCommand('ps_insertfcs', 'on')

    def set_frame_csum_off(self):
        return self.__sendCommand('ps_insertfcs', 'off')

    def add_modifier(self):
        mid = len(self.modifiers.keys())
        tmids = mid + 1
        if not self.__sendCommand('ps_modifiercount', "%d" % tmids):
            logger.error("Failed to create a modifier")
            return -1

        modnew = XenaModifier.XenaModifier(self.xsocket, self.port, self, mid)
        self.modifiers[mid] = modnew
        return modnew

    def get_modifier(self, module, modifier_id):
        if self.modifiers.has_key(modifier_id):
            return self.modifiers[modifier_id]
        return None

    def remove_modifier(self, modifier_id):
        logger.error("Operation not supported")
        return -1

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
