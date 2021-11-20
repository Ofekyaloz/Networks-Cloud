import socket, sys, os, time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileSystemEventHandler

INVALID = -1
IP_INDEX = 1
PORT_INDEX = 2
PATH_INDEX = 3
TIME_INTERVAL_INDEX = 4
ID_INDEX = 5
BUFFER_SIZE = 1024


# function that checks validity of the parameters.
def arguments_check():
    if len(sys.argv) < 5 or len(sys.argv) > 6:
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
    if len(parts) != 4:
        print(f'IP: {ip} is not valid')
        return INVALID
    i = 0
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255 or (i == 0 and int(part) == 0):
            print(f'IP: {ip} is not valid')
            return INVALID
        i += 1


def get_size(msg):
    sum = 0
    for i in msg:
        sum += 1
    return str(sum).zfill(12).encode('utf-8')


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

if len(sys.argv) == 6:
    client_id = sys.argv[5]
else:
    new_client = True
    s.send(('8'.zfill(12)).encode('utf-8'))
    s.send("register".encode('utf-8'))
    data = s.recv(132)
    print("Server sent: ", data)
    client_id = data.decode('utf-8')


def send_all_files(path):
    # root = paths, dirs = folders, files
    for (root, folders, files) in os.walk(path, topdown=True):
        for folder in folders:
            folder_loc = os.path.join(root, folder)
            if not (os.listdir(folder_loc)):
                msg = ("send-dir" + "@@@" + str(folder_loc)).encode('utf-8')
                msg_len = get_size(msg)
                s.send(msg_len)
                s.send(msg)

        for file in files:
            fileloc = os.path.join(root, file)
            with open(fileloc, "rb") as f:
                size = os.path.getsize(fileloc)
                msg = ("send-file@@@" + str(file) + "@@@" + str(size) + "@@@" + str(fileloc)).encode('utf-8')
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
    msg = "finish".encode('utf-8')
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)


def create_folder(folder_path):
    try:
        os.makedirs(folder_path)
        print("created folder " + folder_path)
    except Exception as e:
        print("folder " + folder_path + " already exists.")


def get_all_files(path):
    while True:
        request = s.recv(12)
        request = request.decode('utf-8', 'ignore')
        try:
            length_of_packet = int(request)
        except:
            length_of_packet = 1024
        request = s.recv(length_of_packet).decode('utf-8', 'ignore')

        request_parts = request.split("@@@")
        command = request_parts[0]
        if command == "send-dir":
            folder_path = request_parts[1]
            folder_path = folder_path.replace(client_id[0:15], path)
            create_folder(folder_path)

        elif command == "send-file":
            file_name = request_parts[1]
            file_size = int(request_parts[2])
            file_path = request_parts[3]
            file_path = file_path.replace(client_id[0:15], path)
            folder = file_path.replace(file_name, "")
            create_folder(folder)
            f = open(file_path, 'wb+')
            data = s.recv(file_size)
            print("Writing to file...")
            f.write(data)
            f.close()

        elif command == "alert-delete-folder":
            delete_path = request[1]
            delete_path = delete_path.replace(client_id[0:15], path)
            for root, folders, files in os.walk(delete_path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for folder in folders:
                    os.rmdir(os.path.join(root, folder))

        elif command == "alert-moved-folder":
            src_path = request[1]
            dest_path = request[2]



        elif command == "finish":
            print("Finished")
            break
        time.sleep(2)


msg = ("hello@@@" + str(client_id) + "@@@" + dir_path + "@@@True").encode('utf-8')
msg_len = get_size(msg)
s.send(msg_len)
s.send(msg)
last_viist = time.time()
if (new_client):
    send_all_files(dir_path)
else:
    get_all_files(dir_path)


def ask_change(last_visit):
    msg = ("ask-changed@@@" + str(last_visit)).encode('utf-8')
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)
    print("ask-change")
    get_all_files(dir_path)
    print("received changes")
    time.sleep(2)

class FileChangedHandler(FileSystemEventHandler):
    def alert_file_modified(self, e):
        print(f'{e.event_type}, {e.src_path}')



def on_created(event):
    print(f"created {event.src_path}")
    msg = ("send-dir" + "@@@" + str(event.src_path)).encode('utf-8')
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)


def on_deleted(event):
    print(f"deleted {event.src_path}")
    msg = ("alert-deleted-folder" + "@@@" + str(event.src_path)).encode('utf-8')
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)


def on_modified(event):
    print(f"modified {event.src_path} ")
    file = os.listdir(event.src_path)[0]
    size = os.path.getsize(event.src_path)
    msg = ("send-file@@@" + str(file) + "@@@" + str(size) + "@@@" + str(event.src_path)).encode('utf-8')
    msg_len = get_size(msg)
    s.send(msg_len)
    s.send(msg)


def on_moved(event):
   print(f"moved {event.src_path} to {event.dest_path}")
   msg = ("alert-moved-folder" + "@@@" + str(event.src_path) + "@@@" + str(event.dest_path)).encode('utf-8')
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
        print("awake")
        msg = ("hello@@@" + str(client_id) + "@@@" + dir_path + "@@@False").encode('utf-8')
        msg_len = get_size(msg)
        s.send(msg_len)
        s.send(msg)
        ask_change(last_viist)
        last_viist = time.time()
        msg = "finish".encode('utf-8')
        msg_len = get_size(msg)
        s.send(msg_len)
        s.send(msg)
        print("send finish")
        print("sleep")
        time.sleep(time_interval)

except KeyboardInterrupt:
    observer.stop()
    observer.join()

s.close()
