import os
import subprocess

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
    """
    Runs a shell command using subprocess.run.
    If display_output is True, command output is not captured but shown live.
    Otherwise, captures and returns output if capture_output is True.
    """
    print(f"{TextColor.YELLOW}[CMD] Executing: {command_str}{TextColor.RESET}")
    try:
        if display_output:
            # For commands that need interactive output or are long-running in a terminal (like airodump-ng in xterm)
            # We assume they manage their own output directly (e.g. opening xterm)
            # For simpler direct commands that should display in current console:
            # result = subprocess.run(command_str, shell=shell, check=check, text=text)
            # For now, if display_output is true, we mimic os.system behavior for simplicity in refactor
            return os.system(command_str) # This maintains original behavior for xterm calls etc.
        
        if capture_output:
            result = subprocess.run(command_str, shell=shell, capture_output=True, text=text, check=check)
            return result
        else:
            # Runs command, output goes to stdout/stderr of this script
            result = subprocess.run(command_str, shell=shell, text=text, check=check)
            return result # Returns CompletedProcess instance, not output
    except subprocess.CalledProcessError as e:
        print(f"{TextColor.RED}[ERROR] Command '{e.cmd}' failed with exit code {e.returncode}{TextColor.RESET}")
        if e.stdout:
            print(f"{TextColor.RED}Stdout: {e.stdout}{TextColor.RESET}")
        if e.stderr:
            print(f"{TextColor.RED}Stderr: {e.stderr}{TextColor.RESET}")
        return None
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] An unexpected error occurred while running command: {command_str}\n{e}{TextColor.RESET}")
        return None