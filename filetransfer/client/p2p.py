import socket
import sys
import struct
import os
import pickle
import math

from threading import Thread
from enum import IntEnum

class Flags(IntEnum):
    BEGIN_COPYING = 0x1
    STOP_COPYING = 0x2
flag_response = struct.Struct("I")
block_size = 512

class P2PClient:
    # Simple client thread that sends data to server
    class __ClientThread__(Thread):
        def __init__(self, port=12346):
            Thread.__init__(self)
            self.port = port

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
                for chunk in self.read_from_file(files[2] + file, block_size):
                    self.client_sock.send(chunk)



        def send_to(self, dir, address=""):
            """ Sending files to socket
            :param dir:     Directory
            :param address: IP address of computer
            """
            self.client_sock = socket.socket()
            self.client_sock.connect((address, self.port))
            with self.client_sock as s:
                if flag_response.unpack(s.recv(4))[0] == Flags.BEGIN_COPYING:
                    self.upload_files(self.list_files(dir))
                else:
                    print("Computer doesn't accept connection!")

    # Simple server thread that downloads data from client
    class __ServerThread__(Thread):
        def __init__(self, port=12346):
            Thread.__init__(self)
            self.__create_server(port)

        def __create_server(self, port):
            """ Create P2P server
            :param port: Port
            """
            self.port = port
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.server_sock.bind(("", self.port))
                self.server_sock.listen(1)
            except socket.error as msg:
                print("Cannot create P2P server: " + str(msg))
                sys.exit()

        def receive_data(self, conn):
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
                    for i in range(0, math.ceil(file[1] / block_size)):
                        total_size -= block_size
                        f.write(conn.recv((block_size + total_size) if total_size < 0 else block_size))


        def run(self):
            with self.server_sock as s:
                while 1:
                    (conn, (address, port)) = s.accept()
                    if True:
                        self.receive_data(conn)
                    conn.close()

    def __init__(self):
        self.__ServerThread__().start()
        self.__ClientThread__().send_to("/home/mateusz/Pulpit/PycharmProjects/pyFileTransfer/filetransfer/")