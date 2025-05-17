import os
import subprocess
from .logger import log_action, log_output_summary, log_error, log_warning

# Color codes for text
class TextColor:
    RED = "\033[1;31m"
    GREEN = "\033[1;32m"
    BLUE = "\033[1;34m"
    CYAN = "\033[1;36m"
    YELLOW = "\033[1;33m"
    RESET = "\033[0m"
    PURPLE = "\033[1;35m"

# Color codes for user input fields
class InputColor:
    BOLD = "\033[1m"
    BLUE = "\033[1;34m"
    MAGENTA = "\033[1;35m"
    RESET = "\033[0m"
    PURPLE = "\033[1;35m" # Added PURPLE as it was used in original TextColor

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def run_command(command_str, capture_output=False, text=True, shell=True, check=False, display_output=False):
    print(f"{TextColor.YELLOW}[CMD] Executing: {command_str}{TextColor.RESET}")
    log_action(f"Executing command: {command_str}")
    try:
        if display_output:
            result = os.system(command_str)
            log_output_summary(f"Command output (displayed live): {command_str}")
            return result
        if capture_output:
            result = subprocess.run(command_str, shell=shell, capture_output=True, text=text, check=check)
            log_output_summary(result.stdout if result.stdout else "")
            return result
        else:
            result = subprocess.run(command_str, shell=shell, text=text, check=check)
            log_output_summary("Command executed, output sent to stdout/stderr.")
            return result
    except subprocess.CalledProcessError as e:
        log_error(f"Command '{e.cmd}' failed with exit code {e.returncode}")
        if e.stdout:
            log_output_summary(f"Stdout: {e.stdout}")
        if e.stderr:
            log_output_summary(f"Stderr: {e.stderr}")
        print(f"{TextColor.RED}[ERROR] Command '{e.cmd}' failed with exit code {e.returncode}{TextColor.RESET}")
        if e.stdout:
            print(f"{TextColor.RED}Stdout: {e.stdout}{TextColor.RESET}")
        if e.stderr:
            print(f"{TextColor.RED}Stderr: {e.stderr}{TextColor.RESET}")
        return None
    except Exception as e:
        log_error(f"Unexpected error running command '{command_str}': {e}")
        print(f"{TextColor.RED}[ERROR] An unexpected error occurred while running command: {command_str}\n{e}{TextColor.RESET}")
        return None