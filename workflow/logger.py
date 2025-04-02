from datetime import datetime
import os

class Logger:
    def __init__(self, log_dir='automation_logs'):
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        self.log_dir = log_dir
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"automation_log_{timestamp}.log")
        
        # Initialize log file with header
        with open(self.log_file, 'w') as f:
            f.write(f"=== Automation Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        
        # Also print to console
        print(log_entry.strip())
    
    def info(self, message):
        """Log an info message"""
        self.log(message, "INFO")
    
    def warning(self, message):
        """Log a warning message"""
        self.log(message, "WARNING")
    
    def error(self, message):
        """Log an error message"""
        self.log(message, "ERROR")
    
    def success(self, message):
        """Log a success message"""
        self.log(message, "SUCCESS")
