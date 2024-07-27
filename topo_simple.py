#topology generation in this file

from mininet.topo import Topo


switches = []
hosts = []

class simpleTopo(Topo)
def __init__(self, k):
        super(simpleTopo, self).__init__()
        self.k = k
        self.create_simple()
def create_fat_tree(self):
        k = self.k
        
        
        dpid = f"000000000001"
        switches.append(self.addSwitch(f'sw1', dpid=dpid))


        # Create and connect hosts
        
        for host_id in range(k):
            host_ip = f"10.0.0.{host_id}"
            host = self.addHost(f'h{host_id}', ip=host_ip)
            self.addLink(host, switches[0])
            hosts.append(host)
      