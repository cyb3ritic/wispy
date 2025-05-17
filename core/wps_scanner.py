import os
import time
import subprocess
import re
from prettytable import PrettyTable

from .utils import TextColor, InputColor, clear_screen

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

def interface_exists(interface_name):
    return os.path.exists(f"/sys/class/net/{interface_name}/operstate")

class WPSScanner:
    def __init__(self, interface):
        self.interface = interface
        self.monitor_interface = None

    def enable_monitor_mode(self):
        """
        Enables monitor mode on the specified wireless interface using airmon-ng.
        """
        try:
            # Run airmon-ng to enable monitor mode
            result = subprocess.run(
                ["airmon-ng", "start", self.interface],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Error enabling monitor mode: {result.stderr.strip()}")

            # Extract the monitor mode interface name from the output
            for line in result.stdout.splitlines():
                if "monitor mode enabled" in line.lower():
                    self.monitor_interface = line.split()[-1]
                    break

            if not self.monitor_interface:
                raise RuntimeError("Failed to determine monitor mode interface.")
        except FileNotFoundError:
            raise RuntimeError("The 'airmon-ng' tool is not installed or not in PATH.")
        except Exception as e:
            raise RuntimeError(f"An error occurred while enabling monitor mode: {e}")

    def disable_monitor_mode(self):
        """
        Disables monitor mode on the wireless interface using airmon-ng.
        """
        if self.monitor_interface:
            try:
                subprocess.run(
                    ["airmon-ng", "stop", self.monitor_interface],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            except Exception as e:
                raise RuntimeError(f"An error occurred while disabling monitor mode: {e}")

    def scan(self):
        """
        Scans for WPS-enabled networks using the specified wireless interface.
        Returns a list of dictionaries containing network details.
        """
        try:
            self.enable_monitor_mode()

            # Run the `wash` command to scan for WPS-enabled networks
            result = subprocess.run(
                ["wash", "-i", self.monitor_interface, "-o", "stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Error running wash: {result.stderr.strip()}")

            return self._parse_wash_output(result.stdout)
        except Exception as e:
            raise RuntimeError(f"An error occurred during scanning: {e}")
        finally:
            self.disable_monitor_mode()

    def _parse_wash_output(self, output):
        """
        Parses the output of the `wash` command and extracts network details.
        """
        networks = []
        lines = output.splitlines()

        # Skip the header lines
        for line in lines[2:]:
            columns = re.split(r'\s{2,}', line.strip())
            if len(columns) >= 5:
                networks.append({
                    "bssid": columns[0],
                    "channel": columns[1],
                    "wps_version": columns[2],
                    "wps_locked": columns[3],
                    "essid": columns[4]
                })

        return networks

def scan_for_wps_networks(selected_interface):
    if not selected_interface:
        print(f"{TextColor.RED}[!] No interface selected.{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to continue...{InputColor.RESET}")
        return

    if not interface_exists(selected_interface):
        print(f"{TextColor.RED}[!] Interface {selected_interface} not found.{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to continue...{InputColor.RESET}")
        return

    clear_screen()
    print(f"{TextColor.CYAN}[*] Scanning for WPS-enabled networks on {selected_interface} (Press CTRL+C to stop)...{TextColor.RESET}")
    result_path = os.path.join(REPORTS_DIR, "wps_scanner_result.txt")

    scanner = WPSScanner(selected_interface)
    networks = []

    try:
        for _ in range(2):  # Scan twice for demonstration, adjust as needed
            try:
                networks = scanner.scan()
                display_wps_table(networks)
                time.sleep(5)
                clear_screen()
            except Exception as e:
                print(f"{TextColor.RED}[!] Error: {e}{TextColor.RESET}")
                break
    except KeyboardInterrupt:
        print(f"{TextColor.YELLOW}[*] Scan interrupted. Finalizing output...{TextColor.RESET}")
    except Exception as e:
        print(f"{TextColor.RED}[!] Error: {e}{TextColor.RESET}")

    if networks:
        save_wps_result(result_path, networks)
        print(f"{TextColor.GREEN}[+] Final report saved to: {result_path}{TextColor.RESET}")
    else:
        print(f"{TextColor.YELLOW}[!] No WPS-enabled networks found.{TextColor.RESET}")

    input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to continue...{InputColor.RESET}")

def display_wps_table(networks):
    if not networks:
        print(f"{TextColor.YELLOW}[!] No WPS-enabled networks found yet...{TextColor.RESET}")
        return

    table = PrettyTable()
    table.field_names = ["#", "BSSID", "Channel", "WPS Version", "WPS Locked", "ESSID"]

    for i, net in enumerate(networks):
        table.add_row([
            i + 1,
            net.get("bssid", ""),
            net.get("channel", ""),
            net.get("wps_version", ""),
            net.get("wps_locked", ""),
            net.get("essid", "") or "<Hidden>"
        ])

    print(f"{TextColor.BOLD}{TextColor.GREEN}Detected WPS-enabled Networks:{TextColor.RESET}")
    print(table)

def save_wps_result(path, networks):
    with open(path, "w") as f:
        f.write("Detected WPS-enabled Networks\n")
        f.write("=" * 70 + "\n")
        for i, net in enumerate(networks):
            f.write(f"{i+1}. ESSID : {net.get('essid', '') or '<Hidden>'}\n")
            f.write(f"    BSSID : {net.get('bssid', '')}\n")
            f.write(f"    Channel: {net.get('channel', '')}\n")
            f.write(f"    WPS Version: {net.get('wps_version', '')}\n")
            f.write(f"    WPS Locked: {net.get('wps_locked', '')}\n")
            f.write("-" * 70 + "\n")