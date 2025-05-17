import os # os.system is used in original, will be replaced by run_command
from .utils import TextColor, InputColor, run_command, clear_screen
import time

def scan_networks(selected_interface):
    if not selected_interface:
        print(f"{TextColor.RED}[!] No interface selected for scanning.{TextColor.RESET}")
        return

    print(f"{TextColor.CYAN}[*] Preparing to scan networks on {selected_interface}...{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] When scan window (xterm) appears, press [CTRL+C] in that window to stop.{TextColor.RESET}")
    time.sleep(3) # Original sleep
    # The -M flag for airodump-ng might not be standard or universally supported/needed.
    # It was related to older madwifi-ng drivers. Modern drivers usually don't need it.
    # Keeping it for now to match original behavior.
    # Using xterm as per original script.
    order = f"sudo xterm -e airodump-ng {selected_interface} -M"
    run_command(order, display_output=True) # display_output=True as xterm handles its own window
    print(f"{TextColor.GREEN}[+] Network scan initiated in a new window.{TextColor.RESET}")
    time.sleep(3) # Original sleep

def scan_for_wps_networks(selected_interface):
    if not selected_interface:
        print(f"{TextColor.RED}[!] No interface selected for WPS scanning.{TextColor.RESET}")
        return
    print(f"{TextColor.CYAN}[*] Preparing to scan for WPS networks on {selected_interface}...{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] When scan window (xterm) appears, press [CTRL+C] in that window to stop.{TextColor.RESET}")
    time.sleep(1) # Shorter sleep, seems reasonable
    order = f"sudo xterm -e airodump-ng --wps {selected_interface}"
    run_command(order, display_output=True)
    print(f"{TextColor.GREEN}[+] WPS network scan initiated in a new window.{TextColor.RESET}")
    time.sleep(5) # Original sleep