import os
import random
import socket
import string
import sys
import time

computer_to_os = {}
WINDOWS_SEP = "\\"
LINUX_SEP = "/"

# key : client_id
# value : computer_id
# value_of_value: changes of this computer id
changes = {}

def get_client_id_folder(client_id):
    return os.path.abspath(client_id[:CLIENT_SHORT_ID_LENGTH])

def get_other_slash():
    if os.sep == LINUX_SEP:
        return WINDOWS_SEP
    return LINUX_SEP

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
BIGGEST_SIZE_SOCKET = 100000
STANDARD_SIZE = 4096
CREATE_DIR = "create-dir"
READ_BYTES = "rb"
SEND_FILE = "send-file"
FINISH = "finish"
REGISTER = "register"
ALERT_MOVED_FOLDER = "alert-moved-folder"
ALERT_DELETED_FOLDER = "alert-deleted-folder"
ALERT_MOVED_FILE = "alert-moved-file"
ALERT_DELETED_FILE = "alert-deleted-file"
HELLO = "hello"
ASK_CHANGED = "ask-changed"
SEND_DIR = "send-dir"
SEND_FILE = "send-file"


def convert_path(path, old_slash):
    new_slash = os.sep
    return path.replace(old_slash, new_slash)

def adjust_path(path, old_slash, new_slash):
    return path.replace(old_slash, new_slash)

def get_computer_os_by_id(computer_id):
    if not (computer_id in computer_to_os.keys()):
        return LINUX_SEP
    return computer_to_os[computer_id]

def convert_to_os(path):
    if os.sep == LINUX_SEP:
        return path.replace(WINDOWS_SEP, LINUX_SEP)
    else:
        return path.replace(LINUX_SEP, WINDOWS_SEP)

def adjust_request_to_os(request, computer_id):
    request_parts = request.split(DELIMITER)
    command = request_parts[0]
    old_slash = os.sep
    new_slash = get_computer_os_by_id(computer_id)

    if command == ALERT_MOVED_FOLDER:
        old_folder_path = adjust_path(request_parts[1], old_slash, new_slash)
        new_folder_path = adjust_path(request_parts[2], old_slash, new_slash)
        request = request.replace(request_parts[1], old_folder_path)
        request = request.replace(request_parts[2], new_folder_path)

    elif command == ALERT_MOVED_FILE:
        old_file_path = adjust_path(request_parts[1], old_slash, new_slash)
        new_file_path = adjust_path(request_parts[2], old_slash, new_slash)
        request = request.replace(request_parts[1], old_file_path)
        request = request.replace(request_parts[2], new_file_path)

    elif command == ALERT_DELETED_FILE or command == ALERT_DELETED_FOLDER:
        path = adjust_path(request_parts[1], old_slash, new_slash)
        request = request.replace(request_parts[1], path)

    elif command == SEND_DIR:
        folder_path = adjust_path(request_parts[1], old_slash, new_slash)
        request = request.replace(request_parts[1], folder_path)

    elif command == SEND_FILE:
        file_path = adjust_path(request_parts[3], old_slash, new_slash)
        request = request.replace(request_parts[3], file_path)

    return request

# gets id of client, and dictioanry that maps
# between id to folder, and returns the dir path
# of the folder. for example, /home/Ofek1.
"""
def get_folder_by_id(dictionary, id, computer_id):
    # the dictionary is for example:
    # { 'ABcdefg12356683', {'computerIdAecnkdjsj', 'ofek/noam/temp'} }
    for client_id, value in dictionary.items():
        if id[:15] == client_id and computer_id in value.keys():
            return value[computer_id]
    return EMPTY_FOLDER
"""

# the port in the first argument.
PORT_INDEX = 1
LISTEN_AMOUNT = 5
HOST_IP = ''
# the server is TCP, because it transfers files.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print("bind to ", HOST_IP, int(sys.argv[PORT_INDEX]))
    server.bind((HOST_IP, int(sys.argv[PORT_INDEX])))
except Exception as e:
    print(e)
    print("An invalid port was entered.");

print("Listen amount", LISTEN_AMOUNT)
server.listen(LISTEN_AMOUNT)

# the dictioanry maps
# between id to folder, and returns the short id (15 first digits)
# the dictionary is for example:
# { 'ABcdefg12356683', [('25.123.134.21', 'ofek/noam/temp')] }
dictionary = {}

# the host that the machine is on.
host = socket.gethostname()


# adds new client to the dictionary.
def add_client_to_dictionary(dictionary, client_id, computer_id, path_to_folder):
    client_id_folder = get_client_id_folder(client_id)
    # if the client is not registered, add it to dictionary.
    if client_id_folder not in dictionary:
        dictionary[client_id_folder] = {}
    dictionary[client_id_folder][computer_id] = path_to_folder


# gets a message, and returns the size of the message.
# there are 12 digits to store the size, it's required
# since by this way the receiver will know how much
# bytes to read from the buffer.
# 12 digits, means the biggest message can be 999GB
# since 999,999,999,999 = 999GB
def get_size(msg):
    sum = 0
    # goes over the message and counts the letters
    if msg is int:
        print("*******" + msg + "******")
        msg = str(msg)
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
        if not os.path.isabs(folder_path):
            folder_path = os.path.abspath(folder_path)
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
def send_all_folder(client_id_folder, conn, computer_id, client_id, get_only_modified=False,
                    last_update_time=None):
    dir_path = os.path.abspath(client_id_folder)
    # goes over all the folders in the folder.
    for (root, dirs, files) in os.walk(dir_path, topdown=True):
        for folder in dirs:
            folder_loc = os.path.join(root, folder)
            folder_loc = os.path.relpath(folder_loc, dir_path)
            msg = SEND_DIR + DELIMITER + str(folder_loc)
            msg = adjust_request_to_os(msg, computer_id)
            # sends the directory to the server.
            msg = msg.encode(UTF)
            msg_len = get_size(msg)
            # os.path.getmtime - means the date it was modified.
            if (not get_only_modified) or (get_only_modified and
                                           os.path.getmtime(folder_loc) - last_update_time > 0):
                try:
                    conn.send(msg_len)
                    conn.send(msg)
                except Exception as e:
                    print(e)
        # goes over all the file and sends them.
        for file in files:
            try:
                file_location = os.path.join(root, file)
            except Exception as e:
                print(e)
            try:
                with open(file_location, READ_BYTES) as f:
                    # opens a file and sends all of it.
                    size = os.path.getsize(file_location)
                    request = DELIMITER.join([SEND_FILE, str(file), str(size),
                                              os.path.relpath(str(file_location),get_client_id_folder(client_id))])
                    request = adjust_request_to_os(request, computer_id)
                    msg = request.encode(UTF)
                    sum = get_size(msg)
                    if (not get_only_modified) or (
                            get_only_modified and os.path.getmtime(file_location) - last_update_time > 16):
                        conn.send(sum)
                        conn.send(msg)
                        data_left_to_read = file_size
                        while data_left_to_read > 0:
                            # read the bytes from the file
                            bytes_read = f.read(BUFFER_SIZE)
                            if not bytes_read:
                                # file transmitting is done
                                break
                            data_left_to_read -= len(bytes_read)
                            conn.sendall(bytes_read)
            except Exception as e:
                print(e)
    # when it finishes it says it to the client, so it will know.
    msg = FINISH.encode(UTF)
    sum = get_size(msg)
    conn.send(sum)
    conn.send(msg)


# if client told the server about change in its folder,
# the server will keep it in a list, and when another client
# with the same id will come the server will tell him
# to update itself as it should.
def add_changes(changes, client_id, computer_id, request, dictionary):
    short_id = client_id[:CLIENT_SHORT_ID_LENGTH]
    if short_id not in changes.keys():
        changes[short_id] = {}
        changes[short_id][computer_id] = []
    # key = ID(15 digits),
    # value {'acdd7831hhd': { 'acnakjcds' : "C:\" , "cdakjds": "C:\Example" } }

    for key, value in dictionary.items():
        for id, path in value.items():
            if id not in changes[short_id]:
                changes[short_id][id] = []

    # value = { "computerId", ["SEND-DIR"] }
    for key, value in changes.items():
        dictionary_changes = value
        for other_computer_id, updates in dictionary_changes.items():
            if other_computer_id != computer_id:
                changes[short_id][other_computer_id].append((request, time.time()))


# of changes that the client should make in order to be
# up to date.

def order(changes_for_client):
    lst = []
    for change in changes_for_client:
        request = change[0]
        if request.startswith(SEND_DIR):
            lst.append(change)

    for change in changes_for_client:
        request = change[0]
        if not request.startswith(SEND_DIR):
            lst.append(change)
    return lst


def delete_change_by_request(changes, client_id, computer_id, request):
    to_delete = None
    dict_computer = changes[client_id][computer_id]
    for change in dict_computer:
        req = change[0]
        if req == request:
            to_delete = change
    if to_delete is not None:
        changes[client_id][computer_id].remove(to_delete)

# the server sends to the client
# important changes such as deletion and moving folders.
# it's important before the client gets files.
def send_important_changes(dictionary, client_id, changes, my_last_update_time, connection, computer_id):
    # { 'ABcdefg12356683': {'computerIdAecnkdjsj': 'ofek/noam/temp', 'computerIdAecnkdjsj': 'ofek/noam/temp'} }

    short_id = client_id[:CLIENT_SHORT_ID_LENGTH]
    for short_id in changes.keys():
        # value = {'computerIdAecnkdjsj', ['ofek/noam/temp']}
        value = changes[short_id]
        if computer_id not in changes[short_id]:
            changes[short_id][computer_id] = []
        relevant_changes = value[computer_id]
        # relevant_changes = order(relevant_changes)
        updated = []
        for request, time_was_changed in relevant_changes:
            print("updated client: ", request)
            print("computer id: ", computer_id)
            request = adjust_request_to_os(request, computer_id)
            connection.send(get_size(request.encode()))
            connection.send(request.encode())
            if request.startswith("send-file"):
                send_file(connection, request.encode(), short_id)
            updated.append(request)

    key = client_id[:CLIENT_SHORT_ID_LENGTH]

    if key in changes.keys():
        if computer_id in changes[key].keys():
            # changes = { 'Client_id' : 'Cmp_Id1': [(ALERT, 1234), (ALERT, 1234)] }
            # [(ALERT, 1234)]
            for req in updated:
                delete_change_by_request(changes, short_id, computer_id, req)


# send file
def send_file(s, msg, client_dir, short_id):
    fileloc = msg.decode(UTF).split("@@@")[3]
    fileloc = fileloc.replace(client_dir, short_id)
    fileloc = fileloc.replace(EMPTY_FOLDER, short_id)
    fileloc = convert_path(fileloc, get_other_slash())
    with open(fileloc, READ_BYTES) as f:
        # msg = (DELIMITER.join([SEND_FILE, str(file), str(size), str(fileloc), str(client_id), computer_id])).encode(UTF)
        data_left_to_read = file_size
        while data_left_to_read > 0:
            # read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                # file transmitting is done
                break
            data_left_to_read -= len(bytes_read)
            s.sendall(bytes_read)


client_id = EMPTY_STRING
client_that_said_hello = []

while True:
    try:
        connection, addr = server.accept()
        print('connected in address:', addr)
    except Exception as e:
        print(e)
    print("waiting...")
    counter = 0
    request = ""
    # until finished was not receive, handle the client.
    while True:
        request = connection.recv(MESSAGE_LENGTH_HEADER_SIZE)
        request = request.decode(UTF, IGNORE)
        try:
            length_of_packet = int(request)
        except Exception as e:
            # print(e)
            # raise e
            length_of_packet = BUFFER_SIZE
        try:
            request = connection.recv(length_of_packet).decode(UTF, IGNORE)
        except Exception as e:
            print(e)
        if request != "":
            print(request)
        request_parts = request.split(DELIMITER)
        command = request_parts[0]
        # if it's the first time of the client, then it gets ID.
        if command == REGISTER:
            client_id = EMPTY_STRING.join(
                random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for i in
                range(ID_LENGTH))
            print(client_id)
            connection.send(client_id.encode())
            # connection.close()
        # if the client tells about moving folder, the server keeps it
        # and will update other connections with the same client_id.
        elif command == ALERT_MOVED_FOLDER:
            counter += 1
            separator = request_parts[5]
            computer_id = request_parts[4]
            computer_to_os[computer_id] = separator
            client_id = request_parts[3]
            add_changes(changes, client_id, computer_id, request, dictionary)
            # /home/noam
            # Acdbhd1348
            client_dir = get_client_id_folder(client_id)
            old_folder_path = os.path.join(get_client_id_folder(client_id),
                                           convert_path(request_parts[1], separator))
            # Acdbhd1348/home/noam
            new_folder_path = os.path.join(get_client_id_folder(client_id),
                                           convert_path(request_parts[2], separator))

            # Acdbhd1348/home/example
            try:
                os.rename(os.path.abspath(old_folder_path),
                          os.path.abspath(new_folder_path))
            except Exception as e:
                print(e)
            # connection.close()
            # connection.close()
        elif command == ALERT_MOVED_FILE:
            separator = request_parts[5]
            computer_id = request_parts[4]
            computer_to_os[computer_id] = separator
            client_id = request_parts[3]
            add_changes(changes, client_id, computer_id, request, dictionary)
            # /home/noam
            # Acdbhd1348
            client_dir = get_client_id_folder(client_id)
            old_file_path = os.path.join(get_client_id_folder(client_id),
                                         convert_path(request_parts[1], separator))
            # Acdbhd1348/home/noam
            new_file_path = os.path.join(get_client_id_folder(client_id),
                                         convert_path(request_parts[2], separator))
            # Acdbhd1348/home/example
            try:
                os.rename(os.path.abspath(old_file_path), os.path.abspath(new_file_path))
            except Exception as e:
                print(e)
            # connection.close()
        # if the client tells the server about deleting a folder
        # it will keep it, and will update other clients with the same id.
        # in the meantime, the server deletes the folder in its side.
        elif command == ALERT_DELETED_FILE:
            separator = request_parts[4]
            computer_id = request_parts[3]
            computer_to_os[computer_id] = separator
            client_id = request_parts[2]
            # /home/noam
            # /home/noam/example
            path_to_delete = os.path.join(get_client_id_folder(client_id),
                convert_path(request_parts[1], separator))
            # Acdbhd1348
            client_dir = get_client_id_folder(client_id)
            # Acdbhd1348/home/noam
            # the server delete the folder in its side.
            try:
                os.remove(os.path.abspath(path_to_delete))
            except:
                try:
                    for root, folders, files in os.walk(path_to_delete, topdown=False):
                        for name_of_file in files:
                            os.remove(os.path.join(root, name_of_file))
                        for name_of_file in folders:
                            os.rmdir(os.path.join(root, name_of_file))
                    os.rmdir(path_to_delete)
                except Exception as e:
                    print(e)
            add_changes(changes, client_id, computer_id, request, dictionary)
            # connection.close()
            # connection.close()
        elif command == ALERT_DELETED_FOLDER:
            separator = request_parts[4]
            computer_id = request_parts[3]
            computer_to_os[computer_id] = separator
            client_id = request_parts[2]
            # /home/noam
            # /home/noam/example
            path_in_client = os.path.join(get_client_id_folder(client_id),
                                          convert_path(request_parts[1], separator))
            # Acdbhd1348
            client_dir = get_client_id_folder(client_id)
            # Acdbhd1348/home/noam
            should_do_for_recursive = True
            if (os.path.isfile(path_to_delete)):
                os.remove(os.path.abspath(path_to_delete))
                request.replace("folder", "file")
                add_changes(changes, client_id, client_id, request, dictionary)
                should_do_for_recursive = False
            if should_do_for_recursive:
                # the server delete the folder in its side.
                for root, folders, files in os.walk(path_to_delete, topdown=False):
                    for name_of_file in files:
                        os.remove(os.path.join(root, name_of_file))
                    for name_of_file in folders:
                        os.rmdir(os.path.join(root, name_of_file))
            try:
                os.rmdir(os.path.abspath(path_to_delete))
            except Exception as e:
                print(e)
            add_changes(changes, client_id, computer_id, request, dictionary)
            # connection.close()
        # hello is send every time the client starts connection with the server.
        # in this way the server knows the client id, and client does not have to
        # send it in every request as parameter.
        elif command == HELLO:
            client_id = request_parts[1]
            separator = request_parts[5]
            client_id_folder = client_id[:CLIENT_SHORT_ID_LENGTH]
            client_folder = convert_path(request_parts[2], separator)
            is_first_hello = request_parts[3]
            computer_id = request_parts[4]
            computer_to_os[computer_id] = separator
            add_client_to_dictionary(dictionary, client_id, computer_id, client_folder)
            create_folder(client_id_folder)
            # if it's the first hello, then clone
            # give the client all the changes it needs.
            if is_first_hello.upper() == TRUE:
                create_folder(client_id_folder)
                send_all_folder(client_id_folder, connection, computer_id, client_id)
                msg = FINISH.encode(UTF)
                sum = get_size(msg)
                connection.send(sum)
                connection.send(msg)
                break
            client_that_said_hello.append(computer_id)
            # connection.close()
        # the client asks the server if there was a change.
        elif command == ASK_CHANGED:
            separator = request_parts[4]
            computer_id = request_parts[3]
            computer_to_os[computer_id] = separator
            client_id = request_parts[2]
            my_last_update_time = float(request_parts[1])
            # the server tell the client about moving folders.
            send_important_changes(dictionary, client_id, changes, my_last_update_time, connection, computer_id)
            # the server sends the file to the client.
            client_id_folder = client_id[:CLIENT_SHORT_ID_LENGTH]
            # connection.close()
            msg = FINISH.encode(UTF)
            sum = get_size(msg)
            connection.send(sum)
            connection.send(msg)
            connection.close()
            break
        elif command == SEND_DIR or command == CREATE_DIR:
            separator = request_parts[4]
            computer_id = request_parts[3]
            computer_to_os[computer_id] = separator
            folder_path = convert_path(request_parts[1], separator)
            client_id = request_parts[2]
            # the server creates directory as the client told him.
            folder_path = os.path.abspath(os.path.join(get_client_id_folder(client_id), folder_path))
            create_folder(folder_path)
            if command == CREATE_DIR:
                add_changes(changes, client_id, computer_id, request, dictionary)
            # connection.close()
        elif command == SEND_FILE:
            # the server receives a file from the client.
            file_name = request_parts[1]
            file_size = int(request_parts[2])
            separator = request_parts[7]
            client_id = request_parts[4]
            file_path = os.path.abs(os.path.join(get_client_id_folder(client_id),
                                     convert_path(request_parts[3], separator)))
            is_first_hello = "FALSE"
            try:
                computer_id = request_parts[5]
                computer_to_os[computer_id] = separator
                is_first_hello = request_parts[6]
            except Exception as e:
                computer_id = client_id
                print(e)
            folder = file_path.replace(file_name, EMPTY_STRING)
            create_folder(folder)
            f = open(file_path, WRITE_BYTES)
            data_left_to_read = file_size
            read_from_file = 0
            while data_left_to_read > 0:
                if data_left_to_read < BIGGEST_SIZE_SOCKET:
                    time.sleep(0.5)
                    data = connection.recv(data_left_to_read)
                    read_from_file += len(data)
                    if not data:
                        break
                    print("Writing to file...")
                    f.write(data)
                    f.close()
                    data_left_to_read -= len(data)
                    break
                else:
                    time.sleep(0.5)
                    data = connection.recv(BIGGEST_SIZE_SOCKET)
                    data_left_to_read -= len(data)
                    read_from_file += len(data)
                    if not data:
                        break
                    print("Writing...")
                    f.write(data)
                print("read: ", read_from_file, " left: ", data_left_to_read)
                print(read_from_file / file_size)
                print("Finished writing to file...")
            print("Finished writing to file...")
            if is_first_hello == "FALSE":
                add_changes(changes, client_id, computer_id, request, dictionary)
            # connection.close()
        elif command == FINISH:
            connection.close()
            print("Finished and went to wait to other clients.")
            break
        time.sleep(SLEEP_INTERVAL)