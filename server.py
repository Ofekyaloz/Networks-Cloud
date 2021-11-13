import socket, sys
import os

PORT_INDEX = 1
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', int(sys.argv[PORT_INDEX])))
server.listen(5)
clients = {}

while True:
    client_socket, client_address = server.accept()
    print('Connection from: ', client_address)
    data = client_socket.recv(100)
    request_type = data[0:4]

    print('Received: ', data)
    client_id = os.urandom(128)
    if clients[client_id] is None:
        clients[client_id] = []

    clients[client_id].append(client_socket)
    client_socket.send("DONE" + client_id)

    #client_socket.close()
