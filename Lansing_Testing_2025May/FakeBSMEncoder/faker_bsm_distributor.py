#/usr/bin/env python
"""
Author: Dylan
Date: 05/17/2022
Note: This work is used for :
    1. read fake BSM file and send to MMITSS VSP
"""
import time

#import BSMEncoder
import socket


class UDP:
    def __init__(self, address):
        self.ip, self.port = address

    def send(self, information):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(information, (self.ip, self.port))

    def receive(self):
        addr = (self.ip, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.03)
        sock.bind(addr)
        while True:
            try:
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                data = None
            return data


def distribute_Bsm(msg_li, mmitss_address, obu_address):
    obu_udp, mmitss_udp = UDP(obu_address), UDP(mmitss_address)
    print('yes')
    count = 0
    l = len(msg_li)
    while True:
        idx = count%l
       # print(idx)
        bsm2mmitss_temp = msg_li[idx]
        bsm2obu_temp = "Version=0.7\n" + \
                       "Type=BSM\n" + \
                       "PSID=0x20\n" + \
                       "Priority=7\n" + \
                       "TxMode=ALT\n" + \
                       "TxChannel=183\n" + \
                       "TxInterval=0\n" + \
                       "DeliveryStart=\n" + \
                       "DeliveryStop=\n" + \
                       "Signature=False\n" + \
                       "Encryption=False\n" + \
                       "Payload=" + bsm2mmitss_temp

        bsm2obu = bytes(bsm2obu_temp, 'utf-8')
        bsm2mmitss = bytes.fromhex(bsm2mmitss_temp)
        print(bsm2obu)

        obu_udp.send(bsm2obu)
        mmitss_udp.send(bsm2mmitss)
        time.sleep(0.1)
        count += 1


if __name__ == '__main__':
    # receive_address = ('0.0.0.0', 20001) #read from file
    # send_address = ('10.12.6.205', 1516) #this is for SIP project OBU
    send_address = ('192.168.0.104', 1517) # ip address for OBU
    v2m_address = ('192.168.0.101', 10005)  # v2m means the address from vsp device to mmitss.
    print('run')
    #fake_bsm_file = '20250326-150755_20250326-151156_BSM.txt'
    #fake_bsm_file = '1528-1535_S2N_Qline.txt'
    fake_bsm_file = 'M1_BSM/Warren_N2S.txt'
    #fake_bsm_file = '1548_1556_N2S_Qline.txt'
    #fake_bsm_file = 'Ellsworth_StoneSchool_E2W.txt'
    f = open(fake_bsm_file)
    msg_set = []
    for i in f:
        msg_set.append(i.strip('\n'))
    distribute_Bsm(msg_set, v2m_address, send_address)
