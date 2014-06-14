"""
An application that limits the number of mac addresses learned per port.
Similar to features usually called MAC Limiting or Port Security.

Hardcoded to use forwarding.l2_pairs as the learning mechanism.

Author: Felipe Stall Rechia
"""

# These next two imports are common POX convention
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr
from collections import namedtuple
import pox.forwarding.l2_pairs as l2p
import os


# Even a simple usage of the logger is much nicer than print!
log = core.getLogger()
class PortSecurity(EventMixin):

    def __init__ (self,max_macs=1):
        self.listenTo(core.openflow)
        self.max_macs = max_macs
        self.table = {}
        log.info("Enabling Port Security Module")
        log.info("Maximum MAC Addresses per port: %d" % self.max_macs)

    def _handle_ConnectionUp (self, event):    
        log.info("Creating port-sec table for DPID %s",
                  dpidToStr(event.dpid))
        self.table[event.dpid] = {}
        # check all the switch ports and initialize MAC address counter to zero
        for port in event.ofp.ports:
            log.debug("Init port number: %d, port name: %s"
                      % (port.port_no,port.name))
            self.table[event.dpid][port.port_no] = []
                
        #log.info(event.parsed)
        #event.connection.addListenerByName("PacketIn", self._handle_PacketIn)

    def _handle_PacketIn (self, event):
        packet = event.parsed
        if packet.src in self.table[event.dpid][event.port]:
            log.debug("[DPID %d, P: %d] MAC %s Already Learned" 
                     % (event.dpid,event.port,packet.src))
            l2p._handle_PacketIn(event)
        elif len(self.table[event.dpid][event.port]) < self.max_macs:
            log.debug("[DPID %d, P: %d] MAC %s Adding as Trusted" 
                     % (event.dpid,event.port,packet.src))
            self.table[event.dpid][event.port].append(packet.src)
            l2p._handle_PacketIn(event)
        else:
            log.debug("[DPID %d, P: %d] MAC %s Refusing" 
                     % (event.dpid,event.port,packet.src))
            block_rule = of.ofp_flow_mod()
            block_rule.match.dl_src = packet.src
            block_rule.match.port = event.port
            block_rule.priority = 65535
            event.connection.send(block_rule.pack())

def launch ():
    core.registerNew(PortSecurity)

