#!/usr/bin/python

"""
Custom mininet simulation for L2 Switches and no controllers.
"""

from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

class SimpleSwitch( OVSSwitch ):
    """Custom Switch() subclass which spawns OVSSwitch with empty failMode and
    with and empty list of controllers in order to use it as a simple L2 Switch.
    """
    def start( self ):
        self.failMode=""
        return OVSSwitch.start( self, [  ] )

def noControllerNet():
    "Create a network from semi-scratch without controllers."

    net = Mininet( controller=Controller, switch=SimpleSwitch, build=False )

    print "*** Creating switches"
    s1 = net.addSwitch( 's1' )
    s2 = net.addSwitch( 's2' )

    print "*** Creating hosts"
    hosts1 = [ net.addHost( 'h%d' % n ) for n in 3, 4 ]
    hosts2 = [ net.addHost( 'h%d' % n ) for n in 5, 6 ]

    print "*** Creating links"
    for h in hosts1:
        net.addLink( s1, h )
    for h in hosts2:
        net.addLink( s2, h )
    net.addLink( s1, s2 )

    print "*** Starting network"
    net.build()
    s1.start()
    s2.start()

    print "*** Testing network"
    net.pingAll()

    print "*** Running CLI"
    CLI( net )

    print "*** Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )  # for CLI output
    noControllerNet()
