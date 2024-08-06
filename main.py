#runs all auxiliary files here
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel,info
from topo_simple import SimpleTopo
from ddos import AttackNet
import subprocess
import argparse
import sys
import traceback
from time import sleep,time
#   import website
from mininet.log import setLogLevel, info

def run(k,plot='n'):
    # subprocess.Popen(['ryu-manager', 'ryu_firewall.py', '--log-dir', 'logs', '--log-file', 'ryu.log'])
    # subprocess.Popen(['ryu-manager', 'visualize.py', '--log-dir', 'logs', '--log-file', 'ryu.log'])

    process = subprocess.Popen(
    ['ryu-manager', 'ryu_firewall.py', '--log-dir', 'logs', '--log-file', 'ryu.log'],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL,
    start_new_session=True,
    shell=True
    )
    
    # subprocess.call(
    # ['ryu-manager', 'ryu_firewall.py']
    # )

    topo = SimpleTopo(k)

    net = Mininet(topo, link=TCLink, controller=None, autoSetMacs=True, autoStaticArp=True)
    net.addController('controller', controller=RemoteController, ip="127.0.0.1", port=6633, protocols="OpenFlow13")
    net.start()
    setLogLevel('info')
    try:
        atk = AttackNet(net)
        atk.start_monitor()
        atk.init_sim()       # initialize host roles
        atk.start_traffic()
        sleep(atk.wait_len)
        atk.start_attack()      # begin attacking
        atk.atk_start = time()
        sleep(atk.attack_len)   # wait for given attack duration
        # atk.end_attack()
        atk.atk_end = time()
        sleep(atk.wait_len)
        # atk.end_traffic()       # kill all regular network traffic
        atk.end_monitor()
        atk.data_collection()
        if plot == 'y':
            atk.data_plots()
        CLI(net)
        net.stop()
        atk.clean_net()
    except (KeyboardInterrupt,UserWarning,Exception) as e:
        print(traceback.format_exc())
        print(f"{e} Error Occurred while running attack simulation\n")
        net.stop()
        atk.clean_net()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a simple topo with k hosts')
    parser.add_argument('k', type=int, nargs='?', default=4, help='Enter Hosts')
    parser.add_argument('plot',type=str, nargs='?', default='n', help='Should plots be generated? [y/n]')
    args = parser.parse_args()

    run(args.k,args.plot)
