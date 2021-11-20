import os
import random
import socket
import string
import sys
import time

BUFFER_SIZE = 1024
MESSAGE_LENGTH_HEADER_SIZE = 12
CLIENT_SHORT_ID_LENGTH = 15
# the format of encoding and decoding data.
UTF = "UTF-8"
# ignores undesired parts of the decoding.
IGNORE = "ignore"
# separation between command parts.
DELIMITER = "@@@"
ID_LENGTH = 128
EMPTY_ID = "empty_id"
EMPTY_FOLDER = "empty_folder"
EMPTY_STRING = ""
WRITE_BYTES = "wb+"
SLEEP_INTERVAL = 2
TRUE = "TRUE"
# commands.
SEND_DIR = "send-dir"
READ_BYTES = "rb"
SEND_FILE = "send-file"
FINISH = "finish"
REGISTER = "register"
ALERT_MOVED_FOLDER = "alert-moved-folder"
ALERT_DELETED_FOLDER = "alert-deleted-folder"
HELLO = "hello"
ASK_CHANGED = "ask-changed"
SEND_DIR = "send-dir"
SEND_FILE = "send-file"

# gets id of client, and dictioanry that maps
# between id to folder, and returns the short id
# (15 first digits). for example, ABcdefg12356683.
def get_id_by_addr(dictionary, ip):
    # the dictionary is for example:
    # { 'ABcdefg12356683', [('25.123.134.21', 'ofek/noam/temp')] }
    for client_id, value in dictionary.items():
        # if the value is none then continue.
        if value is None or len(value) == 0 or value == []:
            continue
        client_ip = value[0][0]
        if client_ip == ip:
            return client_id
    return EMPTY_ID


# gets id of client, and dictioanry that maps
# between id to folder, and returns the dir path
# of the folder. for example, /home/Ofek1.
def get_folder_by_id(dictionary, id):
    # the dictionary is for example:
    # { 'ABcdefg12356683', [('25.123.134.21', 'ofek/noam/temp')] }
    for client_id, value in dictionary.items():
        if id[:15] == client_id:
            client_folder = value[0][1]
            return client_folder
    return EMPTY_FOLDER


# the port in the first argument.
PORT_INDEX = 1
LISTEN_AMOUNT = 5
HOST_IP = ''
# the server is TCP, because it transfers files.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server.bind((HOST_IP, int(sys.argv[PORT_INDEX])))
except Exception as e:
    print(e)
    print("An invalid port was entered.");

server.listen(LISTEN_AMOUNT)

# the dictioanry maps
# between id to folder, and returns the short id (15 first digits)
# the dictionary is for example:
# { 'ABcdefg12356683', [('25.123.134.21', 'ofek/noam/temp')] }
dictionary = {}

# the host that the machine is on.
host = socket.gethostname()


# adds new client to the dictionary.
def add_client_to_dictionary(dictionary, client_id):
    client_id_folder = get_client_id_folder(client_id)
    # if the client is not registered, add it to dictionary.
    if client_id_folder not in dictionary:
        dictionary[client_id_folder] = []


# gets a message, and returns the size of the message.
# there are 12 digits to store the size, it's required
# since by this way the receiver will know how much
# bytes to read from the buffer.
# 12 digits, means the biggest message can be 999GB
# since 999,999,999,999 = 999GB
def get_size(msg):
    sum = 0
    # goes over the message and counts the letters
    for i in msg:
        sum += 1
    return str(sum).zfill(MESSAGE_LENGTH_HEADER_SIZE).encode(UTF)


# gets a client id which is 128 charcters,
# then, returns 15 digit id.
def get_client_id_folder(client_id):
    return client_id[:CLIENT_SHORT_ID_LENGTH]


# create a folder on the server side.
def create_folder(folder_path):
    try:
        os.makedirs(folder_path)
        print("created folder " + folder_path)
    except Exception as e:
        # if the folder is exists then it will print so.
        print("folder " + folder_path + " already exists.")


# sends all folders and files in given folder.
# the client_id_folder is for example: ABcdefg12356683
# the conn is the socket of the client.
# get_only_modified - is when the client wants only the changes
# if it's false, then it means clone for the first time.
def send_all_folder(client_id_folder, conn, get_only_modified=False,
                    last_update_time=None):
    dir_path = client_id_folder
    # goes over all the folders in the folder.
    for (root, dirs, files) in os.walk(dir_path, topdown=True):
        for folder in dirs:
            folder_loc = os.path.join(root, folder)
            if not (os.listdir(folder_loc)):
                # sends the directory to the server.
                msg = (SEND_DIR + DELIMITER + str(folder_loc)).encode(UTF)
                msg_len = get_size(msg)
                # os.path.getmtime - means the date it was modified.
                if (not get_only_modified) or (get_only_modified and
                         os.path.getmtime(folder_loc) - last_update_time > 0):
                    conn.send(msg_len)
                    conn.send(msg)

        # goes over all the file and sends them.
        for file in files:
            file_location = os.path.join(root, file)
            with open(file_location, READ_BYTES) as f:
                # opens a file and sends all of it.
                size = os.path.getsize(file_location)
                file_data = DELIMITER.join([SEND_FILE, str(file), str(size), str(file_location)])
                msg = file_data.encode(UTF)
                sum = get_size(msg)
                if (not get_only_modified) or (get_only_modified and os.path.getmtime(file_location) - last_update_time > 16):
                    conn.send(sum)
                    conn.send(file_data.encode(UTF))
                    while True:
                        # read the bytes from the file
                        bytes_read = f.read(BUFFER_SIZE)
                        if not bytes_read:
                            # file transmitting is done
                            break
                        conn.sendall(bytes_read)
    # when it finishes it says it to the client, so it will know.
    msg = FINISH.encode(UTF)
    sum = get_size(msg)
    conn.send(sum)
    conn.send(msg)
# if client told the server about change in its folder,
# the server will keep it in a list, and when another client
# with the same id will come the server will tell him
# to update itself as it should.
def add_changes(changes, key, request):
    if key not in changes:
        changes[key] = []
    changes[key].append((request, time.time()))

# the key is client_id+client_folder and the value is the list
# of changes that the client should make in order to be
# up to date.
changes = {}

# the server sends to the client
# important changes such as deletion and moving folders.
# it's important before the client gets files.
def send_important_folder_changes(dictionary, client_id, changes, my_last_update_time, connection):
    client_folder = get_folder_by_id(dictionary, client_id)
    for key in changes.keys():
        if key.startswith(client_id) and not (key.endswith(client_folder)):
            relevant_changes = changes[key]
            for request, time_was_changed in relevant_changes:
                if time_was_changed - my_last_update_time:
                    connection.send(request.encode())


client_id = EMPTY_STRING
while True:
    connection, addr = server.accept()
    print('connected in address:', addr)
    print("waiting...")
    request = ""
    # until finished was not receive, handle the client.
    while True:
        request = connection.recv(MESSAGE_LENGTH_HEADER_SIZE)
        request = request.decode(UTF, IGNORE)
        try:
            length_of_packet = int(request)
        except Exception as e:
            #print(e)
            #raise e
            length_of_packet = BUFFER_SIZE
        request = connection.recv(length_of_packet).decode(UTF, IGNORE)
        print(request)
        request_parts = request.split(DELIMITER)
        command = request_parts[0]
        # if it's the first time of the client, then it gets ID.
        if command == REGISTER:
            client_id = EMPTY_STRING.join(
                random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for i in range(ID_LENGTH))
            print(client_id)
            add_client_to_dictionary(dictionary, client_id)
            connection.send(client_id.encode())
        # if the client tells about moving folder, the server keeps it
        # and will update other connections with the same client_id.
        elif command == ALERT_MOVED_FOLDER:
            client_id = request_parts[3]
            client_folder = get_folder_by_id(dictionary, client_id)
            add_changes(changes, client_id + client_folder, request)
            # /home/noam
            client_folder = get_folder_by_id(dictionary, client_id)
            # Acdbhd1348
            client_dir = get_client_id_folder(client_id)
            old_folder_path = request_parts[1]
            # Acdbhd1348/home/noam
            old_folder_path = old_folder_path.replace(client_folder, client_dir)
            new_folder_path = request_parts[2]
            # Acdbhd1348/home/example
            new_folder_path = new_folder_path.replace(client_folder, client_dir)
            os.rename(old_folder_path, new_folder_path)
        elif command == "alert-moved-file":
            client_id = request_parts[3]
            client_folder = get_folder_by_id(dictionary, client_id)
            add_changes(changes, client_id + client_folder, request)
            # /home/noam
            client_folder = get_folder_by_id(dictionary, client_id)
            # Acdbhd1348
            client_dir = get_client_id_folder(client_id)
            old_file_path = request_parts[1]
            # Acdbhd1348/home/noam
            old_file_path = old_folder_path.replace(client_folder, client_dir)
            new_file_path = request_parts[2]
            # Acdbhd1348/home/example
            new_file_path = new_file_path.replace(client_folder, client_dir)
            os.rename(old_file_path, new_file_path)
        # if the client tells the server about deleting a folder
        # it will keep it, and will update other clients with the same id.
        # in the meantime, the server deletes the folder in its side.
        elif command == "alert-deleted-file":
            client_id = request_parts[2]
            # /home/noam
            client_folder = get_folder_by_id(dictionary, client_id)
            # /home/noam/example
            path_in_file = request_parts[1]
            # Acdbhd1348
            client_dir = get_client_id_folder(client_id)
            # Acdbhd1348/home/noam
            path_to_delete = path_in_file.replace(client_folder, client_dir)
            # the server delete the folder in its side.
            os.remove(path_to_delete)
            add_changes(changes, client_id + client_folder, request)
        elif command == ALERT_DELETED_FOLDER:
            client_id = request_parts[2]
            # /home/noam
            client_folder = get_folder_by_id(dictionary, client_id)
            # /home/noam/example
            path_in_client = request_parts[1]
            # Acdbhd1348
            client_dir = get_client_id_folder(client_id)
            # Acdbhd1348/home/noam
            path_to_delete = path_in_client.replace(client_folder, client_dir)
            # the server delete the folder in its side.
            for root, folders, files in os.walk(path_to_delete, topdown=False):
                for name_of_file in files:
                    os.remove(os.path.join(root, name_of_file))
                for name_of_file in folders:
                    os.rmdir(os.path.join(root, name_of_file))
            add_changes(changes, client_id + client_folder, request)
        # hello is send every time the client starts connection with the server.
        # in this way the server knows the client id, and client does not have to
        # send it in every request as parameter.
        elif command == HELLO:
            client_id = request_parts[1]
            client_id_folder = client_id[:CLIENT_SHORT_ID_LENGTH]
            client_folder = request_parts[2]
            is_first_hello = request_parts[3]
            add_client_to_dictionary(dictionary, client_id)
            dictionary[client_id_folder].append((
                addr[0], client_folder))
            create_folder(client_id_folder)
            # if it's the first hello, then clone
            # give the client all the changes it needs.
            if is_first_hello.upper() == TRUE:
                create_folder(client_id_folder)
                send_all_folder(client_id_folder, connection)
        # the client asks the server if there was a change.
        elif command == ASK_CHANGED:
            client_id = request_parts[2]
            my_last_update_time = float(request_parts[1])
            # the server tell the client about moving folders.
            send_important_folder_changes(dictionary, client_id, changes, my_last_update_time, connection)
            # the server sends the file to the client.
            send_all_folder(client_id_folder, connection, True, my_last_update_time)
            connection.close()
            break
        elif command == SEND_DIR:
            folder_path = request_parts[1]
            client_id = request_parts[2]
            client_id = get_id_by_addr(dictionary, addr[0])
            client_folder = get_folder_by_id(dictionary, client_id)
            folder_path = folder_path.replace(client_folder, client_id)
            # the server creates directory as the client told him.
            create_folder(folder_path)
        elif command == SEND_FILE:
            # the server receives a file from the client.
            file_name = request_parts[1]
            file_size = int(request_parts[2])
            file_path = request_parts[3]
            client_id = request_parts[4]
            client_id = get_id_by_addr(dictionary, addr[0])
            client_folder = get_folder_by_id(dictionary, client_id)
            file_path = file_path.replace(client_folder, client_id[:CLIENT_SHORT_ID_LENGTH])
            folder = file_path.replace(file_name, EMPTY_STRING)
            create_folder(folder)
            f = open(file_path, WRITE_BYTES)
            data = connection.recv(file_size)
            print("Writing to file...")
            f.write(data)
            f.close()
        elif command == FINISH:
            connection.close()
            print("Finished and went to wait to other clients.")
            break
        time.sleep(SLEEP_INTERVAL)