import sys
import socket
import ipaddress
from threading import Thread, Timer

def create_interval(func, time):
    def wrapper():
        func()
        print("WORK!")
        create_interval(func, time)
    t = Timer(time, wrapper)
    t.start()
    return t

class Client(Thread):
    def __init__(self, max_connections=8, port=12345):
        Thread.__init__(self)

        self.max_connections = max_connections
        self.local_ip = Client.get_local_ip()
        self.port = port
        self.computer_lists = []

    @staticmethod
    def get_local_ip():
        """ Get computer's local ip adress
        :return: IP address string
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("gmail.com", 80))
            return str(ipaddress.IPv4Address(s.getsockname()[0]))

    def run(self):
        """ Client service broadcast message about self through
        local network.
        """
        app_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        app_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        app_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        app_socket.bind(("", self.port))
        create_interval(lambda:
            app_socket.sendto("".encode("utf-8"), ("255.255.255.255", self.port))
        , 1)
        while True:
            message, address = app_socket.recvfrom(self.port)
            if address[0] != self.local_ip:
                print(message, address)

def main():
    Client().start()

if __name__ == "__main__":
    sys.exit(main() or 0)