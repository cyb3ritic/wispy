import os
import subprocess
from .utils import TextColor, InputColor, run_command

def check_root():
    if os.geteuid() != 0:
        print(f"{TextColor.RED}[X] This script requires root (administrator) privileges. Please run it as root.{TextColor.RESET}")
        exit(1)

def set_env_vars():
    os.environ['LC_ALL'] = 'C.UTF-8'

def get_network_interfaces():
    """
    Returns a list of available wireless network interfaces (excluding loopback).
    """
    try:
        interfaces_out_process = run_command('ip -o link show', capture_output=True)
        if interfaces_out_process and interfaces_out_process.stdout:
            interfaces_out = interfaces_out_process.stdout
            interfaces = []
            for line in interfaces_out.splitlines():
                # Example: '2: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> ...'
                parts = line.split(':')
                if len(parts) > 1:
                    iface = parts[1].strip()
                    if iface != "lo" and not iface.startswith("docker") and not iface.startswith("br-"):
                        # Check if it's wireless
                        wireless_check = run_command(f"iw dev {iface} info", capture_output=True)
                        if wireless_check and wireless_check.stdout and "Interface" in wireless_check.stdout:
                            interfaces.append(iface)
            return interfaces
        return []
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] Could not get network interfaces: {e}{TextColor.RESET}")
        return []

def get_interface_mode(interface):
    """
    Returns the mode of the given wireless interface (e.g., managed, monitor).
    """
    try:
        mode_result = run_command(f'iw dev {interface} info', capture_output=True)
        if mode_result and mode_result.stdout:
            for line in mode_result.stdout.strip().split('\n'):
                if 'type' in line:
                    return line.split("type")[1].strip().capitalize()
        return "N/A"
    except Exception:
        return "N/A"

def get_mac_address(interface):
    """
    Returns the MAC address of the given interface.
    """
    try:
        mac_result = run_command(f'cat /sys/class/net/{interface}/address', capture_output=True)
        if mac_result and mac_result.stdout:
            return mac_result.stdout.strip()
        return "N/A"
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] Could not get MAC address for {interface}: {e}{TextColor.RESET}")
        return "N/A"

def mac_randomizer(net_card):
    """
    Randomizes or sets a custom MAC address for the given network card.
    """
    print(f"{TextColor.BLUE}[*] Current MAC for {net_card}: {get_mac_address(net_card)}{TextColor.RESET}")
    run_command(f"ip link set {net_card} down")
    print()
    mac_to_change = input(f"{InputColor.BOLD}{InputColor.BLUE}[*] Enter MAC address to replace (Blank for random):{InputColor.RESET} ")

    try:
        if not mac_to_change:
            run_command(f"macchanger -r {net_card}", display_output=True)
        else:
            run_command(f"macchanger -m {mac_to_change} {net_card}", display_output=True)
        print(f"{TextColor.GREEN}[+] MAC address change initiated.{TextColor.RESET}")
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] Could not change MAC: {e}{TextColor.RESET}")
        print(f"{TextColor.YELLOW}[!] Please try again later or check your permissions.{TextColor.RESET}")
    finally:
        run_command(f"ip link set {net_card} up")
        new_mac = get_mac_address(net_card)
        print(f"{TextColor.GREEN}[+] Interface {net_card} is up. New MAC: {new_mac}{TextColor.RESET}")
        input(f"{TextColor.YELLOW}Press Enter to Continue to the Main Menu...{TextColor.RESET}")

def start_monitor_mode(selected_interface):
    """
    Enables monitor mode on the selected interface.
    """
    print(f"{TextColor.CYAN}[*] Starting monitor mode on {selected_interface}...{TextColor.RESET}")
    run_command(f"sudo airmon-ng check kill", display_output=True)
    result = run_command(f"sudo airmon-ng start {selected_interface}", display_output=True)
    print(f"{TextColor.GREEN}[+] Monitor mode initiated. Check if a new interface name (e.g., {selected_interface}mon) was created.{TextColor.RESET}")
    print(f"{TextColor.YELLOW}You might need to re-select the interface if its name changed.{TextColor.RESET}")

def stop_monitor_mode(selected_interface):
    """
    Disables monitor mode on the selected interface and restarts NetworkManager.
    """
    print(f"{TextColor.CYAN}[*] Stopping monitor mode on {selected_interface}...{TextColor.RESET}")
    run_command(f"sudo airmon-ng stop {selected_interface}", display_output=True)
    print(f"{TextColor.GREEN}[+] Monitor mode stopped on {selected_interface}.{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] Attempting to restart NetworkManager...{TextColor.RESET}")
    # Try systemctl, fallback to service if needed
    result = run_command("sudo systemctl restart NetworkManager", display_output=True)
    if result and result.returncode != 0:
        run_command("sudo service NetworkManager restart", display_output=True)
    print(f"{TextColor.GREEN}[+] NetworkManager restart initiated.{TextColor.RESET}")