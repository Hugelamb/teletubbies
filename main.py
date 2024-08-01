#runs all auxiliary files here
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from topo_simple import SimpleTopo
import ddos
import argparse
import sys
from mininet.log import setLogLevel,info
def run(k):

    setLogLevel('info')

    topo = SimpleTopo(k)
    net = Mininet(topo, link=TCLink, controller=None, autoSetMacs=True, autoStaticArp=True)
    net.addController('controller', controller=RemoteController, ip="127.0.0.1", port=6633, protocols="OpenFlow13")  
    attackNet = ddos.AttackNet(net)
    try:
        net.start()
        attackNet.start_monitor()
        attackNet.init_attack()
        
        CLI(net)
        attackNet.end_attack()
        attackNet.end_monitor()
        net.stop()
        attackNet.clean_net()
    except:
        attackNet.clean_net()
        print('error encountered')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a simple topo with k hosts')
    parser.add_argument('k', type=int, nargs='?', default=4, help='Enter Hosts')
    args = parser.parse_args()

    run(args.k)
