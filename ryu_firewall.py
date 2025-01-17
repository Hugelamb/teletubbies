#construct firewall in this file

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import dpid as dpid_lib
from ryu.lib import hub
import visualize
import ipaddress
import time

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.k = 4

        # firewall variables
        self.monitor_thread = hub.spawn(self.monitor)
        self.src_mac = [] # list of source mac addresses to track
        self.dst_ip = {} # dict of destination IPv4 addresses to track and it's count
        self.count_src = [] # number of times each src has sent requests
        self.count_dst = [] # number of times each dst has received packets
        self.link_max = 50 # set the max. number of packets a link can receive within a window
        self.byte_ratio_max = 100 # set min. number of bytes per packet
        self.dst_max = 2 # set the max. number of times a dst can receive packets within a window


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
        self.add_flow(datapath, 0, match, actions, idle_timeout=0)
        # flow_table(self)

        if datapath.id not in self.datapaths:
            self.datapaths[datapath.id] = datapath
            # self.logger.info('Registering datapath: %16x', datapath.id)

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
            self.add_flow(datapath, 10, match, actions)
            self.logger.info("Added flow to switch %s to port %d for address %s", dpid_str, port_DEST, ip_DEST)
            


    def get_datapath(self, switch_name):
        return self.datapaths.get(switch_name)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, reset_count=False):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        flags = 0
        if reset_count:
            flags |= ofproto.OFPFF_RESET_COUNTS
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst, idle_timeout=idle_timeout, flags=flags)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst, idle_timeout=idle_timeout, flags=flags)
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
        if int(dst[:1]) != 3:
            self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # increment 
        # self.add_dst(src, dst)
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id, 0)
                return
            else:
                self.add_flow(datapath, 1, match, actions, 0)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    '''
    monitor()
        periodically requests flow and port stats from the switch with a period of 1 sec
    '''
    def monitor(self):
        while True:
            for dp in self.datapaths.values():
                self.get_stats(dp)
            hub.sleep(20) # check the throughput every 1 second

    '''
    get_stats()
        retrieves the flow and port stats from the switch
    '''
    def get_stats(self, datapath):
        self.logger.info('Requesting stats for: %016x', datapath.id)

        # ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        request = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(request)

        # request = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY) # gets port info for all ports
        # datapath.send_msg(request)

    '''
    handle_flow_stats
        -> called whenever switch fufils flow stats request that is sent periodically (T = 1 sec)
        retreive relevant data from the flow stats reply
        check data against firewall conditions
        add 'DROP' flow rules if firewall triggered with idle timeout of 10 

        firewall conditions:
        1. packet condition -> number of packets received exceeds the link limit
        2. byte condition -> ratio of bytes to packets received is low (lots of packets with little data - 'empty' packets)
        3. dst condition -> number of packets sent to a host (dst) exceeds the dst limit

    '''
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def handle_flow_stats(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        print('Flow stats received...')

        # sort flow rules, then check the stats of each rule
        for stat in sorted([flow for flow in msg.body if (flow.priority == 10)  and 'ipv4_dst' in flow.match], key=lambda flow: flow.match['ipv4_dst']):
            print(stat.match)
            # filter out by flow rules that have matchedoffending handler [handle_flow_stats] servicing event [EventOFPFlowStatsReply] follows.
            print('priority passed...')
            print(stat)
            if stat.packet_count == 0:
                ip_dst = stat.match['ipv4_dst']
                if ip_dst not in self.dst_ip:
                    # self.dst_ip.append(ip_dst)
                    # self.count_dst.append(1)
                    self.dst_ip[ip_dst] = 0
                    print('added ip for: ', ip_dst)
                # else:
                #     self.dst_ip[ip_dst] += 0

            if stat.packet_count > 0:
                print('packet count passed...')
                if len(self.dst_ip) > 0:
                    # check each dst ip in list and update respective counts
                    if 'ipv4_dst' in stat.match:
                        ip_dst = stat.match['ipv4_dst']

                        if ip_dst not in self.dst_ip: 
                            self.dst_ip[ip_dst] = 0
                            print('added ip for: ', ip_dst)
                        else:
                            for dest_ip, dest_count in self.dst_ip.items():
                                if ip_dst == dest_ip:
                                    self.dst_ip[dest_ip] = dest_count + 1
                                    print('incremented count for: ', ip_dst)

                    
                    # check against firewall conditions
                    packet_condition = stat.packet_count >= self.link_max
                    byte_condition = (stat.byte_count / stat.packet_count) < self.byte_ratio_max

                    if packet_condition and byte_condition:
                        # if ddos detected, send a flow rule to DROP packets
                        self.add_flow(datapath=datapath, priority=11, match=stat.match, actions=[], idle_timeout=10)
                        print(f'!!! DDOS detected - packet or byte !!!')
                        print(f'Dropping link to: ', stat.match['ipv4_dst'])
                        visualize.display_firewall_stats(True, stat.match['ipv4_dst'], stat.packet_count, time.time())

                    else:
                        visualize.display_firewall_stats(False, 'None', 0, time.time())

                        
                    # send flow mod request to update the flow table
                    mod = parser.OFPFlowMod(datapath=datapath, priority=stat.priority, idle_timeout=stat.idle_timeout, match=stat.match, instructions=stat.instructions, flags=ofproto.OFPFF_RESET_COUNTS) # reset the counts for each flag

                    datapath.send_msg(mod)
        
        # check dst condition
        if len(self.dst_ip) > 0:
            for dest_ip, dest_count in self.dst_ip.items():
                # print('ip: ', dest_ip)
                # print('count: ', dest_count)
                dst_condition = dest_count >= self.dst_max
                if dst_condition:
                    match = parser.OFPMatch(ipv4_dst=dest_ip)
                    # send DROP rule
                    self.add_flow(datapath=datapath, priority=15, match=match, actions=[], idle_timeout=10)
                    print(f'!!! DDOS detected - dst limit !!!')
                    print(f'Dropping packets to dst mac: {dest_ip}')
                    print('ip: ', dest_ip)
                    print('count: ', dest_count)

            
        # reset all dst counts to 0
        for key in self.dst_ip:
            self.dst_ip[key] = 0
    
