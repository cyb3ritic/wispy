import os
import subprocess
from .utils import TextColor, InputColor, run_command # Relative import

def check_root():
    if os.geteuid() != 0:
        print(f"{TextColor.RED}[X] This script requires root (administrator) privileges. Please run it as root.{TextColor.RESET}")
        exit(1)

def set_env_vars():
    os.environ['LC_ALL'] = 'C.UTF-8'

def get_network_interfaces():
    try:
        interfaces_out_process = run_command('ifconfig', capture_output=True)
        if interfaces_out_process and interfaces_out_process.stdout:
            interfaces_out = interfaces_out_process.stdout
            interfaces = [line.split(":")[0].strip() for line in interfaces_out.split("\n") if ": flags=" in line and "lo:" not in line]
            return interfaces
        return []
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] Could not get network interfaces: {e}{TextColor.RESET}")
        return []

def get_interface_mode(interface):
    try:
        # Using iw for mode detection
        mode_result = run_command(f'iw dev {interface} info', capture_output=True)
        if mode_result and mode_result.stdout:
            mode_line = [line for line in mode_result.stdout.strip().split('\n') if 'type' in line]
            if mode_line:
                mode = mode_line[0].split("type ")[1].strip()
                return mode
        return "N/A (managed?)" # Or could try parsing ifconfig/ip link for state
    except Exception: # Could be that 'iw' command failed or interface doesn't support it
        # Fallback or simple check if interface is up (very basic)
        try:
            ifconfig_output = run_command(f'ifconfig {interface}', capture_output=True)
            if ifconfig_output and ifconfig_output.stdout:
                 if "RUNNING" in ifconfig_output.stdout: # This is not 'mode' but 'state'
                     return "Managed (Likely)" # Default assumption if 'iw' fails
            return "N/A"
        except Exception:
            return "N/A"


def get_mac_address(interface):
    try:
        mac_result = run_command(f'ifconfig {interface}', capture_output=True)
        if mac_result and mac_result.stdout:
            mac_line = [line for line in mac_result.stdout.strip().split('\n') if 'ether' in line]
            if mac_line:
                mac = mac_line[0].split('ether ')[1].split()[0]
                return mac
        return "N/A"
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] Could not get MAC address for {interface}: {e}{TextColor.RESET}")
        return "N/A"

def mac_randomizer(net_card):
    print(f"{TextColor.BLUE}[*] Current MAC for {net_card}: {get_mac_address(net_card)}{TextColor.RESET}")
    run_command(f"ifconfig {net_card} down")
    print()
    mac_to_change = input(f"{InputColor.BOLD}{InputColor.BLUE}[*] Enter MAC address to replace (Blank for random):{InputColor.RESET} ")

    try:
        if not mac_to_change:
            # Randomize the MAC address
            # The original &> /dev/null suppresses output, good for automation
            # For user feedback, macchanger usually prints new MAC. If using run_command helper,
            # it might be better to let macchanger print, or capture and print.
            # For now, sticking to original suppression.
            run_command(f"macchanger -r {net_card}") # Removed &> /dev/null to see macchanger output
        else:
            run_command(f"macchanger -m {mac_to_change} {net_card}")

        print(f"{TextColor.GREEN}[+] MAC address change initiated.{TextColor.RESET}")
        # MAC might take a moment to reflect, or macchanger shows it.
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] Could not change MAC: {e}{TextColor.RESET}")
        print(f"{TextColor.YELLOW}[!] Please try again later or check your permissions.{TextColor.RESET}")
    finally:
        run_command(f"ifconfig {net_card} up")
        new_mac = get_mac_address(net_card)
        print(f"{TextColor.GREEN}[+] Interface {net_card} is up. New MAC: {new_mac}{TextColor.RESET}")
        input(f"{TextColor.YELLOW}Press Enter to Continue to the Main Menu...{TextColor.RESET}")


def start_monitor_mode(selected_interface):
    print(f"{TextColor.CYAN}[*] Starting monitor mode on {selected_interface}...{TextColor.RESET}")
    # airmon-ng can create a new interface (e.g., wlan0mon)
    # We need to handle this. For now, assume it might change name or use the same.
    run_command(f"sudo airmon-ng start {selected_interface}", display_output=True)
    print(f"{TextColor.GREEN}[+] Monitor mode initiated. Check if a new interface name (e.g., {selected_interface}mon) was created.{TextColor.RESET}")
    print(f"{TextColor.YELLOW}You might need to re-select the interface if its name changed.{TextColor.RESET}")
    # The main loop should ideally re-scan interfaces or update status after this.

def stop_monitor_mode(selected_interface):
    print(f"{TextColor.CYAN}[*] Stopping monitor mode on {selected_interface}...{TextColor.RESET}")
    # Also restart NetworkManager to restore connectivity
    run_command(f"sudo airmon-ng stop {selected_interface}", display_output=True)
    print(f"{TextColor.GREEN}[+] Monitor mode stopped on {selected_interface}.{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] Attempting to restart NetworkManager...{TextColor.RESET}")
    run_command("sudo systemctl restart NetworkManager", display_output=True)
    # An older script might use: run_command("sudo service NetworkManager restart", display_output=True)
    print(f"{TextColor.GREEN}[+] NetworkManager restart initiated.{TextColor.RESET}")