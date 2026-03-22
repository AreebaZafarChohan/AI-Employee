import os
import time
import subprocess
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
WATCH_DIR = "./AI-Employee-Vault"
SYNC_SCRIPT = "./sync_push.sh"
DEBOUNCE_SECONDS = 10 # Wait before triggering sync to batch changes

class SyncHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_sync_time = 0
        self.pending_changes = False

    def on_modified(self, event):
        if event.is_directory:
            return
        if ".git" in event.src_path:
            return
        
        logger.debug(f"Change detected: {event.src_path}")
        self.pending_changes = True

    def on_created(self, event):
        self.on_modified(event)

    def on_deleted(self, event):
        self.on_modified(event)

    def trigger_sync(self):
        if self.pending_changes:
            current_time = time.time()
            if current_time - self.last_sync_time > DEBOUNCE_SECONDS:
                logger.info("[Vault Monitor] Triggering sync push...")
                try:
                    # Determine which script to run based on OS
                    if os.name == 'nt': # Windows
                        subprocess.run(["powershell.exe", "-File", "sync_push.ps1"], check=True)
                    else: # Linux / Mac
                        subprocess.run(["bash", SYNC_SCRIPT], check=True)
                    
                    self.last_sync_time = current_time
                    self.pending_changes = False
                    logger.info("[Vault Monitor] Sync push completed.")
                except subprocess.CalledProcessError as e:
                    logger.error(f"[Vault Monitor] Sync failed: {e}")
                except Exception as e:
                    logger.error(f"[Vault Monitor] Error: {e}")

if __name__ == "__main__":
    handler = SyncHandler()
    observer = Observer()
    observer.schedule(handler, WATCH_DIR, recursive=True)
    observer.start()
    
    logger.info(f"Starting Vault Sync Monitor on {WATCH_DIR}...")
    try:
        while True:
            handler.trigger_sync()
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
