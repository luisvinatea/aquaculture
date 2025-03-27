import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scripts.data_handling.update_aerator_specs import push

class CSVWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith("Pesos_WangFa_Beraqua_3HP_2025-03-22.csv"):
            print(f"Detected change in {event.src_path}. Pushing to Google Sheet...")
            push()

def watch_csv():
    path = "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/csv"
    event_handler = CSVWatcher()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print(f"Watching for changes in {path}...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    watch_csv()