import socket, sys, os, time
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
SEND_DIR = "send-dir"
SEND_FILE = "send-file"
ASK_CHANGED = "ask-changed"
WRITE_BYTES = "wb+"
SLEEP_INTERVAL = 2


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

if len(sys.argv) == MAXIMUM_ARGS_LENGTH:
    client_id = sys.argv[5]
else:
    new_client = True
    s.send(('8'.zfill(12)).encode(UTF))
    s.send(REGISTER.encode(UTF))
    data = s.recv(132)
    print("Server sent: ", data)
    client_id = data.decode(UTF)


def send_all_files(path, first_time, last_visit):
    # root = paths, dirs = folders, files
    for (root, dirs, files) in os.walk(path, topdown=True):
        for folder in dirs:
            folder_loc = os.path.join(root, folder)
            now = os.path.getmtime(folder_loc)
            if not (os.listdir(folder_loc)):
                msg = (DELIMITER.join([SEND_DIR, str(folder_loc)])).encode(UTF)
                msg_len = get_size(msg)
                if first_time or (last_visit - now <= 0):
                    s.send(msg_len)
                    s.send(msg)

        for file in files:
            fileloc = os.path.join(root, file)
            with open(fileloc, READ_BYTES) as f:
                size = os.path.getsize(fileloc)
                msg = (DELIMITER.join([SEND_FILE, str(file), str(size), str(fileloc)])).encode(UTF)
                msg_len = get_size(msg)
                now = os.path.getmtime(folder_loc)
                if first_time or (last_visit - now <= 0):
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


def create_folder(folder_path):
    try:
        os.makedirs(folder_path)
        print("created folder " + folder_path)
    except Exception as e:
        print("folder " + folder_path + " already exists.")


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
        # the server says that a folder was moved.
        if command == "alert-moved-folder":
            # /home/noam
            client_folder = dir_path
            # Acdbhd1348
            client_dir = get_client_id_folder(client_id)
            # Acdbhd1348/temp/home/noam
            old_folder_path = request_parts[1]
            # /ofek/temp/home/noam
            old_folder_path = old_folder_path.replace(client_dir, dir_path)
            # Acdbhd1348/temp/home/example
            new_folder_path = request_parts[2]
            # /ofek/temp/home/example
            old_folder_path = old_folder_path.replace(client_dir, dir_path)
            os.rename(old_folder_path, new_folder_path)
        elif command == ALERT_DELETED_FOLDER:
            # /home/noam
            client_folder = dir_path
            # Abcdd237842/example
            path_in_client = request_parts[1]
            # Abcdd237842
            client_dir = get_client_id_folder(client_id)
            # /ofek/main/home/noam
            path_to_delete = path_in_client.replace(client_dir, dir_path)
            # the server delete the folder in its side.
            for root, folders, files in os.walk(path_to_delete, topdown=False):
                for name_of_file in files:
                    os.remove(os.path.join(root, name_of_file))
                for name_of_file in folders:
                    os.rmdir(os.path.join(root, name_of_file))
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
            break
        time.sleep(SLEEP_INTERVAL)


msg = (DELIMITER.join([HELLO, str(client_id), dir_path, "True"])).encode(UTF)
msg_len = get_size(msg)
s.send(msg_len)
s.send(msg)
last_visit = time.time()
if new_client:
    send_all_files(dir_path, True, last_visit)
else:
    get_changes_from_server(dir_path)


def ask_change(last_visit):
    msg = (DELIMITER.join([ASK_CHANGED, str(last_visit)])).encode(UTF)
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)
    get_changes_from_server(dir_path)


class FileChangedHandler(FileSystemEventHandler):
    def alert_file_modified(self, e):
        print(f'{e.event_type}, {e.src_path}')


def on_created(event):
    print(f"created {event.src_path}")
    msg = (DELIMITER.join([SEND_DIR, str(event.src_path)])).encode(UTF)
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)


def on_deleted(event):
    print(f"deleted {event.src_path}")
    msg = (DELIMITER.join([ALERT_DELETED_FOLDER, str(event.src_path)])).encode(UTF)
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)


def on_modified(event):
    print(f"modified {event.src_path} ")
    file = os.listdir(event.src_path)[0]
    size = os.path.getsize(event.src_path)
    msg = (DELIMITER.join([SEND_FILE, str(file), str(size), + str(event.src_path)])).encode(UTF)
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)


def on_moved(event):
    print(f"moved {event.src_path} to {event.dest_path}")
    msg = (DELIMITER.join([ALERT_MOVED_FOLDER, str(event.src_path), str(event.dest_path)])).encode(UTF)
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)


handler = PatternMatchingEventHandler("*", None, False, True)
handler.on_created = on_created
handler.on_deleted = on_deleted
handler.on_modified = on_modified
handler.on_moved = on_moved
observer = Observer()
observer.schedule(handler, path=dir_path, recursive=True)

observer.start()
try:
    while True:
        ask_change(last_visit)
        last_visit = time.time()
        print("sleep")
        time.sleep(time_interval)
        msg = "finish".encode('utf-8')
        msg_len = get_size(msg)
        s.send(msg_len)
        s.send(msg)
        print("send finish")
except KeyboardInterrupt:
    observer.stop()
    observer.join()

s.close()