#/usr/bin/env python
"""
Author: Dylan
Date: 05/17/2022
Note: This work is used for :
    1. read fake BSM file and send to MMITSS VSP
"""
import time

import BSMEncoder
import socket
import folium
import numpy as np
from haversine import haversine, Unit


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

def decimal_convert(num):
    is_negative = num < 0
    num_str = str(abs(num))
    if len(num_str) <= 2:
        result = '0.' + num_str.zfill(2)
    else:
        result = num_str[:2] + '.' + num_str[2:]
    return '-' + result if is_negative else result

def bsm_vislz(msg_li):
    # obu_udp, mmitss_udp = UDP(obu_address), UDP(mmitss_address)
    print('yes')
    count = 0
    l = len(msg_li)
    locs = np.zeros((l,2))  # [x, y]
    for b in msg_li:
        if b[4:6] == '80':
            aa = bytearray.fromhex(b[8:])
        else:
            aa = bytearray.fromhex(b[6:])
        result_tmp = BSMEncoder.decode(aa)
        (id, secMark, msgCount, speed, heading, lat, lon, elev, length, width) = result_tmp
        print(f'id: {id}\nsecMark: {secMark}\nmsgCount: {msgCount}\nspeed: {speed}\nheading: {heading}\nlat: {lat}\nlon: {lon}\nelev: {elev}\nlength: {length}\nwidth: {width}')
        locs[count, :] = (decimal_convert(lat), decimal_convert(lon))
        count += 1
        print('yes')
    loc_avg = np.mean(locs, axis=0)
    m = folium.Map(loc_avg, zoom_start=14)  # lat lon
    for idx in range(locs.shape[0]):
        folium.CircleMarker(location=[locs[idx, 0], locs[idx, 1]], radius=1, color='blue',
                            fill='True', fill_color='blue').add_to(m)
    m.save("N2Sqline2.html")
    print('eys')


if __name__ == '__main__':
    # receive_address = ('0.0.0.0', 20001) #read from file
    # send_address = ('10.12.6.205', 1516) #this is for SIP project OBU
    # send_address = ('192.168.0.101', 1517) # ip address for OBU
    # v2m_address = ('192.168.0.102', 10005)  # v2m means the address from vsp device to mmitss.
    print('run')
    # fake_bsm_file = 'pudemo_BSM.txt'
    # fake_bsm_file = 'Ellsworth_StoneSchool_E2W.txt'
    fake_bsm_file = 'M1_Corrido_0326/1522follow_Baltimore2Warren.txt'
    f = open(fake_bsm_file)
    msg_set = []
    for i in f:
        msg_set.append(i.strip('\n'))
    bsm_vislz(msg_set)
