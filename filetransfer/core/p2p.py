import socket
import sys
import struct
import os
import pickle
import math
import re

from queue import Queue
from threading import Thread
from enum import IntEnum

from .. import settings
from .scanner import DeviceScanner

class Flags(IntEnum):
    BEGIN_COPYING = 0x1
    STOP_COPYING = 0x2
int_response = struct.Struct("I")

# Simple server thread that downloads data from core
class Server(Thread):
    def __init__(self, handler):
        Thread.__init__(self, daemon = True)
        self.handler = handler

        self.__create_server()
        self.start()

    def __create_server(self):
        """ Create P2P server
        """
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_sock.bind(("", settings.ports["transfer"]))
            self.server_sock.listen(1)
        except socket.error as msg:
            print("Cannot create P2P server: " + str(msg))
            sys.exit()

    def run(self):
        with self.server_sock as s:
            while 1:
                (conn, address) = s.accept()
                self.handler.on_accept_connection_prompt(address[0], Server.__ClientThread__(conn))

    class __ClientThread__(Thread):
        def __init__(self, conn):
            Thread.__init__(self, daemon=True)
            self.conn = conn
            self.q = Queue()

        def accept_connection(self):
            """ Accept connection and begin copying
            """
            self.conn.send(int_response.pack(Flags.BEGIN_COPYING))
            self.start()

        def refuse_connection(self):
            """ Refuse connection and close socket
            """
            self.conn.send(int_response.pack(Flags.STOP_COPYING))
            self.conn.close()

        def receive_data(self):
            """ Receive files from core
            """
            blocks = int_response.unpack(self.conn.recv(4))[0]

            for block in range(0, blocks):
                # Receive block header
                block_header_size = int_response.unpack(self.conn.recv(4))[0]
                (file_list, total_size, root_path) = pickle.loads(self.conn.recv(block_header_size))

                for file in file_list:
                    # Create file previous chunk is empty
                    # Create directory if not exists
                    dir = os.path.abspath("../download/" + os.path.dirname(file[0]))
                    if not os.path.exists(dir):
                        os.makedirs(dir)

                    # Close previous file
                    with open(dir + "/" + os.path.basename(file[0]), "wb+") as f:
                        total_size = file[1]
                        for i in range(0, math.ceil(file[1] / settings.block_size)):
                            total_size -= settings.block_size
                            f.write(self.conn.recv((settings.block_size + total_size) if total_size < 0 else settings.block_size))

        def run(self):
            self.receive_data()
            self.conn.close()

# Simple core thread that sends data to server
class Client:
    def __init__(self, handler):
        self.handler = handler

    @staticmethod
    def read_from_file(filename, chunk_size):
        """ Reads chunk of binary data from file and yield it
        :param filename:    Path to file
        :param chunk_size:  Block size
        :return: Binary data
        """
        with open(filename, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if data:
                    yield data
                else:
                    break

    def upload_files(self, blocks):
        # Send number of blocks
        self.client_sock.send(int_response.pack(len(blocks)))
        for block in blocks:
            # Send block header
            block_header = pickle.dumps(block)
            self.client_sock.send(int_response.pack(len(block_header)))
            self.client_sock.send(block_header)

            # Send files
            for (file, size) in block[0]:
                for chunk in self.read_from_file(block[2] + file, settings.block_size):
                    self.client_sock.send(chunk)

    def begin_copying(self, address, blocks):
        """ Sending files to socket
        :param address: IP address of computer
        :param blocks:  List of dirs
        """
        self.client_sock = socket.socket()
        self.client_sock.connect((address, settings.ports["transfer"]))
        with self.client_sock as s:
            if int_response.unpack(s.recv(4))[0] == Flags.BEGIN_COPYING:
                self.upload_files(blocks)
            else:
                self.handler.on_refuse_connection_prompt()

class P2PClient:
    def __init__(self, handler):
        self.server = Server(handler)
        self.scanner = DeviceScanner(handler)

    @staticmethod
    def list_files(dir):
        """ List all files in directory without rootpath
        :param dir: Directory
        :return:    (files, total_size)
        """
        def get_file_info(file, folder_root="", root_path=""):
            path = folder_root.replace(root_path, "") + "/" + file
            return ( path
                   , os.path.getsize(root_path + path)
                   )

        # If file return array with one file
        if os.path.isfile(dir):
            root = os.path.dirname(dir)
            file = get_file_info(os.path.basename(dir), root_path=root)
            return ([file], file[1], root)

        total = []
        total_size = 0
        root_path = ""

        for (folder_root, dirs, files) in os.walk(dir):
            if not len(total):
                root_path = re.sub("(\/(?:[^\/]*))$", "", folder_root)

            for file in files:
                total.append(get_file_info(file, folder_root, root_path))
                total_size += total[-1][1]

        return (total, total_size, root_path)

    def send_files(self, address, blocks):
        def worker():
            Client(self.server.handler).begin_copying(address, blocks)
        Thread(target=worker).start()
