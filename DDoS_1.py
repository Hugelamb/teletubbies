import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
import argparse
import random
import threading
import time

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
        num_core_switches = (k // 2) ** 2
        for i in range(num_core_switches):
            dpid = f"0000000000{k:02d}{i // (k//2):02d}{i % (k//2):02d}"
            core_switches.append(self.addSwitch(f'c_sw{i}', dpid=dpid))

        # Create pods
        for pod in range(k):
            aggr_switches.append([])
            edge_switches.append([])
            for sw in range(k // 2):
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
                host_ip = f"10.{pod}.{sw_index}.{host_id+2-offset}"
                host = self.addHost(f'h{pod}{host_id}', ip=host_ip)
                self.addLink(host, edge_switches[pod][sw_index])
                hosts.append(host)
                if (host_id+1) % (k//2) == 0:
                    sw_index += 1
                    offset += self.k ** 2//8

def ddos_attack(host, target_ip, duration=10, spoofed_ip='10.1.1.1'):
    """Simulates a DDoS attack using hping3 from the given host to the target IP."""
    host.cmd(f'timeout {duration}s hping3 --flood -a {spoofed_ip} {target_ip}')
    host.cmd('killall hping3')

def benign_traffic(host, target_ip, duration=10):
    """Simulates benign traffic using hping3 from the given host to the target IP."""
    host.cmd(f'timeout {duration}s hping3 {target_ip}')
    host.cmd('killall hping3')

def run_fat_tree(k):
    show_graph = 0
    topo = FatTreeTopo(k)
    net = Mininet(topo=topo, link=TCLink, controller=None, autoSetMacs=True, autoStaticArp=True)
    net.addController('controller', controller=RemoteController, ip="127.0.0.1", port=6633, protocols="OpenFlow13")
    net.start()

    # Print all links in the network
    print("All links in the network:")
    for link in net.links:
        print(f"{link.intf1.node.name} -- {link.intf1.name} <--> {link.intf2.name} -- {link.intf2.node.name}")

    # Print all hosts and their IP addresses
    print("All hosts in the network:")
    for host in net.hosts:
        print(f"Host: {host.name}, IP: {host.IP()}")

    # Select the victim host based on actual names
    victim_host = net.hosts[0]  # Select the first host as an example
    victim_ip = victim_host.IP()

    episode_count = 100
    no_of_hosts = len(net.hosts)

    for episode in range(episode_count):
        print(f"Episode {episode}")
        
        # Select a random attacker host
        attacking_host_id = random.randint(0, no_of_hosts - 2)
        attacking_host = net.hosts[attacking_host_id]

        # Select a random benign host, ensuring it's not the attacker
        benign_host_id = random.choice([i for i in range(no_of_hosts) if i != attacking_host_id])
        benign_host = net.hosts[benign_host_id]

        print(f"Host {attacking_host_id} is attacking and Host {benign_host_id} is sending normal requests")

        # Launch attack and benign traffic
        attack_thread = threading.Thread(target=ddos_attack, args=(attacking_host, victim_ip))
        benign_thread = threading.Thread(target=benign_traffic, args=(benign_host, victim_ip))
        
        attack_thread.start()
        benign_thread.start()
        
        attack_thread.join()
        benign_thread.join()

        time.sleep(2)  # Pause between episodes

    CLI(net)
    net.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a Fat-Tree topology with k-parameter')
    # default is the number (K) 
    parser.add_argument('k', type=int, nargs='?', default=4, help='Fat-Tree parameter k (must be an even number)')
    args = parser.parse_args()

    if args.k % 2 != 0:
        print("Error: k must be an even number.")
        sys.exit(1)

    run_fat_tree(args.k)

