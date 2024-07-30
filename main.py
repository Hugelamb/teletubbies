#runs all auxiliary files here
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from topo_simple import SimpleTopo
from ddos_sim import ddos_attack
import argparse
import sys

def run(k):
    
    topo = SimpleTopo(k)
    net = Mininet(topo, link=TCLink, controller=None, autoSetMacs=True, autoStaticArp=True)
    net.addController('controller', controller=RemoteController, ip="127.0.0.1", port=6633, protocols="OpenFlow13")
    print('boo')
    net.start()
    print('boo')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a simple topo with k hosts')
    parser.add_argument('k', type=int, nargs='?', default=4, help='Enter Hosts')
    args = parser.parse_args()

    run(args.k)
