#runs all auxiliary files here
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from topo_simple import SimpleTopo
from ddos import AttackNet
import subprocess
import argparse
import sys
from time import sleep,time
#   import website
from mininet.log import setLogLevel, info

def run(k):
    setLogLevel('info')     
    
    # subprocess.Popen(['ryu-manager', 'ryu_firewall.py', '--log-dir', 'logs', '--log-file', 'ryu.log'])
    # subprocess.Popen(['ryu-manager', 'visualize.py', '--log-dir', 'logs', '--log-file', 'ryu.log'])

    # process = subprocess.Popen(
    # ['ryu-manager', 'visualize.py', '--log-dir', 'logs', '--log-file', 'ryu.log'],
    # stdout=subprocess.DEVNULL,
    # stderr=subprocess.DEVNULL,
    # stdin=subprocess.DEVNULL,
    # start_new_session=True
    # )
    
    # website.socketio.run(app, debug=True, port=5000)
    
    subprocess.Popen(
    ['ryu-manager', 'ryu_firewall.py', '--log-dir', 'logs', '--log-file', 'ryu.log'],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL,
    start_new_session=True,
    shell=True
    )

    topo = SimpleTopo(k)

    net = Mininet(topo, link=TCLink, controller=None, autoSetMacs=True, autoStaticArp=True)
    net.addController('controller', controller=RemoteController, ip="127.0.0.1", port=6633, protocols="OpenFlow13")
    net.start()
    try:
        atk = AttackNet(net)
        atk.init_roles()
        atk.start_monitor() 
        sleep(atk.wait_len)
        atk.start_traffic()
        atk.init_attack()
        atk.atk_start = time()
        sleep(atk.attack_len)
        atk.end_attack()
        atk.atk_end = time()
        sleep(atk.wait_len)
        atk.end_monitor()
        atk.data_collection()
        atk.data_plots()
        CLI(net)
        net.stop()
        atk.clean_net()
    except KeyboardInterrupt:
        net.stop()
        atk.clean_net()
        print("Error Occurred while running attack simulation")
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a simple topo with k hosts')
    parser.add_argument('k', type=int, nargs='?', default=4, help='Enter Hosts')
    args = parser.parse_args()

    run(args.k)
