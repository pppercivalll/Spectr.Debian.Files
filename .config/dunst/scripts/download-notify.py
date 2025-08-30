#!/usr/bin/env python3
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Temporary extensions (download in progress)
TEMP_EXTS = {".part", ".crdownload", ".tmp", ".aria2", ".part~", ".partial"}

# Folders to monitor
WATCH_DIRS = [
    Path.home() / "Downloads",
    Path.home() / "Music",
    Path.home() / "Documents",
    Path.home() / "Pictures",
    Path.home() / "Videos",
]

def is_temp(path: Path) -> bool:
    return path.suffix.lower() in TEMP_EXTS

def human(nbytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(nbytes)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.1f} {u}"
        size /= 1024

def notify(path: Path):
    size = path.stat().st_size if path.exists() else 0
    body = f"{path.name}\n{human(size)}"
    cmd = [
        "dunstify",
        "-a", "download",
        "-u", "normal",
        "-i", "folder-download",
        "-r", "4242",
        "📁 Download complete", body
    ]
    subprocess.run(cmd, check=False)

class Handler(FileSystemEventHandler):
    def on_moved(self, event):
        if event.is_directory:
            return
        src, dst = Path(event.src_path), Path(event.dest_path)
        if is_temp(src) and not is_temp(dst):
            notify(dst)

def main():
    observer = Observer()
    for d in WATCH_DIRS:
        if d.exists():
            observer.schedule(Handler(), str(d), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
