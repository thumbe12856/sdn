from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
from mininet.node import RemoteController

def createNet():
    net = Mininet(controller=None)
    switch1 = net.addSwitch('s1')
    host1 = net.addHost('h1')
    host2 = net.addHost('h2')
    net.addLink(host1, switch1)
    net.addLink(host2, switch1)
    
    net.addController("c0", controller=RemoteController,
                      ip="127.0.0.1",
                      port=6633)
    print "Net start"
    net.start()

    print "Dumping host connections"
    dumpNodeConnections(net.hosts)
    
    print "Testing network connectivity"
    net.pingAll()
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    createNet()

