import time
import shutil
from .utils import TextColor, InputColor, run_command, clear_screen

def _get_terminal_emulator():
    """
    Returns the best available terminal emulator command for the system.
    """
    for term in ["x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "xterm"]:
        if shutil.which(term):
            return term
    return None

def scan_networks(selected_interface):
    """
    Launches airodump-ng in a new terminal window to scan for wireless networks.
    """
    if not selected_interface:
        print(f"{TextColor.RED}[!] No interface selected for scanning.{TextColor.RESET}")
        return

    terminal = _get_terminal_emulator()
    if not terminal:
        print(f"{TextColor.RED}[!] No supported terminal emulator found. Please install xterm, gnome-terminal, or similar.{TextColor.RESET}")
        return

    print(f"{TextColor.CYAN}[*] Preparing to scan networks on {selected_interface}...{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] A new terminal window will open. Press [CTRL+C] in that window to stop scanning.{TextColor.RESET}")
    time.sleep(1)

    if "xterm" in terminal:
        order = f"sudo xterm -hold -e 'airodump-ng {selected_interface}'"
    else:
        order = f"sudo {terminal} -- bash -c 'airodump-ng {selected_interface}; exec bash'"

    run_command(order, display_output=True)
    print(f"{TextColor.GREEN}[+] Network scan initiated in a new window.{TextColor.RESET}")
    time.sleep(1)

def scan_for_wps_networks(selected_interface):
    """
    Launches airodump-ng with --wps in a new terminal window to scan for WPS-enabled networks.
    """
    if not selected_interface:
        print(f"{TextColor.RED}[!] No interface selected for WPS scanning.{TextColor.RESET}")
        return

    terminal = _get_terminal_emulator()
    if not terminal:
        print(f"{TextColor.RED}[!] No supported terminal emulator found. Please install xterm, gnome-terminal, or similar.{TextColor.RESET}")
        return

    print(f"{TextColor.CYAN}[*] Preparing to scan for WPS networks on {selected_interface}...{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] A new terminal window will open. Press [CTRL+C] in that window to stop scanning.{TextColor.RESET}")
    time.sleep(1)

    if "xterm" in terminal:
        order = f"sudo xterm -hold -e 'airodump-ng --wps {selected_interface}'"
    else:
        order = f"sudo {terminal} -- bash -c 'airodump-ng --wps {selected_interface}; exec bash'"

    run_command(order, display_output=True)
    print(f"{TextColor.GREEN}[+] WPS network scan initiated in a new window.{TextColor.RESET}")
    time.sleep(1)