#!/usr/bin/env python2

import socket

BUFFER_SIZE = 1024 # same as in server
HOST = 'pepper-chatbot.informatik.fh-nuernberg.de'
PORT = 4444

class ClientSocket():
    def __init__(self):
        pass

    def send_file(self, filename):
        self.connect()
        with open(filename, "rb") as file:
            while True:
                bytes_read = file.read(BUFFER_SIZE)
                if not bytes_read:
                    file.close()
                    self.socket.send(b"DONE")
                    print("DONE SENDING")
                    # file transmitting is done
                    response = self.socket.recv(1024)
                    self.socket.close()
                    print(response)
                    return response
                # we use sendall to assure transimission in busy networks
                self.socket.sendall(bytes_read)

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[+] Connecting to " + str(HOST) + ":" + str(PORT))
        self.socket.connect((HOST, PORT))
        print("[+] Connected.")
