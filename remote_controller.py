#!/usr/bin/python

"""
Custom mininet simulation for use of a Remote Controller.
"""

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel


def RemoteControllerNet():
    "Create a network from semi-scratch with a remote controller."

    net = Mininet( controller=RemoteController, switch=OVSSwitch, build=False )

    print "*** Creating switches"
    s1 = net.addSwitch( 's1' )
    s2 = net.addSwitch( 's2' )

    print "*** Creating hosts"
    hosts1 = [ net.addHost( 'h%d' % n, ip='192.168.100.%d/24' % n, mac='00:11:11:00:00:%d' %n ) for n in 3, 4 ]
    hosts2 = [ net.addHost( 'h%d' % n, ip='192.168.100.%d/24' % n, mac='00:22:22:00:00:%d' %n ) for n in 5, 6 ]

    print "*** Creating links"
    for h in hosts1:
        net.addLink( s1, h )
    for h in hosts2:
        net.addLink( s2, h )
    net.addLink( s1, s2 )

    print "*** Add POX remote controller"
    c0 = RemoteController('POX', ip='127.0.0.1', port=6633)

    print "*** Starting network"
    net.build()
    s1.start([c0])
    s2.start([c0])
    #hosts1[0].cmd('/usr/lib/quagga/zebra -f /home/rechia/mnlab/h3_zebra.conf &')

    #print "*** Testing network"
    #net.pingAll()

    print "*** Running CLI"
    CLI( net )

    print "*** Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )  # for CLI output
    RemoteControllerNet()
