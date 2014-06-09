#!/usr/bin/python

"""
Topologia para demonstracao de funcionalidades basicas L2 e L3 com
controlador remoto POX
"""

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections


def RemoteControllerNet():
    "Cria uma rede configurada manualmente com controlador remoto."

    net = Mininet( controller=RemoteController, switch=OVSSwitch, build=False )

    print "*** Criando switches"
    SW1 = net.addSwitch( 'SW1' )
    SW2 = net.addSwitch( 'SW2' )
    SW3 = net.addSwitch( 'SW3' )
    SW4 = net.addSwitch( 'SW4' )

    print "*** Criando hosts e enlaces para os switches"
    hosts = {}
    for oct3 in range(10,31,10):
        for host in range(1,2+1):
            name = "h%d_%d" % (oct3,host)
            hosts[name] = net.addHost( name,
                          ip='192.168.%d.%d/24' % (oct3, host),
                          mac='02:00:00:00:%d:%d' % (oct3, host))
            if oct3 == 10:
                net.addLink(hosts[name], SW1)
            elif oct3 == 20:
                net.addLink(hosts[name], SW2)
            elif oct3 == 30:
                net.addLink(hosts[name], SW3)

    print "*** Criando enlace entre os switches"
    
    net.addLink( SW4, SW1 )
    net.addLink( SW4, SW2 )
    net.addLink( SW4, SW3 )

    print "*** Adicionando controlador remoto POX"
    c0 = RemoteController('POX_L2', ip='127.0.0.1', port=6633)
    c1 = RemoteController('POX_SR', ip='127.0.0.1', port=9000)

    print "*** Construindo e iniciando os elementos da rede"
    net.build()
    SW1.start([c1])
    SW2.start([c1])
    SW3.start([c1])
    SW4.start([c0])

    print "*** Configurando default GWs em cada host"
    for oct3 in range(10,31,10):
        for host in range(1,2+1):
            name = "h%d_%d" % (oct3,host)
            hosts[name].cmd('route add default gw 192.168.%d.254' % oct3)


    print "*** Imprimindo tabela de conexoes:"
    dumpNodeConnections(net.switches)
    print "*** Imprimindo DPIDs dos switches:"
    print "SW1:",SW1.dpid
    print "SW2:",SW2.dpid
    print "SW3:",SW3.dpid
    print "SW4:",SW4.dpid

    print "*** Iniciando CLI"
    CLI( net )

    print "*** Parando a rede..."
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )  # for CLI output
    RemoteControllerNet()
