from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
import ryu.app.ofctl.api as api
from ryu.lib.packet import ipv4

class Lab2controller(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
	print("init")
	self.mac_to_port_table = {}
	self.ip_to_mac_table = {}
	self.now_port = []
	self.repply_lock = False
        super(Lab2controller, self).__init__(*args, **kwargs)

    def send_port_stats_request(self, datapath):
	print("send request")
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        req = ofp_parser.OFPPortStatsRequest(datapath, 0, ofp.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
	print("reply request")
        ports = []
        for stat in ev.msg.body:
	    print("port num {0}".format(stat.port_no))
	    ports.append(stat.port_no)
	self.logger.info('PortStats: %s', ports)
	self.now_port = ports
	self.repply_lock = False

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
	print("add flow")
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

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
	print("switch features handler")
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
	match = parser.OFPMatch()
	self.repply_lock = True
	self.now_port = []
	#self.send_port_stats_request(datapath)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
	self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
	#print("packet in handler")
	msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
	datapath_id = datapath.id

	pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src
	
	pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
	if(pkt_ipv4):
		ip4_src = pkt_ipv4.src
		ip4_dst = pkt_ipv4.dst

		self.mac_to_port_table.setdefault(ip4_src, {})
		self.mac_to_port_table.setdefault(ip4_dst, {})
		self.ip_to_mac_table[ip4_src] = src
		self.ip_to_mac_table[ip4_dst] = dst

	in_port = msg.match['in_port']
	self.mac_to_port_table.setdefault(datapath_id, {})
	self.mac_to_port_table[datapath_id][src] = in_port
	
	if(dst in self.ip_to_mac_table.values()):
		print("here!")

	if(dst in self.mac_to_port_table[datapath_id]):
            out_port = self.mac_to_port_table[datapath_id][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

	actions = [parser.OFPActionOutput(out_port)]

	if(out_port != ofproto.OFPP_FLOOD):
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 2, match, actions)

	out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
	datapath.send_msg(out)

