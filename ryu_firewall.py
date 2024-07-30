#construct firewall in this file

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import dpid as dpid_lib
from ryu.lib import hub
import ipaddress

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.k = 4
        self.monitor_thread = hub.spawn(self._monitor)

    def check_ip_in_subnet(ip, subnet):
        n = ipaddress.ip_network(subnet)
        netw = int(n.network_address)
        mask = int(n.netmask)
        a = int(ipaddress.ip_address(ip))
        in_network = (a & mask) == netw
        return in_network

    def get_first_digit(number):
        number_str = str(abs(number)).replace('.', '')
        return int(number_str[0])

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Store datapath with a unique identifier
        switch_name = f'{datapath.id}'  # Adjust this to your naming convention
        self.datapaths[switch_name] = datapath

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        # flow_table(self)

        # Make Changes HERE!

        # Route Aggregate and Edge Switches
        for i in range(self.k):
            for j in range(self.k):
                #switch_name = f'agSw{i}{j}'
                switch_name = f'{datapath.id}'
                datapath = self.get_datapath(switch_name)
                dpid_str = dpid_lib.dpid_to_str(datapath.id)
                if dpid_str[11]==str(i) and dpid_str[13]==str(j):
                    if datapath and j >= self.k//2:
                        self.setup_aggregate_switch_flows(datapath, int(str(i) + str(j)))
                    elif datapath and j < self.k//2:
                        self.setup_edge_switch_flows(datapath, int(str(i) + str(j)))
                    else:
                        print(f"Error: Datapath {datapath} not found for {switch_name}")
                    


        # Route core switches

        #switch_name = f'c_sw{i}'
        switch_name = f'{datapath.id}'
        datapath = self.get_datapath(switch_name)
        dpid_str = dpid_lib.dpid_to_str(datapath.id)
        if dpid_str[11]==str(self.k): #checks 12th digit to see if this switch is a core switch
            self.setup_core_switch_flows(datapath)


    def setup_core_switch_flows(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid_str = dpid_lib.dpid_to_str(datapath.id)
        # Example: Installing a flow to forward packets based on switch index
        for i in range( (self.k // 2) ** 2 ):
            # Example match criteria and actions for switch 0
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=(f"10.{i}.0.0", '255.255.0.0'))
            actions = [parser.OFPActionOutput(i+1)]

            # Install the flow entry
            self.add_flow(datapath, 1, match, actions)
            # self.logger.info("Added flow to core switch %s match subnet 10.%d.x.x to port %d", dpid_str, i, i+1)

    def setup_aggregate_switch_flows(self, datapath, switch_index):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid_str = dpid_lib.dpid_to_str(datapath.id)

        i = switch_index % 10               # 2nd digit
        switch_index = switch_index // 10   # 1st digit

        # Agg to Core route - if in from port 3&4, out from ports 1&2
        for in_port in range(1+self.k//2, 1+self.k):
            for out_port in range(1, 1+self.k//2):
                match = parser.OFPMatch(in_port=(in_port))
                actions = [parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, 1, match, actions)
        for j in range(0, self.k//2):
            ip_DEST = (f"0.0.0.{j+2}", '0.0.0.255')
            
            match = parser.OFPMatch(eth_type = 0x0800, ipv4_dst = ip_DEST)
        
            #SUFFIX_OUTPUT_PORT_NUM = (j - 2 + y) % (self.k//2) + (self.k//2)
            actions = [parser.OFPActionOutput(j+1)]
            
            self.add_flow(datapath, 1, match, actions)


        # Agg to Edge route
        for j in range(0, self.k//2):
            ip_DEST = (f"10.{switch_index}.{j}.0", '255.255.255.0')
            port_DEST = (self.k//2) + j+1

            match = parser.OFPMatch(eth_type = 0x0800, ipv4_dst = ip_DEST)
            actions = [parser.OFPActionOutput(port_DEST)]
            self.add_flow(datapath, 10, match, actions)
            # self.logger.info("Added flow to switch %s to port %d for address %s", dpid_str, port_DEST, ip_DEST[0])

    def setup_edge_switch_flows(self, datapath, switch_index):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid_str = dpid_lib.dpid_to_str(datapath.id)

        i = switch_index % 10               # 2nd digit
        switch_index = switch_index // 10   # 1st digit

        # Edge to Agg route - if in from port 3&4, out from ports 1&2
        for in_port in range(1+self.k//2, 1+self.k):
            for out_port in range(1, 1+self.k//2):
                match = parser.OFPMatch(in_port=(in_port))
                actions = [parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, 1, match, actions)

        for j in range(0, self.k//2):
            ip_DEST = (f"0.0.0.{j+2}", '0.0.0.255')
            
            match = parser.OFPMatch(eth_type = 0x0800, ipv4_dst = ip_DEST)
        
            #SUFFIX_OUTPUT_PORT_NUM = (j - 2 + y) % (self.k//2) + (self.k//2)
            actions = [parser.OFPActionOutput(j+1)]
            
            self.add_flow(datapath, 1, match, actions)

        # Edge to Host route

        for j in range(0,  self.k//2): # Number of hosts under a single edge switch
            #10.pod.switch.id
            ip_DEST = (f"10.{switch_index}.{i}.{j+2}")
            port_DEST = (j+3)

            match = parser.OFPMatch(eth_type = 0x0800, ipv4_dst = ip_DEST)
            actions = [parser.OFPActionOutput(port_DEST)]
            self.add_flow(datapath, 11, match, actions)
            self.add_flow(datapath, 10, match, actions)
            self.logger.info("Added flow to switch %s to port %d for address %s", dpid_str, port_DEST, ip_DEST)
        


    def get_datapath(self, switch_name):
        return self.datapaths.get(switch_name)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)
   

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('Registering datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('Unregistering datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug('Sending stats request to: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('Datapath         Port     '
                         'RX-Packets  RX-Bytes  RX-Errors '
                         'TX-Packets  TX-Bytes  TX-Errors')
        self.logger.info('---------------- -------- '
                         '---------- -------- -------- '
                         '---------- -------- --------')
        for stat in sorted(body, key=lambda x: x.port_no):
            self.logger.info('%016x %8x %10d %8d %8d %10d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)