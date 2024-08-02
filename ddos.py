
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
# module imports
import argparse
import random 
import sys
import csv
import cmd
# import matplotlib.pyplot as plt
from math import floor
from subprocess import Popen
from time import sleep,time
# user import
from topo_simple import SimpleTopo
import inspect

class AttackNet:
    def __init__(self, net):
        self.attack_len = 3
        self.tmp = 'tmp.csv'
        self.data = {}
        self.net = net
        self.wait_len = 2
        self.itfs = []
        self.atk_start = 0
        self.atk_end = 0
        self.atkers = []
        self.normals = []
        self.target = []
    def clean_net(self):
        cmd = "sudo mn -c"
        Popen(cmd,shell=True).wait()
        
    def init_roles(self):
        info('*** Choose network host roles for simulation.\n')
        
        net_sz = len(self.net.hosts)
        botnet_sz = floor(net_sz*0.3) 
        if botnet_sz < 2:
            botnet_sz = 2

        host_ids = [self.net.hosts[id] for id in random.sample(range(net_sz),botnet_sz)]
        self.atkers = host_ids[1:]
        self.target = host_ids[0]
        self.normals = [id for id in self.net.hosts if id not in host_ids]    
        self.itfs = ['edSw'+list(str(host.IP()))[3]+list(str(host.IP()))[5] for host in host_ids if host not in self.normals]


        print(f"relevant interfaces are: {self.itfs}")
    def init_attack(self):
        """
        Initiate DDoS attack with botnet_sz made of between 20-40% of network hosts using

        hping3 in the background
        """
        info('*** Initiate attack\n')
        attackers = self.atkers
        target = self.target
        print(target.IP())
        print(f"The following hosts will be attacking during the simulation: {attackers}")
        print(f"{target} will be the victim of the DDoS attack")
        print(f"{target} has ip {target.IP()}")
        for attacker in attackers:
            print(attacker,' is attacking.')
            attacker.cmd(f"hping3 --flood {target.IP()} &")

    def end_attack(self):
        info('*** End Attack\n')
        cmd = "killall hping3"
        Popen(cmd, shell=True).wait()
    
    def start_traffic(self):
        normals = self.normals
        for (src,dst) in zip(normals[1:-2],normals[2:-1]):
            src.cmd(f"hping3 {dst.IP()} &") 
    def start_monitor(self):
        info('*** run bwm-ng in background for data collection\n')
        cmd = f"bwm-ng -o csv -T rate -C ',' > {self.tmp} &"
        Popen(cmd,shell=True)

    def end_monitor(self):
        """Kill all running instances of bwm-ng """
        info('*** kill all monitoring instances\n')
        cmd = f"killall bwm-ng"
        Popen(cmd, shell=True).wait()
    def data_collection(self):
        info('*** Scrape data from generated csv file.\n')
        with open(self.tmp) as data_csv:
            reader = csv.reader(data_csv, delimiter=',')
            for row in reader:
                key = row[1]
                timestamp = float(row[0])
                thruput_bytes = float(row[4])
                if key in self.data:
                    self.data[key]['time'].append(timestamp)
                    self.data[key]['load'].append(thruput_bytes)
                else:
                    self.data[key] = {}
                    self.data[key]['time'] = []
                    self.data[key]['load'] = []
    def data_plots(self):
        info('*** Plots\n')
        itfs = self.itfs
        print(itfs)
        attack_period = (self.atk_start,self.atk_end)
        
        for k in sorted(self.data):
            if k[:6] in itfs:
                print('boo')
                xdata = self.data[k]['time']
                ydata = self.data[k]['load']
                plt.subplot()
                plt.plot(xdata,ydata)
                plt.title(k)
                plt.ylabel('bits/s')
                plt.axvspan(*attack_period,color='red', alpha = 0.1)
                plt.show() 

                
    '''def run(self):
        info('*** run ddos\n') 
        self.clean_net()
        self.init_attack()
    ''' 
