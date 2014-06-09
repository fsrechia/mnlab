# Copyright 2011 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

"""
This is an L2 learning switch written directly against the OpenFlow library.
It is derived from one written live for an SDN crash course.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.util import str_to_bool
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
import pox.lib.packet.icmp as icmp
from pox.lib.packet.arp import arp
from pox.lib.packet.udp import udp
from pox.lib.packet.dns import dns
from pox.lib.addresses import IPAddr, EthAddr


import time
import code
import os
import struct
import sys

log = core.getLogger()
FLOOD_DELAY = 5
#default location /home/ubuntu/cs144_lab3/IP_CONFIG
IPCONFIG_FILE = './IP_CONFIG'
ROUTE_FILE = './rtable'
IP_SETTING={}
RTABLE = []
ROUTER_IP={}

#Topology is fixed 
#sw0-eth1:server1-eth0 sw0-eth2:server2-eth0 sw0-eth3:client

class RouterInfo(Event):
  '''Event to raise upon the information about an openflow router is ready'''

  def __init__(self, info, rtable):
    Event.__init__(self)
    self.info = info
    self.rtable = rtable


class OFHandler (EventMixin):
  def __init__ (self, connection, transparent):
    # Switch we'll be adding L2 learning switch capabilities to
    self.connection = connection
    self.transparent = transparent
    self.nat_rule_installed = False
    self.sw_info = {}
    self.connection.send(of.ofp_set_config(miss_send_len = 65535))
    for port in connection.features.ports:
        intf_name = port.name.split('-')
        if(len(intf_name) < 2):
          continue
        else:
          intf_name = intf_name[1]
        if intf_name in ROUTER_IP.keys():
          self.sw_info[intf_name] = (ROUTER_IP[intf_name], port.hw_addr.toStr(), '10Gbps', port.port_no)
    self.rtable = RTABLE
    # We want to hear Openflow PacketIn messages, so we listen
    self.listenTo(connection)
    self.listenTo(core.cs144_srhandler)
    core.cs144_ofhandler.raiseEvent(RouterInfo(self.sw_info, self.rtable))

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch to implement above algorithm.
    """
    pkt = event.parse()
    if pkt.type == pkt.IP_TYPE:
        log.info('Caught SR In IP Packet: %s => %s' % (pkt.next.srcip, pkt.next.dstip))
        if pkt.next.srcip == '192.168.30.2' and pkt.next.dstip == '192.168.30.254':
            pkt.next.dstip = IPAddr('192.168.10.1')
            log.info('Rewritten In packet   : %s => %s' % (pkt.next.srcip, pkt.next.dstip))
   # if pkt.type == ethernet.IP_TYPE and not self.nat_rule_installed:
   #   log.info('got IP Packet: %s => %s' % (pkt.next.srcip, pkt.next.dstip))
   #   if pkt.next.dstip == '192.168.30.2' and pkt.next.srcip == '192.168.10.1':
   #     log.info('trying to create stupid NAT rule...')
   #     nat_rule = of.ofp_flow_mod()
   #     nat_rule.match.dl_type = 0x800
   #     nat_rule.match.nw_src = pkt.next.srcip
   #     nat_rule.match.nw_src = pkt.next.srcip
   #     nat_rule.actions.append(of.ofp_action_nw_addr.set_src('192.168.30.254')) 
   #     nat_rule.actions.append(of.ofp_action_dl_addr.set_src('ce:cc:af:a9:be:64'))
   #     nat_rule.actions.append(of.ofp_action_dl_addr.set_dst('02:00:00:00:30:02'))
   #     nat_rule.actions.append(of.ofp_action_output(port = 3))
   #     self.connection.send(nat_rule)
   #     self.nat_rule_installed = True


    raw_packet = pkt.raw
    core.cs144_ofhandler.raiseEvent(SRPacketIn(raw_packet, event.port))
    msg = of.ofp_packet_out()
    msg.buffer_id = event.ofp.buffer_id
    msg.in_port = event.port
    self.connection.send(msg)


  def _handle_SRPacketOut(self, event):
    msg = of.ofp_packet_out()
    new_packet = event.pkt
    msg.actions.append(of.ofp_action_output(port=event.port))
    # -1 causes exceptions.RuntimeError: can not have both buffer_id and data set
    #msg.buffer_id = -1
    msg.buffer_id = None
    msg.in_port = of.OFPP_NONE
    e = ethernet(raw=new_packet)
    if e.type == ethernet.IP_TYPE:
        log.info('Caught SR Out IP Packet: %s => %s' % (e.next.srcip, e.next.dstip))
        if e.next.srcip == '192.168.10.1' and e.next.dstip == '192.168.30.2':
            e.next.srcip = IPAddr('192.168.30.254')
            log.info('Rewritten Out packet   : %s => %s' % (e.next.srcip, e.next.dstip))
    #msg.data = new_packet
    msg.data = e.pack()
    self.connection.send(msg)

class SRPacketIn(Event):
  '''Event to raise upon a receive a packet_in from openflow'''

  def __init__(self, packet, port):
    Event.__init__(self)
    self.pkt = packet
    self.port = port

class cs144_ofhandler (EventMixin):
  """
  Waits for OpenFlow switches to connect and makes them learning switches.
  """
  _eventMixin_events = set([SRPacketIn, RouterInfo])

  def __init__ (self, transparent):
    EventMixin.__init__(self)
    self.listenTo(core.openflow)
    self.transparent = transparent

  def _handle_ConnectionUp (self, event):
    log.debug("Connection %s" % (event.connection,))
    OFHandler(event.connection, self.transparent)



def get_ip_setting():
  if (not os.path.isfile(IPCONFIG_FILE)):
    return -1
  ipf = open(IPCONFIG_FILE, 'r')
  for line in ipf:
    if(len(line.split()) == 0):
      break
    name, ip = line.split()
    if ip == "<ELASTIC_IP>":
      log.info("ip configuration is not set, please put your Elastic IP addresses into %s" % IPCONFIG_FILE)
      sys.exit(2)
    print name, ip
    IP_SETTING[name] = ip
    if "SW" in name:
        router,interface = name.split("-")
        print "Interface %s from router %s IP address: %s" % (interface,router,ip)
        ROUTER_IP[interface] = IP_SETTING[name]
  ipf.close()

  if (not os.path.isfile(ROUTE_FILE)):
    return -1 
  rf =  open(ROUTE_FILE, 'r')
  for line in rf:
    if(len(line.split()) == 0):
      break
    dest,gw,mask,intf = line.split()
    print "add route:",dest,gw,mask,intf
    RTABLE.append((dest,gw,mask,intf))
  rf.close()

  return 0


def launch (transparent=False):
  """
  Starts an Simple Router Topology
  """    
  core.registerNew(cs144_ofhandler, str_to_bool(transparent))
  
  r = get_ip_setting()
  if r == -1:
    log.debug("Couldn't load config file for ip addresses, check whether %s exists" % IPCONFIG_FILE)
    sys.exit(2)
  else:
    log.debug('*** ofhandler: Successfully loaded ip settings for hosts\n %s\n' % IP_SETTING)
