import socket, sys
import os
import time
import string, random

BUFFER_SIZE = 1024


# /home/Ofek1
# /home/Ofek2
# text
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


def add_client_to_dictionary(dictionary, addr, client_id):
    client_id_folder = client_id[0:15]
    if client_id_folder not in dictionary:
        dictionary[client_id_folder] = []


UTF = "UTF-8"
IGNORE = "ignore"


def get_size(msg):
    sum = 0
    for i in msg:
        sum += 1
    return str(sum).zfill(12).encode('utf-8')


def get_client_id_folder(client_id):
    return client_id[0:15]


def create_folder(folder_path):
    try:
        os.makedirs(folder_path)
        print("created folder " + folder_path)
    except Exception as e:
        print("folder " + folder_path + " already exists.")


def send_all_folder(client_id_folder, s, get_only_modified = False,
                                         last_update_time = None):
    dir_path = client_id_folder
    now = time.time()
    if last_update_time is None:
        last_update_time = now
    for (root, dirs, files) in os.walk(dir_path, topdown=True):
        for folder in dirs:
            folder_loc = os.path.join(root, folder)
            if not (os.listdir(folder_loc)):
                msg = ("send-dir" + "@@@" + str(folder_loc)).encode('utf-8')
                msg_len = get_size(msg)
                if not (get_only_modified and now - last_update_time <= 0):
                    s.send(msg_len)
                    s.send(msg)

        for file in files:
            fileloc = os.path.join(root, file)
            with open(fileloc, "rb") as f:
                size = os.path.getsize(fileloc)
                filedata = "send-file@@@" + str(file) + "@@@" + str(size) + "@@@" + str(fileloc)
                msg = filedata.encode('utf-8')
                sum = get_size(msg)
                if not (get_only_modified and now - last_update_time <= 0):
                    s.send(sum)
                    s.send(filedata.encode('utf-8'))
                    while True:
                        # read the bytes from the file
                        bytes_read = f.read(BUFFER_SIZE)
                        if not bytes_read:
                            # file transmitting is done
                            break
                        s.sendall(bytes_read)
    msg = "finish".encode('utf-8')
    sum = get_size(msg)
    s.send(sum)
    s.send(msg)


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
        client_id = ""
        try:
            length_of_packet = int(request)
        except:
            length_of_packet = 1024
        request = connection.recv(length_of_packet).decode(UTF, IGNORE)

        request_parts = request.split("@@@")
        command = request_parts[0]
        if command == "register":
            client_id = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for i in range(128))
            print(client_id)
            add_client_to_dictionary(dictionary, addr, client_id)
            connection.send(client_id.encode())
        elif command == "hello":
            client_id = request_parts[1]
            client_id_folder = client_id[0:15]
            client_folder = request_parts[2]
            is_first_hello = request_parts[3]
            add_client_to_dictionary(dictionary, addr, client_id)
            dictionary[client_id_folder].append((
                addr[0], client_folder))
            create_folder(client_id_folder)
            if is_first_hello.upper() == "TRUE":
                create_folder(client_id_folder)
                send_all_folder(client_id_folder, connection)
        elif command == "ask-changed":
            time_step = float(request_parts[1])
            send_all_folder(client_id_folder, connection, True, time_step)
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
