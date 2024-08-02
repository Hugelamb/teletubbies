
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


class AttackNet:
    def __init__(self, net):
        self.attack_len = 5
        self.tmp = 'tmp.csv'
        self.data = {}
        self.net = net
        self.wait_len = 5
        self.itfs = []
        self.atk_start = 0
        self.atk_end = 0

    def clean_net(self):
        cmd = "sudo mn -c"
        Popen(cmd,shell=True).wait()

    def init_attack(self):
        """
        Initiate DDoS attack with botnet_sz made of between 20-40% of network hosts using

        hping3 in the background
        """
        info('*** Initiate attack\n')
        net_sz = len(self.net.hosts)
        botnet_sz = floor(net_sz*0.3) 
        if botnet_sz < 2:
            botnet_sz = 2
        host_ids = [self.net.hosts[id] for id in random.sample(range(len(self.net.hosts)),botnet_sz)]
        print(host_ids)
        attackers = host_ids[1:]
        target = host_ids[0]
        print(target.IP())
        print(f"The following hosts will be attacking during the simulation: {attackers}")
        print(f"{target} will be the victim of the DDoS attack")
        print(f"{target} has ip {target.IP()}")
        for attacker in attackers:
            
            print(attacker)
            attacker.cmd(f"hping3 --flood {target.IP()} &")
            print("still running")

    def end_attack(self):
        info('*** End Attack\n')
        cmd = "killall hping3"
        Popen(cmd, shell=True).wait()
    
    def start_monitor(self):
        info('*** run bwm-ng in background for data collection\n')
        cmd = f"bwm-ng -o csv -T rate -C ',' > {self.tmp} &"
        Popen(cmd,shell=True).wait()

    def end_monitor(self):
        """Kill all running instances of bwm-ng """
        info('*** kill all monitoring instances\n')
        cmd = f"killall bwm-ng"
        Popen(cmd, shell=True).wait()
    def data_collection(self):
        info('*** Scrape data from generated csv file')
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
        itfs = [t for t in self.itfs if t in self.data]
        attack_period = (self.atk_start,self.atk_end)
        for k in sorted(self.data):
            xdata = self.data[k]['time']
            ydata = self.data[k]['load']
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
