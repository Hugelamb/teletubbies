#ddos packet generation in this file
from mininet.net import Mininet
from topo_simple import SimpleTopo
from mininet.node import Controller, RemoteController,OVSSwitch

import random
import threading
import sys
import cmd

def ddos_attack(target,attacker,sim_length=10):
    # Send a ddos attack targeting host 'target' from host 'attacker'
    # send for a defined period of time or until packets are blocked by firewall/ 
    host.cmd('sh timeout' + str(sim_length) + 's hping3 ' + target_ip + ' --flood -a ' + attacker_ip)
    
    return "Process <ddos_attack> terminated."
def ddos_good_actor():
    """
    generate normal packet activity for given host in network.
    """
    host.cmd(host + ' ping ' + INSERT RANDOMIZED destination)
    return "Process <ddos_good_actor> terminated."
def run_attack_sim():
    
    atk_thread = threading.Thread(target=ddos_attack, args=(attacker,))
    tgt_thread = threading.Thread(target=ddos_good_actor, args=(target,))
    
    atk_thread.start()
    tgt_thread.start()

    atk_thread.join()
    tgt_thread.join()
    return "Simulation Started"

def main():
    
    return sys.stdout("file run successfully")
if __name__ == "__main__":
    main()
    
