import sys
import socket
import ipaddress
import time
import os

from threading import Thread, Timer
from sys import platform

get_milliseconds = lambda: int(round(time.time() * 1000))
def create_interval(func, time):
    def wrapper():
        func()
        create_interval(func, time)
    return Timer(time, wrapper).start()

# Device
class Device:
    def __init__(self, address, last_seen=get_milliseconds()):
        self.last_seen = last_seen
        self.address = address

        self.send_files('.')

    @staticmethod
    def get_file_list(path):
        files = []
        for root, dirnames, filenames in os.walk(path):
            for file in filenames:
                files.append(root + '/' + file)
        return files

    def send_files(self, path):
        """ Send files or folders to device
        :param path: Path to folder or file
        """
        print(Device.get_file_list(path))

    def is_active(self):
        """ Check is device active
        :return: True if device is still active
        """
        return get_milliseconds() - self.last_seen <= 3000

# Client that contains deivces list
class Client(Thread):
    def __init__(self, max_connections=8, port=12345):
        Thread.__init__(self)

        self.local_ip = Client.get_local_ip()
        self.port = port
        self.devices = {}
        self.__open_sockets()

    def __open_sockets(self):
        """ Create app sockets
        :param port: App port
        :return:
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.bind(("", self.port))

    @staticmethod
    def get_local_ip():
        """ Get computer's local ip adress
        :return: IP address string
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("gmail.com", 80))
            return str(ipaddress.IPv4Address(s.getsockname()[0]))

    def __reload_list(self):
        """ Remove inactive devices from list
        """
        self.devices = {key: device for key, device in self.devices.items() if device.is_active()}

    def run(self):
        """ Client service broadcast message about self through
        local network.
        """
        create_interval(lambda:(
              self.socket.sendto("".encode("utf-8"), ("255.255.255.255", self.port))
            , self.__reload_list()
        ), 1)

        # Fetch computer hostname and ip in network
        while True:
            (message, address) = self.socket.recvfrom(self.port)
            address = socket.getfqdn(address[0])

            if address == self.local_ip:
                if address in self.devices:
                    self.devices[address].last_seen = get_milliseconds()
                else:
                    self.devices[address] = Device(address)

def main():
    Client().start()

if __name__ == "__main__":
    sys.exit(main() or 0)