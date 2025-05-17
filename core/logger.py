import os
import logging

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'wispy.log')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

def log_action(action: str):
    """
    Log a high-level action performed by the user or system.
    """
    logging.info(f"ACTION: {action}")

def log_output_summary(output: str):
    """
    Log a summary of console output (first 300 chars, single line).
    """
    summary = output.strip().replace('\n', ' ')[:300]
    logging.info(f"OUTPUT: {summary}")

def log_error(error: str):
    """
    Log an error message.
    """
    logging.error(f"ERROR: {error}")

def log_warning(warning: str):
    """
    Log a warning message.
    """
    logging.warning(f"WARNING: {warning}")