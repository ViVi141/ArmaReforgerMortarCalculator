import os
import traceback
from datetime import datetime
from utils import resource_path

class DevLog:
    def __init__(self):
        self.log_dir = resource_path("Mortar Calculator Logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def write_log(self, error):
        """Writes the full traceback of an error to a timestamped log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_path = os.path.join(self.log_dir, f"error_log_{timestamp}.txt")
        
        with open(log_file_path, "w") as f:
            f.write(f"--- Error Log: {timestamp} ---\n\n")
            traceback.print_exc(file=f)