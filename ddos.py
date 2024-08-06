
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
import os
import matplotlib.pyplot as plt
from math import floor
from subprocess import Popen
from time import sleep,time
# user import
from topo_simple import SimpleTopo
import inspect

class AttackNet:
    def __init__(self, net):
        self.attack_len = 5
        self.tmp = 'tmp.csv'
        self.data = {}
        self.net = net
        self.wait_len = 3
        self.itfs = []
        self.atk_start = 0
        self.atk_end = 0
        self.actors = []
        self.normals = []
        self.target = ''
    def clean_net(self):
        cmd = "sudo mn -c"
        Popen(cmd,shell=True).wait() 

    def init_sim(self):
        """
        Initiate DDoS attack with botnet_sz made of between 20-40% of network hosts using

        hping3 in the background
        """
        info('*** Initiate simulation\n')
        net_sz = len(self.net.hosts)
        botnet_sz = floor(net_sz*0.3) 
        if botnet_sz < 2:
            botnet_sz = 2
        host_ids = [self.net.hosts[id] for id in random.sample(range(len(self.net.hosts)),botnet_sz)]
        self.actors = host_ids
        self.target = self.actors[0]
        # print(self.actors)
    
    def start_traffic(self):
        info('*** Start normal network traffic\n')
        self.normals = [id for id in self.net.hosts if not id in self.actors]
        # run traffic for sim duration     
        for host in self.normals:
            host.cmd(f"timeout {self.wait_len*2+self.attack_len}s hping3 -S -d 200 -i 1 {self.target.IP()} &")
        
    def start_attack(self):
        info('*** Begin Attack\n')
        attackers = self.actors[1:]
        print(f"{self.target} will be the victim of the DDoS attack")
        print(f"{self.target} has ip {self.target.IP()}")
        for attacker in attackers:
            attacker.cmd(f"timeout {self.attack_len}s hping3 --flood {self.target.IP()} &")
    
    def end_attack(self):
        info('*** End Attack\n')
        cmd = "killall hping3"
        Popen(cmd, shell=True).wait()
     
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
        info('*** Scrape data from generated csv file\n')
        with open(self.tmp) as data_csv:
            reader = csv.reader(data_csv, delimiter=',', quoting=csv.QUOTE_NONE)
            for row in reader:
                key = row[1]
                timestamp = float(row[0])
                rxb = float(row[2])
                txb = float(row[3])
                # txp = float(row[7])
                # rxp = float(row[8])
                thruput_bytes = float(row[4])
                if key in self.data:
                    self.data[key]['time'].append(timestamp)
                    self.data[key]['load'].append(thruput_bytes)
                    self.data[key]['Tx_bytes/s'].append(txb)
                    self.data[key]['Rx_bytes/s'].append(rxb)
                  # self.data[key]['Packets out/s'].append(txp)
                  # self.data[key]['Packets in/s'].append(rxp)


                else:
                    self.data[key] = {}
                    self.data[key]['time'] = []
                    self.data[key]['load'] = []
                    self.data[key]['Tx_bytes/s'] = []
                    self.data[key]['Rx_bytes/s'] = []
                    self.data[key]['Packets out/s'] = []
                    self.data[key]['Packets in/s'] = []
            
    def data_plots(self):
        info('*** Plots\n') 
        intf_of_intrst = [[[x.intf1.name, x.intf2.name] for x in self.net.links if str(y) in str(x.intf1)] for y in self.actors]
        intf_of_intrst = [x[0] for x in intf_of_intrst]
        attack_period = (self.atk_start,self.atk_end)
        counter = 0
        intf_normal = [[[x.intf1.name, x.intf2.name] for x in self.net.links if str(y) in str(x.intf1)] for y in self.normals]
        print(intf_normal)
        intf_of_intrst.append(intf_normal[random.randint(0,len(intf_normal)-1)][0]) 
        for k in sorted(intf_of_intrst):
            xdataraw = self.data[k[1]]['time']
            xdata = [x-min(xdataraw) for x in xdataraw] 
            ydata = self.data[k[1]]
            atk_t_no_offset = (attack_period[0]-min(xdataraw),attack_period[1]-min(xdataraw))     
            plt.figure()
            loadline, = plt.plot(xdata,ydata['load'], label='Overall Load')
            txb, = plt.plot(xdata,ydata['Tx_bytes/s'], label='Outgoing bytes')
            rxb, = plt.plot(xdata,ydata['Rx_bytes/s'], label='Received bytes')
            if k[0][0:-5] == str(self.target):
                plt.title(f"Target {k[0][0:-5]} network activity")
                
            elif k[0][0:-5] in str(self.actors): 
                plt.title(f"Attacker {k[0][0:-5]} network activity")
            else:
                plt.title(f"Normal host {k[0][0:-5]} network activity")
            print(k)
            plt.ylabel('Port Activity (bytes/s)')
            plt.xlabel('Simulation Time (s)')
            plt.legend(handles=[loadline,txb,rxb])
            plt.axvspan(*atk_t_no_offset,color='red', alpha = 0.1)
            cwd = os.getcwd()
            imagepath = cwd + "/plots/"+ f'{k[0][0:-5]}.png' 
            plt.savefig(imagepath, bbox_inches='tight')
            if counter < len(intf_of_intrst)-1:
                plt.show(block=False)
            else:
                plt.show()
            counter += 1
            
                
    '''def run(self):
        info('*** run ddos\n') 
        self.clean_net()
        self.init_attack()
    ''' 
