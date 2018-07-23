from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
import ryu.app.ofctl.api as api

class Lab1controller(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
	print("init")
	self.now_port = []
	self.repply_lock = False
        super(Lab1controller, self).__init__(*args, **kwargs)


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
        datapath = ev.msg.datapath
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
	self.send_port_stats_request(datapath)
        #actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
	if(not self.repply_lock):
		print("here")
		actions = [parser.OFPActionOutput(self.now_port[2])]
		self.add_flow(datapath, 0, match, actions)
				
