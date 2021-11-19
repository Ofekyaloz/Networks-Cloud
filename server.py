import socket, sys
import os
import time

#/home/Ofek1
#/home/Ofek2
#text
def get_id_by_addr(dictionary, addr):
    for client_id, value in dictionary.items():
        if (value is None or len(value) == 0 or value == []):
            continue
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


def add_client_to_dictionary(dictionary, addr):
    client_id_folder = client_id[0:15]
    if client_id_folder not in dictionary:
        dictionary[client_id_folder] = []

UTF = "UTF-8"
IGNORE = "ignore"


def create_folder(folder_path):
    try:
        os.makedirs(folder_path)
        print("created folder " + folder_path)
    except Exception as e:
        print("folder " + folder_path + " already exists.")


while True:
    connection, addr = server.accept()  # Establish connection with client.
    print('Connected:', addr)
    print("Waiting for requests...")
    request = ""
    # if len(request) == 0:
    # 000000000012###
    # hello@@@cnakjcndak.cao
    while True:
        request = connection.recv(12)
        request = request.decode(UTF, IGNORE)
        try:
            length_of_packet = int(request)
        except:
            length_of_packet = 1024
        request = connection.recv(length_of_packet).decode(UTF, IGNORE)

        request_parts = request.split("@@@")
        command = request_parts[0]
        if command == "register":
            client_id = os.urandom(128)
            add_client_to_dictionary(dictionary, addr)
            connection.send(client_id)
        elif command == "hello":
            client_id = request_parts[1]
            client_id_folder = client_id[0:15]
            client_folder = request_parts[2]
            add_client_to_dictionary(dictionary, addr)
            dictionary[client_id_folder].append((
                addr[0], client_folder))
            create_folder(client_id_folder)
        elif command == "send-dir":
            folder_path = request_parts[1]
            client_id = get_id_by_addr(dictionary, addr[0])
            client_folder = get_folder_by_id(dictionary, client_id)
            folder_path = folder_path.replace(client_folder, client_id)
            create_folder(folder_path)
        elif command == "send-file":
            file_name = request_parts[1]
            file_size = int(request_parts[2])
            file_path = request_parts[3]
            client_id = get_id_by_addr(dictionary, addr[0])
            # /home/ofek/Desktop/temp/ofek
            client_folder = get_folder_by_id(dictionary, client_id)
            file_path = file_path.replace(client_folder, client_id[0:15])
            folder = file_path.replace(file_name, "")
            create_folder(folder)
            f = open(file_path, 'wb+')
            data = connection.recv(file_size)
            print("Writing to file...")
            f.write(data)
            f.close()
        elif command == "finish":
            connection.close()
            print("Finished and went to wait to other clients.")
            break
        time.sleep(2)


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
