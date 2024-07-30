#ddos packet generation in this file
# mininet imports
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import Controller, RemoteController,OVSSwitch
from mininet.cli import CLI
# module imports
import argparse
import random
import threading
import sys
import cmd
# user imports
from topo_simple import SimpleTopo

def ddos_attack(host,target):
    attack_duration = input("Attack length in seconds: ")
    # Send a ddos attack targeting host 'target' from host 'attacker'
    # send for a defined period of time or until packets are blocked by firewall/
    host.cmd('sh timeout ' + str(attack_duration) + 's hping3 --flood -a ' + host.IP() + ' ' + target.IP())
    # host.cmd('sh killall hping3')
    
    
    return "Process <ddos_attack> terminated."
def ddos_good_actor(host):
    """
    generate normal packet activity for given host in network.
    """
    TX_len = input("Transmission length in seconds: ")
    host.cmd('sh timeout ' + str(TX_len) + 's hping3 ' + host.IP())
    # host.cmd('sh killall hping3')
    return "Process <ddos_good_actor> terminated."
def run_attack_sim(net,sim_len=1):
    
    # decide which hosts to use as attackers and targets
    hosts = net.hosts
    [attacker_id,target_id] = random.sample(range(len(hosts)),2)
    attacker = hosts[attacker_id]
    target = hosts[target_id]
    print(attacker,' ', target)

    atk_thread = threading.Thread(target=ddos_attack, args=(attacker,target))
    tgt_thread = threading.Thread(target=ddos_good_actor, args=(target,))
    
    atk_thread.start()
    tgt_thread.start()
    
    atk_thread.join()
    tgt_thread.join()
    return "Simulation Started"

def main():
    # run basic test sim using known attacker and target ips for any k topology with k =< 2
    parser = argparse.ArgumentParser(description='Create a simple topo with k hosts')
    parser.add_argument('k', type=int, nargs='?', default=4, help='Enter Hosts')
    args = parser.parse_args() 
    topo = SimpleTopo(args.k)
    net = Mininet(topo=topo, link=TCLink, controller=None, autoSetMacs=True, autoStaticArp=True)
    net.addController('controller',controller=RemoteController, ip="127.0.0.1", port=6633, protocols="OpenFlow13")
    net.start()
    run_attack_sim(net,sim_len=10)
    CLI(net)
    return "file run successfully"
if __name__ == "__main__":
    print(main())
    
