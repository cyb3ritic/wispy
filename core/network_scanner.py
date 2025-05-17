import os
import time
import subprocess
import csv
import datetime
import itertools
import sys
from prettytable import PrettyTable
from .utils import TextColor, InputColor, clear_screen

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

def interface_exists(interface_name):
    return os.path.exists(f"/sys/class/net/{interface_name}/operstate")

def scan_networks(selected_interface):
    if not selected_interface:
        print(f"{TextColor.RED}[!] No interface selected.{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to continue...{InputColor.RESET}")
        return

    if not interface_exists(selected_interface):
        print(f"{TextColor.RED}[!] Interface {selected_interface} not found.{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to continue...{InputColor.RESET}")
        return

    clear_screen()
    print(f"{TextColor.CYAN}[*] Starting Wi-Fi scan on {selected_interface} (Press CTRL+C to stop)...{TextColor.RESET}")
    base_path = os.path.join(REPORTS_DIR, "network_scanner_result")
    csv_path = base_path + "-01.csv"
    result_path = os.path.join(REPORTS_DIR, "network_scanner_result.txt")

    cmd = ["sudo", "airodump-ng", selected_interface, "--write", base_path, "--output-format", "csv"]

    try:
        proc = subprocess.Popen(cmd)
        time.sleep(5)  # Let airodump collect a few entries

        while True:
            if os.path.exists(csv_path):
                try:
                    networks = parse_csv(csv_path)
                    display_table(networks)
                    time.sleep(3)
                    clear_screen()
                except Exception:
                    pass
    except KeyboardInterrupt:
        print(f"{TextColor.YELLOW}[*] Scan interrupted. Finalizing output...{TextColor.RESET}")
        proc.terminate()
    except Exception as e:
        print(f"{TextColor.RED}[!] Error: {e}{TextColor.RESET}")
        return

    if os.path.exists(csv_path):
        try:
            networks = parse_csv(csv_path)
            save_result(result_path, networks)
            print(f"{TextColor.GREEN}[+] Final report saved to: {result_path}{TextColor.RESET}")
        except Exception as e:
            print(f"{TextColor.RED}[!] Failed to process results: {e}{TextColor.RESET}")
    else:
        print(f"{TextColor.YELLOW}[!] No output found. Nothing to save.{TextColor.RESET}")

    # Clean leftover files
    for ext in ["-01.csv", "-01.cap", "-01.kismet.csv", "-01.log.csv"]:
        try:
            os.remove(base_path + ext)
        except FileNotFoundError:
            pass

    input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to continue...{InputColor.RESET}")

def parse_csv(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    header_found = False
    networks = []

    for line in lines:
        if not header_found:
            if line.strip().startswith("BSSID"):
                header_found = True
            continue

        if header_found and line.strip():
            row = [col.strip() for col in line.split(",")]
            if len(row) < 14 or not row[0].count(":") == 5:
                continue

            network = {
                "BSSID": row[0],
                "Channel": row[3],
                "Power": row[8],
                "Privacy": row[5],
                "Cipher": row[6],
                "Auth": row[7],
                "ESSID": row[13]
            }
            networks.append(network)

    return networks

def display_table(networks):
    if not networks:
        print(f"{TextColor.YELLOW}[!] No networks found yet...{TextColor.RESET}")
        return

    # Find strongest and weakest signals
    try:
        powers = [int(net["Power"]) for net in networks if net["Power"].lstrip('-').isdigit()]
        strongest = max(powers) if powers else None
        weakest = min(powers) if powers else None
    except Exception:
        strongest = weakest = None

    # Summary
    print(f"{TextColor.BOLD}{TextColor.CYAN}Scan Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{TextColor.RESET}")
    print(f"{TextColor.GREEN}Networks Detected: {len(networks)}{TextColor.RESET}", end="  ")
    if strongest is not None:
        print(f"{TextColor.BOLD}Strongest: {strongest} dBm{TextColor.RESET}", end="  ")
    if weakest is not None:
        print(f"Weakest: {weakest} dBm", end="")
    print("\n")

    table = PrettyTable()
    table.field_names = ["#", "BSSID", "Channel", "Power", "Privacy", "Cipher", "Auth", "ESSID"]

    for i, net in enumerate(networks):
        essid = net["ESSID"] or "<Hidden>"
        # Color for ESSID
        if not net["ESSID"]:
            essid = f"{TextColor.RED}<Hidden>{TextColor.RESET}"
        elif "WEP" in net["Privacy"] or "WPA" in net["Privacy"]:
            essid = f"{TextColor.YELLOW}{essid}{TextColor.RESET}"
        else:
            essid = f"{TextColor.GREEN}{essid}{TextColor.RESET}"

        # Highlight strongest signal
        power = net["Power"]
        if strongest is not None and power.lstrip('-').isdigit() and int(power) == strongest:
            power = f"{TextColor.BOLD}{TextColor.GREEN}{power}{TextColor.RESET}"

        table.add_row([
            i + 1,
            net["BSSID"],
            net["Channel"],
            power,
            net["Privacy"],
            net["Cipher"],
            net["Auth"],
            essid
        ])

    print(f"{TextColor.BOLD}{TextColor.GREEN}Detected Wi-Fi Networks:{TextColor.RESET}")
    print(table)

def save_result(path, networks):
    with open(path, "w") as f:
        f.write("Detected Wi-Fi Networks\n")
        f.write("=" * 70 + "\n")
        for i, net in enumerate(networks):
            f.write(f"{i+1}. ESSID : {net['ESSID'] or '<Hidden>'}\n")
            f.write(f"    BSSID : {net['BSSID']}\n")
            f.write(f"    Channel: {net['Channel']} | Signal: {net['Power']} dBm\n")
            f.write(f"    Security: {net['Privacy']} ({net['Cipher']} / {net['Auth']})\n")
            f.write("-" * 70 + "\n")
