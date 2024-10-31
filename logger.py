import logging
import os, sys
from datetime import datetime
class StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance, while also printing to console.
    """
    def __init__(self, logger, log_level=logging.INFO, stream=None):
        self.logger = logger
        self.log_level = log_level
        self.stream = stream  # Original stream (stdout or stderr)

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            # More accurate checking for JSON-like structures
            if line.strip().startswith('[{"') and line.strip().endswith('}]'):
                continue  # Skip logging this line if it matches the pattern
            self.logger.log(self.log_level, line.rstrip())
            if self.stream:
                self.stream.write(line + '\n')  # Append newline for console output
                self.stream.flush()

    def flush(self):
        pass

def setup_logging():
    os.makedirs('./logs', exist_ok=True)
    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        filename=f'./logs/job_{current_time}.log',
        filemode='a'
    )
    # Capture original stdout and stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    # Redirect stdout and stderr to logging and also print to original streams
    sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO, original_stdout)
    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR, original_stderr)

if __name__ == "__main__":
    setup_logging()
    print("This message will be logged and also displayed on the console.")
    print('[{"name": "Example", "type": "test"}]')
    try:
        raise ValueError("This error will be logged and displayed.")
    except Exception as e:
        print(e)
