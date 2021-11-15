
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

    # creates a new client
    if data != "REGS":
        client_id = os.urandom(128)
        clients[client_id] = []
        client_socket.send(client_id)
        continue

    clients[client_id].append(client_socket)
    client_socket.send("DONE" + client_id)

    client_socket.close()
    print('Client disconnected')


    #os.remove(data_file) # delete a file
    #os.rename('first.zip', 'first_01.zip') # rename
