
xenalib
=======

It is a colection of classes to interface with Xena traffic generator.
The goal is to help network engineers to write traffic test scripts
requiring minimum possible knowledge of Xena specifics.

The very minimum script requires a XenaSocket object to connect to
the Xena chassis. It receives the chassis IP address.

    xsocket = XenaSocket('<chassis IP address>')
    xsocket.connect()

At this point you have the communication opened with Xena's chassis.
Now create the Manager object passing the socket opened above, the
owner string and the password string.  The owner string is limited
to 8 chars. The password is an option argument in case the default
string 'xena' is valid.

    xm = XenaManager(xsocket, '<owner>', '<password = xena>')

The object will login in the chassis using default. The Manager
allows you to add/remove ports.  You need to specify the module
number and the port number.

    port0 = xm.add_port(1, 0)

The port object offers many methods to set/get port's configuration
and statistics.  For example, to disable pause frames on the port:

    port0.set_pause_frames_off()

You can repeat the same for a second port if needed:
    port1 = xm.add_port(1, 1)
    port1.set_pause_frames_off()

The interesting part of Xena is the possibility to create individual
streams and run them alone or in parallel.  The streams are associated
to ports and needs an identification number too.  The line below creates
a stream ID 1 on port 0 (s1_p0).

    s1_p0 = port0.add_stream(1)

As for the ports, the stream object offers many methods to set/get
stream's configuration. Here are some examples:

    s1_p0.set_stream_on()
    s1_p0.disable_packet_limit()
    s1_p0.set_rate_fraction()
    s1_p0.set_packet_header(pkthdr)
    s1_p0.set_packet_length_fixed(64, 1518)
    s1_p0.set_packet_payload_incrementing('0x00')
    s1_p0.disable_test_payload_id()
    s1_p0.set_frame_csum_on()

After enabled one or more streams, you can start traffic on a port
calling the following method:

    port0.start_traffic()

While the traffic is running, the chassis and the script are free
to get statistics, status or the elapsed running time. The test
runs independently of the script, so if the script or the connection
breaks down, the test will continue.  You can set the time limit in
microseconds on the transmit port as a failsafe mechanism if needed.

    # stop traffic after 10 seconds
    port0.set_rx_time_limit_ms(1000000)

Also during the execution, the connection has the keepalive option
enabled and there is a separate thread sending empty commands to the
chassis in order to keep the connection alive.

It is possible to get more specific statistics and process each them
or use the methods to push all the statistics to the Manager's cache.
You can reset or request the cache at any time.

    # capture all the TX port1 stats
    port1.grab_all_tx_stats()
    # capture all the RX port0 stats
    port0.grab_all_rx_stats()

    # get the current stats in the cache
    print port1.dump_all_rx_stats()


The statistics come in a python dictionary format which is easy to
navigate and find the specific fields.

The layout follows this pattern:
   {
      <sample> : { 'stat name' : { 'unit' : 'value' } },
      <sample> : { 'stat name' : { 'unit' : 'value' } },
      ...
   }


This is the the basic layout for the RX stats:
   {
     <timestamp> : {
       'pr_total': {
             'pps': <int>,
             'packets': <int>,
             'bps': <int>,
             'bytes': <int>
       },
       'pr_tplds': {
              <counter> : <int>,
              ...
       },
       'pr_notpld': {
             'pps': <int>,
             'packets': <int>,
             'bps': <int>,
             'bytes': <int>
       },
       'p_receivesync': {
             'IN SYNC' : 'True'|'False',
       },
       'pr_extra': {
             'gapcount': <int>,
             'pingreplies': <int>,
             'arprequests': <int>,
             'fcserrors': <int>,
             'pingrequests': <int>,
             'pauseframes': <int>,
             'arpreplies': <int>,
             'gapduration': <int>
       }
     },
     ...
  },


This is the basic layout for the TX stats:
  {
     <timestamp> : {
       'pt_extra': {
             'injectedtid': <int>,
             'injectedmis': <int>,
             'pingreplies': <int>,
             'arprequests': <int>,
             'training': <int>,
             'injectedint': <int>,
             'pingrequests': <int>,
             'injectedfcs': <int>,
             'arpreplies': <int>,
             'injectedseq': <int>
       },
       'pt_stream_<id>': {
             'pps': <int>,
             'packets': <int>,
             'bps': <int>,
             'bytes': <int>
       },
       ...
       'pt_total': {
             'pps': <int>,
             'packets': <int>,
             'bps': <int>,
             'bytes': <int>
       },
       'pt_notpld': {
             'pps': <int>,
             'packets': <int>,
             'bps': <int>,
             'bytes': <int>
       }
     },
       ...
  }


Some statistics may or may not be available depending on the configuration.

The script single_stream available in the repo shows the basics of
how a script can be done.


Output in CSV format
====================

It is possible to write the statistics in CSV format without any additional
work.  The single_stream example includes what is needed and it is mainly
including the StatsCSV module and calling write_csv as show below:

     write_csv(<filename.csv>, "Test Title", stats)


Troubleshooting:
================

All classes use the python logging facility, so you can set the log
level to DEBUG in order to get a lot more information.

    logging.basicConfig(level=logging.DEBUG)


Bugs:
=====

Please report bugs directly to Flavio Leitner <fbl@redhat.com>


