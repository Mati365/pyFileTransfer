import socket
import sys
import struct
import os
import pickle
import math

from threading import Thread
from enum import IntEnum
from .. import settings

class Flags(IntEnum):
    BEGIN_COPYING = 0x1
    STOP_COPYING = 0x2
flag_response = struct.Struct("I")

class P2PClient:
    # Simple core thread that sends data to server
    class __ClientThread__(Thread):
        @staticmethod
        def list_files(dir):
            """ List all files in directory without rootpath
            :param dir: Directory
            :return:    (files, total_size)
            """
            total = []
            total_size = 0
            root_path = ""
            for (root, dirs, files) in os.walk(dir):
                if not len(total):
                    root_path = root

                for file in files:
                    path = root.replace(root_path, "") + "/" + file
                    size = os.path.getsize(root_path + path)

                    total.append((path, size))
                    total_size += size

            return (total, total_size, root_path)

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

        def upload_files(self, files):
            # Send list of all files to transfer
            self.client_sock.send(pickle.dumps(files))
            for (file, size) in files[0]:
                for chunk in self.read_from_file(files[2] + file, settings.block_size):
                    self.client_sock.send(chunk)

        def send_to(self, address, path="", files=()):
            """ Sending files to socket
            :param address: IP address of computer
            :param files:   List of files
            """
            if path != "":
                files = self.list_files(path)

            self.client_sock = socket.socket()
            self.client_sock.connect((address, settings.ports["transfer"]))
            with self.client_sock as s:
                if flag_response.unpack(s.recv(4))[0] == Flags.BEGIN_COPYING:
                    self.upload_files(files)
                else:
                    print("Computer doesn't accept connection!")

    # Simple server thread that downloads data from core
    class __ServerThread__(Thread):
        def __init__(self):
            Thread.__init__(self)

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

        def receive_data(self, conn):
            """ Receive files from core
            :param conn: Client socket
            :return:
            """
            conn.send(flag_response.pack(Flags.BEGIN_COPYING))
            (file_list, total_size, root_path) = pickle.loads(conn.recv(4096))

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
                        f.write(conn.recv((settings.block_size + total_size) if total_size < 0 else settings.block_size))

        def run(self):
            with self.server_sock as s:
                while 1:
                    (conn, (address, port)) = s.accept()
                    if True:
                        self.receive_data(conn)
                    conn.close()

    # Create both client and server
    def __init__(self):
        self.server = self.__ServerThread__()
        self.client = self.__ClientThread__()