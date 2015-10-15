import socket
import ipaddress

from threading import Thread
from ..tools import get_milliseconds, create_interval
from ..settings import ports


# Device visible in device list
class NetworkHost:
    def __init__(self, address, last_seen=get_milliseconds()):
        self.last_seen = last_seen
        self.address = address

    def is_active(self):
        """ Check is device active
        :return: True if device is still active
        """
        return get_milliseconds() - self.last_seen <= 3000

# Client that contains deivces list
class DeviceList(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.local_ip = DeviceList.get_local_ip()
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
        self.socket.bind(("", ports["broadcast"]))

    @staticmethod
    def get_local_ip():
        """ Get computer's local ip adress
        :return: IP address
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
              self.socket.sendto("".encode("utf-8"), ("255.255.255.255", ports["broadcast"]))
            , self.__reload_list()
        ), 1)

        # Fetch computer hostname and ip in network
        while True:
            (message, address) = self.socket.recvfrom(ports["broadcast"])
            address = socket.getfqdn(address[0])

            if address == self.local_ip:
                if address in self.devices:
                    self.devices[address].last_seen = get_milliseconds()
                else:
                    self.devices[address] = NetworkHost(address)
