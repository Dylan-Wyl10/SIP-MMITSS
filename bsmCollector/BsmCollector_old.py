#!/usr/bin/env python
"""
Modified script for receiving UDP packets, converting them to hexadecimal,
identifying the type of message in a case-insensitive manner, and saving to a text file
named after the message type, with parameters configured from a JSON file.
"""

import socket
import time
import binascii
import os
import json
from datetime import datetime

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

def save_to_file(directory, message_type, content):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_path = os.path.join(directory, f"{timestamp}_{message_type}.txt")
    with open(file_path, 'a') as file:
        file.write(content + '\n')

def load_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)

def identify_message_type(hex_data, message_identifiers):
    hex_data_lower = hex_data.lower()  # convert hex data to lowercase to make the search case-insensitive
    for message_type, identifier in message_identifiers.items():
        print(hex_data_lower, identifier.lower())
        index = hex_data_lower.find(identifier.lower())  # search for the identifier in the message
        if index != -1:
            print('Yes')
            return message_type, index
    return None

def main():
    config = load_config("bsm_collector_config.json")
    ip_address = config["ip_address"]
    port_number = config["port_number"]
    directory_path = config["directory_path"]
    max_messages = config["max_messages"]
    message_identifiers = config["message_identifiers"]

    # Ensure the provided directory exists
    os.makedirs(directory_path, exist_ok=True)

    address = (ip_address, port_number)
    udp = UDP(address)

    message_count = 0
    while message_count < max_messages:
        packet = udp.receive()
        if packet is not None:
            hex_data = packet.hex()
            message_type, start_index = identify_message_type(hex_data, message_identifiers)
            if message_type:
                sliced_message = hex_data[start_index:]  # slice the message from the identifier
            if message_type:
                print("this is the {}th data".format(str(message_count)),hex_data)
                save_to_file(directory_path, message_type, sliced_message)
                message_count += 1

if __name__ == "__main__":
    main()
