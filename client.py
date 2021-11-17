import socket, sys, os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

INVALID = -1
IP_INDEX = 1
PORT_INDEX = 2
PATH_INDEX = 3
TIME_INTERVAL_INDEX = 4
ID_INDEX = 5


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
        print(f'Error: path: {sys.argv[PATH_INDEX]} ,does not exists')
        return INVALID
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

class FileChangedHandler(FileSystemEventHandler):
    def alert_file_modified(self, e):
        print(f'{e.event_type}, {e.src_path}')

flag = arguments_check()
if flag == INVALID:
    exit(INVALID)
ip = sys.argv[IP_INDEX]
port = int(sys.argv[PORT_INDEX])
dir_path = sys.argv[PATH_INDEX]
time_interval = sys.argv[TIME_INTERVAL_INDEX]
client_id = ""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect((ip, port))

# if len(sys.argv) == 6:
#     client_id = sys.argv[5]
# else:
#     s.send("REGS")
#     data = s.recv(132)
#     print("Server sent: ", data)
#     client_id = data[4:]

# saving the files
all_files = os.listdir(dir_path)
# saving the files path
files_path = [os.path.abspath(x) for x in os.listdir(dir_path)]
print(files_path)
#
entries = os.listdir(dir_path)
print(entries)

s.connect((ip, port))

if len(sys.argv) == 6:
    client_id = sys.argv[5]
else:
    s.send("REGS")
    data = s.recv(132)
    print("Server sent: ", data)
    client_id = data[4:]

BUFFER_SIZE = 1024

for (root, dirs, files) in os.walk(dir_path, topdown=True):
    for name in files:
        print(os.path.join(root, name))
        fileloc = os.path.join(root, name)
        with open(fileloc, "rb") as f:
            while True:
                # read the bytes from the file
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    # file transmitting is done
                    break
                # we use sendall to assure transimission in
                # busy networks
                s.sendall(bytes_read)


# handler = FileChangedHandler()
# observer = Observer()
# observer.schedule(handler, path=dir_path, recursive = True)
#
# try:
#     while True:
#         time.sleep(2)
# except:
#     observer.stop()
#
# observer.join()
s.close()
