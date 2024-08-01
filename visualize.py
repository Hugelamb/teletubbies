import requests
import time

def display_attack_stats(attacker_host, target_host, pkt_num, time_stamp):
    data = {
        "attacker_host": attacker_host,
        "target_host": target_host,
        "pkt_num": pkt_num,
        "time_stamp": time_stamp
    }
    url = f"http://127.0.0.1:5000/attack/{attacker_host}"
    response = requests.put(url, json=data)
    if response.status_code == 200:
        print(f"Attack data updated for {attacker_host}")
    else:
        print(f"Failed to update attack data for {attacker_host}")

def display_firewall_stats(attack_status, suspected_host, dropped_pkt_count, time_stamp):
    data = {
        "attack_status": attack_status,
        "suspected_host": suspected_host,
        "dropped_pkt_count": dropped_pkt_count,
        "time_stamp": time_stamp
    }
    url = f"http://127.0.0.1:5000/firewall/{suspected_host}"
    response = requests.put(url, json=data)
    if response.status_code == 200:
        print(f"Firewall data updated for {suspected_host}")
    else:
        print(f"Failed to update firewall data for {suspected_host}")

if __name__ == '__main__':
    i = 0
    while i < 500:
        display_attack_stats("H01", "H11", i, time.time())
        display_attack_stats("H02", "H11", i+100, time.time())

        attack_status = False
        display_firewall_stats(attack_status, "H01", i, time.time())

        time.sleep(0.3)
        i += 1