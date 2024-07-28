#topology generation in this file

import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
import argparse


core_switches = []
aggr_switches = []
edge_switches = []
hosts = []

class FatTreeTopo(Topo):
    def __init__(self, k):
        super(FatTreeTopo, self).__init__()
        self.k = k
        self.create_fat_tree()

    def create_fat_tree(self):
        k = self.k
        

        # Create core switches
        num_core_switches = (k // 2) ** 2 #(k/2)^2 core switches
        for i in range(num_core_switches):
            dpid = f"0000000000{k:02d}{i // (k//2):02d}{i % (k//2):02d}"
            core_switches.append(self.addSwitch(f'c_sw{i}', dpid=dpid))

        # Create pods
        for pod in range(k): #there are k pods
            aggr_switches.append([])
            edge_switches.append([])
            for sw in range(k // 2): #2 layers of k/2 switches
                aggr_dpid = f"0000000000{pod:02d}{k//2 + sw:02d}01"
                edge_dpid = f"0000000000{pod:02d}{sw:02d}01"
                aggr_switches[pod].append(self.addSwitch(f'agSw{pod}{sw}', dpid=aggr_dpid))
                edge_switches[pod].append(self.addSwitch(f'edSw{pod}{sw}', dpid=edge_dpid))

            # Connect core and aggregation switches
            for i in range(k // 2):
                for j in range(k // 2):
                    core_index = (i * (k // 2) + j)
                    self.addLink(core_switches[core_index], aggr_switches[pod][i])

            # Connect aggregation and edge switches within each pod
            for aggr_sw in aggr_switches[pod]:
                for edge_sw in edge_switches[pod]:
                    self.addLink(aggr_sw, edge_sw)

            # Create and connect hosts
            sw_index = 0
            offset = 0
            for host_id in range((k**3//4)//k):
                # print(f"host:{host_id+1} connecting to switch: {sw_index}, condition:{ (host_id+1) % (k//2) == 0}")
                host_ip = f"10.{pod}.{sw}.{host_id+2}"
                host_ip = f"10.{pod}.{sw_index}.{host_id+2-offset}"
                host = self.addHost(f'h{pod}{host_id}', ip=host_ip)
                self.addLink(host, edge_switches[pod][sw_index])
                hosts.append(host)
                if (host_id+1) % (k//2) == 0:
                    sw_index += 1
                    offset += self.k ** 2//8


import subprocess

def generate_and_visualize_topology(topo, filename='topology', output_format='png'):
    """
    Generates a DOT file and visualizes it using Graphviz.

    Parameters:
    - topo: Mininet Topo object representing the network topology.
    - filename: Base filename for output image file (default: 'topology').
    - output_format: Output format for visualization ('png', 'pdf', etc.) (default: 'png').
    """
    dot_filename = f"{filename}.dot"

    # Generate DOT file
    with open(dot_filename, 'w') as f:
        f.write('graph {\n')
        f.write('    rankdir=TB;\n')  # Set layout direction to Top to Bottom
        
        # Add switches and links
        for switch in topo.switches():
            f.write(f'    {switch};\n')
        
        for link in topo.links(withInfo=True):
            f.write(f'    {link[0]} -- {link[1]};\n')

        # Add hosts at the bottom
        f.write('    subgraph hosts {\n')
        f.write('        rank=same;\n')
        for host in topo.hosts():
            f.write(f'        {host};\n')
        f.write('    }\n')

        f.write('}\n')

    # Visualize using Graphviz
    output_file = f"{filename}.{output_format}"
    subprocess.run(['dot', f'-T{output_format}', dot_filename, f'-o{output_file}'])


def run_fat_tree(k):
    show_graph = 0
    topo = FatTreeTopo(k)
    net = Mininet(topo, link=TCLink, controller=None, autoSetMacs=True, autoStaticArp=True)
    net.addController('controller', controller=RemoteController, ip="127.0.0.1", port=6633, protocols="OpenFlow13")
    net.start()
    if show_graph: 
        generate_and_visualize_topology(topo)
    CLI(net)
    net.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a Fat-Tree topology with k-parameter')
    parser.add_argument('k', type=int, help='Fat-Tree parameter k (must be an even number)')
    args = parser.parse_args()

    if args.k % 2 != 0:
        print("Error: k must be an even number.")
        sys.exit(1)

    run_fat_tree(args.k)
