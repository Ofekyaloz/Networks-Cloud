import socket, sys, os, time
import string
import random

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileSystemEventHandler

INVALID = -1
IP_INDEX = 1
PORT_INDEX = 2
PATH_INDEX = 3
TIME_INTERVAL_INDEX = 4
ID_INDEX = 5
CLIENT_SHORT_ID_LENGTH = 15
MINIMUM_ARGS_LENGTH = 5
MAXIMUM_ARGS_LENGTH = 6
IP_PARTS_AMOUNT = 4
MAX_INT_IP = 255
MESSAGE_SIZE_HEADER_LENGTH = 12
UTF = 'utf-8'
IGNORE = "ignore"
DELIMITER = "@@@"
BUFFER_SIZE = 1024
READ_BYTES = "rb"
REGISTER = "register"
HELLO = "hello"
SEND_DIR = "send-dir"
FINISH = "finish"
ALERT_DELETED_FOLDER = "alert-deleted-folder"
ALERT_MOVED_FOLDER = "alert-moved-folder"
ALERT_DELETED_FILE = "alert-deleted-file"
ALERT_MOVED_FILE = "alert-moved-file"
SEND_DIR = "send-dir"
SEND_FILE = "send-file"
ASK_CHANGED = "ask-changed"
WRITE_BYTES = "wb+"
SLEEP_INTERVAL = 2
ID_LENGTH = 12
EMPTY_STRING = ""
global updates_set
updates_set = set()


def create_folder(folder_path):
    try:
        os.makedirs(folder_path)
        print("created folder " + folder_path)
    except Exception as e:
        print("folder " + folder_path + " already exists.")

def get_client_id_folder(client_id):
    return client_id[:CLIENT_SHORT_ID_LENGTH]

# function that checks validity of the parameters.
def arguments_check():
    if len(sys.argv) < MINIMUM_ARGS_LENGTH or len(sys.argv) > MAXIMUM_ARGS_LENGTH:
        print("Error: invalid number of arguments")
        return INVALID
    ip = sys.argv[IP_INDEX]
    port = sys.argv[PORT_INDEX]
    if not port.isdigit():
        print(f'Error: invalid port: {port}')
        return INVALID

    time_interval = sys.argv[TIME_INTERVAL_INDEX]
    if not time_interval.isdigit():
        print(f'Error: time interval: {sys.argv[TIME_INTERVAL_INDEX]} ,is not a number')
        return INVALID
    else:
        time_interval = int(time_interval)
        if time_interval <= 0:
            print(f'time interval {time_interval} is not valid')
            return INVALID
    if not os.path.isdir(sys.argv[PATH_INDEX]):
        create_folder(sys.argv[PATH_INDEX])
    else:
        pass
    parts = ip.split('.')
    if len(parts) != IP_PARTS_AMOUNT:
        print(f'IP: {ip} is not valid')
        return INVALID
    i = 0
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= MAX_INT_IP or (i == 0 and int(part) == 0):
            print(f'IP: {ip} is not valid')
            return INVALID
        i += 1

# return the size of a message, 12 chars
def get_size(msg):
    sum = 0
    for i in msg:
        sum += 1
    return str(sum).zfill(MESSAGE_SIZE_HEADER_LENGTH).encode(UTF)


flag = arguments_check()
if flag == INVALID:
    exit(INVALID)
ip = sys.argv[IP_INDEX]
port = int(sys.argv[PORT_INDEX])
dir_path = sys.argv[PATH_INDEX]
time_interval = int(sys.argv[TIME_INTERVAL_INDEX])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
new_client = False

# if the client has id save it, else ask new id from the server
if len(sys.argv) == MAXIMUM_ARGS_LENGTH:
    client_id = sys.argv[5]
else:
    new_client = True
    s.send(('8'.zfill(12)).encode(UTF))
    s.send(REGISTER.encode(UTF))
    data = s.recv(132)
    print("Server sent: ", data)
    client_id = data.decode(UTF)


# send all the files from a specific path
def send_all_files(path, computer_id, s):
    # root = paths, dirs = folders, files
    for (root, dirs, files) in os.walk(path, topdown=True):
        for folder in dirs:
            folder_loc = os.path.join(root, folder)
            msg = (DELIMITER.join([SEND_DIR, str(folder_loc), str(client_id), computer_id])).encode(UTF)
            msg_len = get_size(msg)
            s.send(msg_len)
            s.send(msg)

        for file in files:
            fileloc = os.path.join(root, file)
            with open(fileloc, READ_BYTES) as f:
                size = os.path.getsize(fileloc)
                msg = (DELIMITER.join([SEND_FILE, str(file), str(size), str(fileloc), str(client_id), computer_id])).encode(UTF)
                msg_len = get_size(msg)
                s.send(msg_len)
                s.send(msg)
                while True:
                    # read the bytes from the file
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        # file transmitting is done
                        break
                    s.sendall(bytes_read)
    msg = FINISH.encode(UTF)
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)
    s.close()


# receive changes from the server
def get_changes_from_server(path):
    while True:
        request = s.recv(MESSAGE_SIZE_HEADER_LENGTH)
        request = request.decode(UTF, IGNORE)
        try:
            length_of_packet = int(request)
        except:
            length_of_packet = BUFFER_SIZE
        request = s.recv(length_of_packet).decode(UTF, IGNORE)

        request_parts = request.split(DELIMITER)
        command = request_parts[0]
        print(command)
        # the server says that a folder was moved.
        if command == ALERT_MOVED_FOLDER:
            # cdshdbcsjjcbhdsbhjcsbhjcdsbjhcbhjsdbhjhbds\ofek\do
            # mycomputer\ofek\do
            client_dir = get_client_id_folder(client_id)
            old_folder_path = request_parts[1]
            old_folder_path = old_folder_path.replace(client_dir, dir_path)
            new_folder_path = request_parts[2]
            new_folder_path = new_folder_path.replace(client_dir, dir_path)
            os.rename(old_folder_path, new_folder_path)

        elif command == ALERT_DELETED_FILE:
            client_dir = get_client_id_folder(client_id)
            # /home/noam/example
            path_in_file = request_parts[1]
            # Acdbhd1348/home/noam
            path_to_delete = path_in_file.replace(client_dir, dir_path)
            try:
            # the server delete the folder in its side.
                os.remove(path_to_delete)
            except Exception as e:
                print(e)

        elif command == ALERT_MOVED_FILE:
            client_dir = get_client_id_folder(client_id)
            # /home/noam
            old_file_path = request_parts[1]
            # Acdbhd1348/home/noam
            old_file_path = old_file_path.replace(client_dir, dir_path)
            new_file_path = request_parts[2]
            # Acdbhd1348/home/example
            new_file_path = new_file_path.replace(client_dir, dir_path)
            try:
                os.rename(os.path.abspath(old_file_path), os.path.abspath(new_file_path))
            except:
                pass
        elif command == ALERT_DELETED_FOLDER:
            path_in_client = request_parts[1]
            client_dir = get_client_id_folder(client_id)
            path_to_delete = path_in_client.replace(client_dir, dir_path)
            # the client delete the folder in its side.
            for root, folders, files in os.walk(path_to_delete, topdown=False):
                for name_of_file in files:
                    os.remove(os.path.join(root, name_of_file))
                for name_of_file in folders:
                    os.rmdir(os.path.join(root, name_of_file))
            os.rmdir(os.path.abspath(path_to_delete))
        if command == SEND_DIR:
            folder_path = request_parts[1]
            folder_path = folder_path.replace(client_id[0:MESSAGE_SIZE_HEADER_LENGTH], path)
            create_folder(folder_path)

        elif command == SEND_FILE:
            file_name = request_parts[1]
            file_size = int(request_parts[2])
            file_path = request_parts[3]
            file_path = file_path.replace(client_id[0:15], path)
            folder = file_path.replace(file_name, "")
            create_folder(folder)
            f = open(file_path, WRITE_BYTES)
            data = s.recv(file_size)
            print("Writing to file...")
            f.write(data)
            f.close()

        elif command == FINISH:
            print("Finished")
            msg = FINISH.encode(UTF)
            msg_len = get_size(msg)
            s.send(msg_len)
            s.send(msg)
            s.close()
            break
        time.sleep(SLEEP_INTERVAL)

computer_id = EMPTY_STRING.join(
                random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for i in range(ID_LENGTH))
print("computer id: ", computer_id)
last_visit = time.time()
if new_client:
    msg = (DELIMITER.join([HELLO, str(client_id), dir_path, "False", computer_id])).encode(UTF)
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)
    send_all_files(dir_path, computer_id, s)
else:
    msg = (DELIMITER.join([HELLO, str(client_id), dir_path, "True", computer_id])).encode(UTF)
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)
    get_changes_from_server(dir_path)

# ask changes from the server
def ask_change(last_visit):
    print("ask change")
    msg = (DELIMITER.join([ASK_CHANGED, str(last_visit), str(client_id), computer_id])).encode(UTF)
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)
    get_changes_from_server(dir_path)


class FileChangedHandler(FileSystemEventHandler):
    def alert_file_modified(self, e):
        print(f'{e.event_type}, {e.src_path}')

# send file
def send_file(s , msg):
    fileloc = msg.decode(UTF).split("@@@")[3]
    with open(fileloc, READ_BYTES) as f:
        #msg = (DELIMITER.join([SEND_FILE, str(file), str(size), str(fileloc), str(client_id), computer_id])).encode(UTF)
        while True:
            # read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                # file transmitting is done
                break
            s.sendall(bytes_read)

def on_created(event):
    print(f"created {event.src_path}")
    if os.path.isfile(event.src_path):
        file = os.path.basename(event.src_path)
        #send_file(s, event.src_path, file, client_id)
        size = os.path.getsize(event.src_path)
        msg = (DELIMITER.join([SEND_FILE, str(file), str(size), str(event.src_path), str(client_id), computer_id])).encode(UTF)
    elif os.path.isdir(event.src_path):
        msg = (DELIMITER.join([SEND_DIR, str(event.src_path), str(client_id), computer_id])).encode(UTF)
    else:
        return
    print(msg[:30])
    updates_set.add(msg)


def on_deleted(event):
    print(f"deleted {event.src_path}")
    if event.is_directory:
        msg = (DELIMITER.join([ALERT_DELETED_FOLDER, str(event.src_path), str(client_id), computer_id])).encode(UTF)
    else:
        msg = (DELIMITER.join([ALERT_DELETED_FILE, str(event.src_path), str(client_id), computer_id])).encode(UTF)
    print(msg[:30])
    updates_set.add(msg)


# def on_modified(event):
#     print(f"modified {event.src_path} ")
#     file = os.path.basename(event.src_path)
#     if file.startswith("."):
#         return
#     size = os.path.getsize(event.src_path)
#     msg = (DELIMITER.join([SEND_FILE, str(file), str(size), str(event.src_path), str(client_id)])).encode(UTF)
#     send_watch(s,msg)

# add move alert-moved-folder
def on_moved(event):
    print(f"moved {event.src_path} to {event.dest_path}")
    if event.is_directory:
        msg = (DELIMITER.join([ALERT_MOVED_FOLDER, str(event.src_path), str(event.dest_path), str(client_id), computer_id])).encode(UTF)
    elif (".goutputstream") in str(event.src_path):
        size = os.path.getsize(event.dest_path)
        file = os.path.basename(event.dest_path)
        #send_file(s, event.dest_path, file, client_id)
        msg = (DELIMITER.join([SEND_FILE, str(file), str(size), str(event.src_path), str(client_id), computer_id])).encode(UTF)
    elif os.path.isfile(event.dest_path):
        msg = (DELIMITER.join([ALERT_MOVED_FILE, str(event.src_path), str(event.dest_path), str(client_id), computer_id])).encode(UTF)
    else:
        return
    print(msg[:30])
    updates_set.add(msg)


handler = PatternMatchingEventHandler("*", None, False, True)
handler.on_created = on_created
handler.on_deleted = on_deleted
# handler.on_modified = on_modified
handler.on_moved = on_moved
observer = Observer()
observer.schedule(handler, path=dir_path, recursive=True)

observer.start()
print("sleep")
time.sleep(time_interval)


def send_watch(s, updates_set):
    print("send_watch")
    for msg in updates_set:
        msg_len = get_size(msg)
        s.send(msg_len)
        s.send(msg)
        if (msg.decode(UTF)).startswith("send-file"):
            send_file(s, msg)
        print("watch send: ", msg[:30])
    updates_set = set()
    return updates_set

try:
    while True:
        print("awake")
        #observer.stop()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        ask_change(last_visit)
        last_visit = time.time()
        # observer = Observer()
        # observer.schedule(handler, path=dir_path, recursive=True)
        # observer.start()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        print(updates_set)
        updates_set = send_watch(s, updates_set)
        print("sleep")
        msg = FINISH.encode(UTF)
        msg_len = get_size(msg)
        s.send(msg_len)
        s.send(msg)
        s.close()
        time.sleep(time_interval)


except KeyboardInterrupt:
    observer.stop()
    observer.join()