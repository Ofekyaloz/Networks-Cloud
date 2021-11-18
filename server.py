import socket, sys
import os


def get_id_by_addr(dictionary, addr):
    for client_id, value in dictionary.items():
        client_socket = value[0][0]
        if client_socket == addr:
            return client_id
    return "empty_id"


def get_folder_by_id(dictionary, id):
    for client_id, value in dictionary.items():
        if client_id == id:
            client_folder = value[0][1]
            return client_folder
    return "empty_folder"


PORT_INDEX = 1
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', int(sys.argv[PORT_INDEX])))
server.listen(5)
dictionary = {}

host = socket.gethostname()  # Get local machine name

port = 12345  # Reserve a port for your service.
# send-file,name,size
buffer = []
while True:
    connection, addr = server.accept()  # Establish connection with client.
    print('Connected:', addr)
    print("Waiting for requests...")
    request = ""
    # if len(request) == 0:
    # 000000000012###
    # hello@@@cnakjcndak.cao
    connection.settimeout(15)
    while True:
        try:
            request = connection.recv(12).decode()
            length_of_packet = int(request)
            request = connection.recv(length_of_packet).decode()

            request_parts = request.split("@@@")
            command = request_parts[0]
            if command == "hello":
                client_id = request_parts[1]
                client_id_folder = client_id[0:15]
                client_folder = request_parts[2]
                if client_id_folder not in dictionary:
                    dictionary[client_id_folder] = []
                dictionary[client_id_folder].append((addr, client_folder))
                try:
                    os.makedirs(client_id_folder)
                    print("created folder " + client_id_folder)
                except Exception as e:
                    print("folder " + client_folder + " already exists.");
            if command == "send-file":
                file_name = request_parts[1]
                file_size = int(request_parts[2])
                file_path = request_parts[3]
                client_id = get_id_by_addr(dictionary, addr)
                # /home/ofek/Desktop/temp/ofek - 1234
                # /home/ofek/Desktop/temp/ofek1 - 1234
                client_folder = get_folder_by_id(dictionary, client_id)
                file_path = file_path.replace(client_folder, client_id[0:15])
                f = open(file_path, 'wb')
                data = connection.recv(file_size)
                print("Writing to file...")
                f.write(data)
                f.close()
            print("Finished iteration in server.")
        except Exception as e:
            pass
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
