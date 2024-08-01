import requests

def display_attack_stats(attacker_host, target_host, pkt_num, time_stamp):
    # print(f"Update: {attacker_host}, {target_host}, {pkt_num}")

    url = "http://127.0.0.1:5000/attack/table"
    
    data = {
        "attacker_host": attacker_host,
        "target_host": target_host,
        "pkt_num": pkt_num,
        "time_stamp": time_stamp
    }
    url = f"http://127.0.0.1:5000/attack/{attacker_host}"

    response = requests.put(url, json=data)


if __name__ == '__main__':
    import time

    i=0
    while i < 500:
        display_attack_stats("H01", "H11", i, time.time())
        display_attack_stats("H02", "H11", i+100, time.time())
        time.sleep(0.3)
        i+=1
    display_attack_stats("H03", "H11", i+100, time.time())
