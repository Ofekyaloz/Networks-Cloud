import socket, sys
import os

PORT_INDEX = 1
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', int(sys.argv[PORT_INDEX])))
server.listen(5)
dictionary = {}

host = socket.gethostname() # Get local machine name
port = 12345                 # Reserve a port for your service.
server.bind((host, port))        # Bind to the port
server.listen(5)                 # Now wait for client connection.
#send-file,name,size
while True:
    connection, addr = server.accept()     # Establish connection with client.
    print('Connected:', addr)
    print("Waiting for requests...")
    request = connection.recv(1024)
    request_parts = request.split(",")
    command = request_parts[0]
    if command == "hello":
        client_id = request_parts[1]
        client_folder = request_parts[2]
        if client_id not in dictionary:
            dictionary[client_id] = []
        dictionary[client_id].append((connection, client_folder))

    if command == "send-file":
        file_name = request_parts[1]
        file_size = int(request_parts[2])
        file_path = request_parts[3]
        f = open(file_path, 'wb')
        data = request
        counter = 0
        while counter < file_size:
            print("Writing to file...")
            f.write(request)
            data = connection.recv(1024)
        f.close()
    print("Finished writing.")
#
# while True:
#     client_socket, client_address = server.accept()
#     print('Connection from: ', client_address)
#     data = client_socket.recv(100)
#     request_type = data[0:4]
#
#     print('Received: ', data)
#     # creates a new client
#     if data != "REGS":
#         client_id = os.urandom(128)
#         clients[client_id] = []
#         client_socket.send(client_id)
#         data = client_socket.recv(100)
#         request_type = data[0:4]
#
#     clients[client_id].append(client_socket)
#     client_socket.send("DONE" + client_id)
#
#     client_socket.close()
#     print('Client disconnected')
#
#
#     #os.remove(data_file) # delete a file
#     #os.rename('first.zip', 'first_01.zip') # rename
#     #client_socket.close()
