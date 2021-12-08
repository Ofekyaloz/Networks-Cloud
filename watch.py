import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileSystemEventHandler


class FileChangedHandler(FileSystemEventHandler):
    def alert_file_modified(self, e):
        print(f'{e.event_type}, {e.src_path}')


def on_created(event):
    print(f"created {event.src_path}")


def on_deleted(event):
    print(f"deleted {event.src_path}")


def on_modified(event):
    print(f"modified {event.src_path} ")


def on_moved(event):
   print(f"moved {event.src_path} to {event.dest_path}")


handler = PatternMatchingEventHandler("*", None, False, True)
handler.on_created = on_created
handler.on_deleted = on_deleted
handler.on_modified = on_modified
handler.on_moved = on_moved

observer = Observer()
observer.schedule(handler, path="/home/ofek/Desktop/temp", recursive=True)

observer.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    observer.join()
