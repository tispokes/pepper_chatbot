#!/usr/bin/env python2

# # This file contains a test for the socket with
# a fixed file name and print the answer from
# the backend

import socket

HOST = 'pepper-chatbot.informatik.fh-nuernberg.de'
PORT = 4444
FILE = 'Lars-wo_finde_ich_Raum_HW013.wav'
MARKUP_OPENING_CHAR = '['
BUFFER_SIZE = 1024 # same as in server

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("[+] Connecting to " + str(HOST) + ":" + str(PORT))
s.connect((HOST, PORT))
print("[+] Connected.")

def markup_parser(text):
    print(text)

with open(FILE, "rb") as f:
    while True:
        # read the bytes from the file
        bytes_read = f.read(BUFFER_SIZE)
        if not bytes_read:
            f.close()
            s.send(b"DONE")
            print("DONE SENDING")
            # file transmitting is done
            data = s.recv(1024)
            s.close()
            break
        s.sendall(bytes_read)

print(len(data))
print(data)
if len(data) > 2:
    words = data.split()
    sentence = ""
    for word in words:
        if word[0] == MARKUP_OPENING_CHAR:
            markup_parser(word[1:-1])
            continue
        print(word)
