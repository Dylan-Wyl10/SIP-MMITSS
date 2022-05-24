#!/usr/bin/env python
"""
Author: Dylan
Date: 02/17/2022
Note: This work is used for :
    1. receive bsm from VISSIM
    2. encode VISSIM bsm to J2735 BSM_Package
    3. forward J2735 BSM to OBU via UDP protocol
"""
###########################################################################

import BSMEncoder
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


def encodeBSM(string):
    string_hex = string.hex()
    msgCnt = int(string_hex[0: 8], 16) % 128
    temporaryID = str(int(string_hex[8: 24], 16))
    secMark = int(int(string_hex[24: 28], 16) / 100)  # [0 - 599]

    ##position
    lat = int(string_hex[28: 36], 16)
    lon = - (2 ** 32 - int(string_hex[36: 44], 16))
    elev = int(int(string_hex[44: 52], 16) / 100)  # what is the unit in Sean's case, current follow MMITSS encoding
    ## accuracy:
    semiMajor = 15
    semiMinor = 10
    orientation = 20
    speed = int(int(string_hex[52: 56], 16) / 2)
    heading = int(int(string_hex[56: 60], 16) / 1.25)
    angle = 5  # based on Sean's example
    ## accelerations:
    acc_long = 5
    acc_lat = 12
    acc_vert = 15
    acc_yaw = 200
    ## size
    length = int(int(string_hex[60: 64], 16) / 100)  # length out of range,
    width = int(int(string_hex[64: 68], 16) / 10)

    # temp = lon

    # print(int(string_hex[28: 36], 16))
    # print(temp, type(temp))
    x = BSMEncoder.encode(temporaryID, lon, lat, elev, semiMajor, semiMinor, orientation, speed, heading, angle,
                          acc_long, acc_lat, acc_vert, acc_yaw, length, width, msgCnt, secMark)
    # print(x)
    x_ = "001425" + x.hex()[0:74]
    bsm_tmp = "Version=0.7\n" + \
              "Type=BSM\n" + \
              "PSID=0x20\n" + \
              "Priority=7\n" + \
              "TxMode=ALT\n" + \
              "TxChannel=SCH\n" + \
              "TxInterval=0\n" + \
              "DeliveryStart=\n" + \
              "DeliveryStop=\n" + \
              "Signature=False\n" + \
              "Encryption=False\n" + \
              "Payload=" + x_

    bsm = bytes(bsm_tmp, 'utf-8')
    x = bytes.fromhex(x_)
    # x = bytes(x, 'utf-8')
    print(x)

    # (id, secMark, msgCount, speed, heading, lat, lon, elev, length, width) = BSMEncoder.decode(x)
    # print(f'id: {id}\nsecMark: {secMark}\nmsgCount: {msgCount}\nspeed: {speed}\nheading: {heading}\nlat: {lat}\nlon: {lon}\nelev: {elev}\nlength: {length}\nwidth: {width}')
    # print('#######################################################################')
    return bsm, x_


def saveBSM(r_address, payload_li):
    r_udp = UDP(r_address)
    bsm_string = r_udp.receive()
    if bsm_string is not None:
        #        print("bsm from vissim is: ", bsm_string)

        bsm_pkg, payload_hex = encodeBSM(bsm_string)
        # print("bsm package is:", bsm_pkg)
        # print("##########################################################")
        print("payload hex is:", payload_hex)
        payload_li.append(payload_hex)
        print("#########################################################")
    return payload_li


if __name__ == '__main__':
    receive_address = ('0.0.0.0', 20001)
    send_address = ('10.12.6.205', 1516)
    v2m_address = ('10.12.6.206', 10005)  # v2m means the address from vsp device to mmitss.
    print('run')
    file_opt = 'fake_bsm.txt'

    payload_li = []
    tick_count = 0
    while len(payload_li) < 850:
        payload_li = saveBSM(receive_address, payload_li)
    print(payload_li)
    with open(file_opt, "w") as f:
        for p in payload_li:
            f.write(p + "\n")

