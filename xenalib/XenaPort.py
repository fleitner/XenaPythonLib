import time
import logging
import XenaStream

logger = logging.getLogger(__name__)

class XenaPort:
    def __init__(self, xsocket, module, port):
        self.xsocket = xsocket
        self.module = module
        self.port = port
        self.streams = {}
        self.pt_stats = {}
        self.pr_stats = {}

    def __del__(self):
        pass

    def port_str(self):
        return "%s/%s" % (self.module, self.port)

    def __build_cmd_str(self, cmd):
        return "%s %s" % (self.port_str(), cmd)

    def __sendCommand(self, cmd):
        cmd_str = self.__build_cmd_str(cmd)
        return self.xsocket.sendQueryVerify(cmd_str)

    def __sendQuery(self, cmd):
        cmd_str = self.__build_cmd_str(cmd)
        return self.xsocket.sendQuery(cmd_str)

    def __sendQueryReplies(self, cmd):
        cmd_str = self.__build_cmd_str(cmd)
        return self.xsocket.sendQuery(cmd_str, True)

    def reserve(self):
        return self.__sendCommand('p_reservation reserve')

    def relinquish(self):
        return self.__sendCommand('p_reservation relinquish')

    def release(self):
        return self.__sendCommand('p_reservation release')

    def reset(self):
        return self.__sendCommand('p_reset')

    def start_traffic(self):
        logger.info("Port(%s): Starting traffic", self.port_str())
        return self.__sendCommand('p_traffic on')

    def stop_traffic(self):
        logger.info("Port(%s): Stopping traffic", self.port_str())
        return self.__sendCommand('p_traffic off')

    def get_traffic_status(self):
        reply = self.__sendQuery('p_traffic ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False
        return status

    def __pack_stats(self, parms, start, fields = [ 'bps', 'pps', 'bytes',
                     'packets' ]):
        data = {}
        i = 0
        for column in fields:
            data[column] = int(parms[start + i])
            i += 1

        return data

    def __pack_txextra_stats(self, parms, start):
        fields = [ 'arprequests', 'arpreplies', 'pingrequests', 'pingreplies',
                   'injectedfcs', 'injectedseq', 'injectedmis', 'injectedint',
                   'injectedtid', 'training' ]
        return self.__pack_stats(parms, start, fields)

    def __pack_rxextra_stats(self, parms, start):
        fields = [ 'fcserrors', 'pauseframes', 'arprequests', 'arpreplies',
                   'pingrequests', 'pingreplies', 'gapcount', 'gapduration' ]
        return self.__pack_stats(parms, start, fields)

    def __pack_tplds_stats(self, parms, start):
        data = {}
        i = 0
        for val in range(start, len(parms) - start):
            data[i] = int(parms[val])
            i += 1
        return data

    def __pack_tplderrors_stats(self, parms, start):
        fields = [ 'dummy', 'seq', 'mis', 'pld' ]
        return self.__pack_stats(parms, start, fields)

    def __pack_tpldlatency_stats(self, parms, start):
        fields = [ 'min', 'avg', 'max', '1sec' ]
        return self.__pack_stats(parms, start, fields)

    def __pack_tpldjitter_stats(self, parms, start):
        fields = [ 'min', 'avg', 'max', '1sec' ]
        return self.__pack_stats(parms, start, fields)

    def __parse_stats(self, stats_list):
        storage = {}
        for line in stats_list:
            parms = line.split()
            if parms[1] == 'PT_TOTAL':
                storage['pt_total'] = self.__pack_stats(parms, 2)
            elif parms[1] == 'PR_TOTAL':
                storage['pr_total'] = self.__pack_stats(parms, 2)
            elif parms[1] == 'PT_NOTPLD':
                storage['pt_notpld'] = self.__pack_stats(parms, 2,)
            elif parms[1] == 'PR_NOTPLD':
                storage['pr_notpld'] = self.__pack_stats(parms, 2,)
            elif parms[1] == 'PT_EXTRA':
                storage['pt_extra'] = self.__pack_txextra_stats(parms, 2)
            elif parms[1] == 'PR_EXTRA':
                storage['pr_extra'] = self.__pack_rxextra_stats(parms, 2)
            elif parms[1] == 'PR_PFCSTATS':
                storage['pr_pfcstats'] = self.__pack_rxextra_stats(parms, 2)
            elif parms[1] == 'PT_STREAM':
                entry_id = "pt_stream_%s" % parms[2].strip('[]')
                storage[entry_id] = self.__pack_stats(parms, 3)
            elif parms[1] == 'PR_TPLDS':
                tid_list = self.__pack_tplds_stats(parms, 2)
                if len(tid_list):
                    storage['pr_tplds'] = tid_list
            elif parms[1] == 'PR_TPLDTRAFFIC':
                if storage.has_key('pr_tpldstraffic'):
                    data = storage['pr_tpldstraffic']
                else:
                    data = {}
                entry_id = parms[2].strip('[]')
                data[entry_id] = self.__pack_stats(parms, 3)
                storage['pr_tpldstraffic'] = data
            elif parms[1] == 'PR_TPLDERRORS':
                if storage.has_key('pr_tplderrors'):
                    data = storage['pr_tplderrors']
                else:
                    data = {}
                entry_id = parms[2].strip('[]')
                data[entry_id] = self.__pack_tplderrors_stats(parms, 3)
                storage['pr_tplderrors'] = data
            elif parms[1] == 'PR_TPLDLATENCY':
                if storage.has_key('pr_tpldlatency'):
                    data = storage['pr_tpldlatency']
                else:
                    data = {}
                entry_id = parms[2].strip('[]')
                data[entry_id] = self.__pack_tpldlatency_stats(parms, 3)
                storage['pr_tpldlatency'] = data
            elif parms[1] == 'PR_TPLDJITTER':
                if storage.has_key('pr_tpldjitter'):
                    data = storage['pr_tpldjitter']
                else:
                    data = {}
                entry_id = parms[2].strip('[]')
                data[entry_id] = self.__pack_tpldjitter_stats(parms, 3)
                storage['pr_pldjitter'] = data
            elif parms[1] == 'PR_FILTER':
                if storage.has_key('pr_filter'):
                    data = storage['pr_filter']
                else:
                    data = {}
                entry_id = parms[2].strip('[]')
                data[entry_id] = self.__pack_stats(parms, 3)
                storage['pr_filter'] = data
            elif parms[1] == 'P_RECEIVESYNC':
                if parms[2] == 'IN_SYNC':
                    storage['p_receivesync' ] = { 'IN SYNC' : 'True' }
                else:
                    storage['p_receivesync' ] = { 'IN SYNC' : 'False' }
            else:
                logger.warning("Received unknown stats: %s", parms[1])

        return storage

    def clear_all_tx_stats(self):
        self.pt_stats = {}
        return self.__sendCommand('pt_clear')

    def dump_all_tx_stats(self):
        return self.pt_stats

    def grab_all_tx_stats(self):
        txstats_list = self.__sendQueryReplies('pt_all ?')
        if txstats_list:
            timestamp = time.time()
            txdata = self.__parse_stats(txstats_list)
        self.pt_stats[timestamp] = txdata

    def clear_all_rx_stats(self):
        self.pr_stats = {}
        return self.__sendCommand('pr_clear')

    def dump_all_rx_stats(self):
        return self.pr_stats

    def grab_all_rx_stats(self):
        rxstats_list = self.__sendQueryReplies('pr_all ?')
        if rxstats_list:
            timestamp = time.time()
            rxdata = self.__parse_stats(rxstats_list)
        self.pr_stats[timestamp] = rxdata

    def get_tpld_latency_stats(self, tid):
        tpldlat_tid = {}
        rxstats = self.__sendQuery('pr_tpldlatency [%d] ?' % tid)
        if rxstats:
            rxdata = self.__parse_stats([rxstats])
            tpldlat = rxdata['pr_tpldlatency']
            tpldlat_tid = tpldlat['%d' % tid]
        return tpldlat_tid

    def set_speed(self, mbitspersec=10000):
        speed = None
        if bitspersec == 'auto':
            speed = 'auto'
        elif bitspersec == 10000:
            speed = 'F10G'
        elif bitspersec == 1000:
            speed = 'F1G'
        else:
            logger.error("Port(%s): Unsupported port speed: %s",
                          self.port_str(), bitspersec)
            return -1

        logger.debug("Port(%s): Setting port speed: %s",
                      self.port_str(), bitspersec)

    def get_speed(self):
        reply = self.__sendQuery('p_speed ?')
        speed = reply.split()[-1]
        logger.debug("Port(%s): Got port speed: %s", self.port_str(), speed)
        return speed

    def set_autoneg_on(self):
        return self.__sendCommand('p_autonegselection on')

    def set_autoneg_off(self):
        return self.__sendCommand('p_autonegselection off')

    def get_autoneg_enabled(self):
        reply = self.__sendQuery('p_autonegselection ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        logger.debug("Port(%s): Got port autoneg: %s", self.port_str(), status)
        return status

    def get_tpld_errors_stats(self, tid):
        reply = self.__sendQuery('pr_tplderrors [%d] ?' % tid)
        stats = self.__pack_tplderrors_stats(reply.split(), 3)
        logger.debug("Port(%s): Stats dummy:%d, seq:%d, mis:%d, lpd=%d",
                      self.port_str(), stats['dummy'], stats['seq'],
                      stats['mis'], stats['pld'])
        return stats

    def get_total_errors_counter(self):
        reply = self.__sendQuery('p_errors ?')
        errors = int(reply.split()[-1])
        logger.debug("Port(%s): Got total errors: %d", self.port_str(), errors)
        return errors

    def set_tx_speed_reduction(self, parts_per_million):
        return self.__sendCommand('p_speedreduction %d' % parts_per_million)

    def get_tx_speed_reduction(self):
        reply = self.__sendQuery('p_speedreduction ?')
        ppm = int(reply.split()[-1])
        logger.debug("Port(%s): Tx speed reduction: %d", self.port_str(), ppm)
        return ppm

    def set_interframe_gap(self, minbytes = 20):
        return self.__sendCommand('p_interframegap %d' % minbytes)

    def get_interframe_gap(self):
        reply = self.__sendQuery('p_interframegap ?')
        gap = int(reply.split()[-1])
        logger.debug("Port(%s): Interframe gap: %d", self.port_str(), gap)
        return ppm

    def set_macaddr(self, macaddr = '04:F4:BC:2F:A9:80'):
        macaddrstr = ''.join(macaddr.split(':'))
        return self.__sendCommand('p_macaddress %s' % macaddrstr)

    def get_macaddr(self):
        reply = self.__sendQuery('p_macaddress ?')
        macstr = int(reply.split()[-1])
        macaddress =  "%s:%s:%s:%s:%s:%s" % (macstr[2:4], macstr[4:6],
                       macstr[6:8], macstr[8:10], macstr[10:12], macstr[12:14])
        logger.debug("Port(%s): Mac address: %s", self.port_str(), macaddress)
        return macaddress

    def set_ipaddr(self, ipaddr, subnet, gateway, wild='0.0.0.255'):
        cmd = 'p_ipaddress %s %s %s %s' % ( ipaddr, subnet, gateway, wild)
        return self.__sendCommand(cmd)

    def get_ipaddr(self):
        reply = self.__sendQuery('p_ipaddr ?')
        config_list = reply.split()
        wild = config_list[-1]
        gw = config_list[-2]
        subnet = config_list[-3]
        ipaddr = config_list[-4]
        logger.debug("Port(%s): Port ip config: %s, %s, %s, %s",
                      self.port_str(), ipaddr, subnet, gw, wild)
        return (ipaddr, subnet, gw, wild)

    def set_arpreply_on(self):
        return self.__sendCommand('p_arpreply on')

    def set_arpreply_off(self):
        return self.__sendCommand('p_arpreply off')

    def get_arpreply_enabled(self):
        reply = self.__sendQuery('p_arpreply ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        logger.debug("Port(%s): ARP reply enabled: %s", self.port_str(), status)
        return status

    def set_pingreply_on(self):
        return self.__sendCommand('p_pingreply on')

    def set_pingreply_off(self):
        return self.__sendCommand('p_pingreply off')

    def get_pingreply_enabled(self):
        reply = self.__sendQuery('p_pingreply ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        logger.debug("Port(%s): PING reply enabled: %s", self.port_str(),
                      status)
        return status

    def set_pause_frames_on(self):
        return self.__sendCommand('p_pause on')

    def set_pause_frames_off(self):
        return self.__sendCommand('p_pause off')

    def get_pause_frames_enabled(self):
        reply = self.__sendQuery('p_pause ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        logger.debug("Port(%s): Pause frames is enabled: %s", self.port_str(),
                     status)
        return status

    def set_extra_csum_on(self):
        return self.__sendCommand('p_checksum on')

    def set_extra_csum_off(self):
        return self.__sendCommand('p_checksum off')

    def get_extra_csum_enabled(self):
        reply = self.__sendQuery('p_checksum ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        logger.debug("Port(%s): Extra checksum is enabled: %s",
                      self.port_str(), status)
        return status

    def set_tx_enabled_on(self):
        return self.__sendCommand('p_txenable on')

    def set_tx_enabled_off(self):
        return self.__sendCommand('p_txenable off')

    def set_txmode_normal(self):
        return self.__sendCommand('p_txmode normal')

    def set_txmode_strictuniform(self):
        return self.__sendCommand('p_txmode strictuniform')

    def set_txmode_sequential(self):
        return self.__sendCommand('p_txmode sequential')

    def get_txmode_status(self):
        reply = self.__sendQuery('p_txmode ?')
        status = reply.split()[-1]
        logger.debug("Port(%s): TX mode: %s", self.port_str(), status)
        return status

    def get_tx_enabled_status(self):
        reply = self.__sendQuery('p_txenable ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        logger.debug("Port(%s): Transmitter is enabled: %s", self.port_str(),
                     status)
        return status

    def set_tx_time_limit_ms(self, microsecs):
        return self.__sendCommand('p_txtimelimit %d' % microsecs)

    def get_tx_time_limit_ms(self):
        reply = self.__sendQuery('p_txtimelimit ?')
        limit = int(reply.split()[-1])
        logger.debug("Port(%s): TX time limit: %d", self.port_str(), limit)
        return limit

    def get_tx_elapsed_time(self):
        elapsed = 0
        if self.get_traffic_status():
            reply = self.__sendQuery('p_txtime ?')
            elapsed = int(reply.split()[-1])
            logger.debug("Port(%s): Transmitting for %s usec", self.port_str(),
                         elapsed)
        else:
            logger.error("Port(%s): Elapsed time on a stopped port",
                          self.port_str())
        return elapsed

    def get_port_total_tx_stats(self):
        reply = self.__sendQuery('pt_total ?')
        stats = self.__pack_stats(reply.split(), 2)
        logger.debug("Port(%s): Stats bps:%d, pps:%d, bytes:%d, pkts=%d",
                      self.port_str(), stats['bps'], stats['pps'],
                      stats['bytes'], stats['packets'])
        return stats

    def get_port_total_rx_stats(self):
        reply = self.__sendQuery('pr_total ?')
        stats = self.__pack_stats(reply.split(), 2)
        logger.debug("Port(%s): Stats bps:%d, pps:%d, bytes:%d, pkts=%d",
                      self.port_str(), stats['bps'], stats['pps'],
                      stats['bytes'], stats['packets'])
        return stats

    def get_port_nopld_stats(self):
        reply = self.__sendQuery('pt_nopld ?')
        stats = self.__pack_stats(reply.split(), 2)
        logger.debug("Port(%s): nopld stats bps:%d, pps:%d, bytes:%d, pkts=%d",
                      self.port_str(), stats['bps'], stats['pps'],
                      stats['bytes'], stats['packets'])
        return stats

    def add_stream(self, sid):
        if self.streams.has_key(sid):
            logger.error("Adding duplicated stream")
            return

        if self.__sendCommand('ps_create [%s]' % sid):
            stream_new = XenaStream.XenaStream(self.xsocket, self, sid)
            self.streams[sid] = stream_new
            return stream_new

        return

    def get_stream(self, sid):
        if self.streams.has_key(sid):
            return self.streams[sid]

        return None

    def del_stream(self, sid):
        if not self.streams.has_key(sid):
            logger.error("Deleting unknown stream")
            return

        stream_del = self.streams.pop(sid)
        del stream_del
        return self.__sendCommand('ps_delete [%s]' % sid)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
