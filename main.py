import os
import time
from core.utils import TextColor, InputColor, clear_screen
from core.interface_handler import (
    check_root, set_env_vars, get_network_interfaces,
    get_interface_mode, get_mac_address, mac_randomizer,
    start_monitor_mode, stop_monitor_mode
)
from core.scanner import scan_networks, scan_for_wps_networks
from core.attacker import get_handshake, deauth_main, wps_network_attacks
from core.cracker import (
    crack_handshake_custom, create_wordlist,
    crack_handshake_generated_wordlist
)
from core.detector import (
    detect_weak_encryption, detect_rogue_aps,
    start_deauth_attack_detection
)
from core.logger import log_action, log_error

def display_banner():
    print(TextColor.PURPLE + """

░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓███████▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓██████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░     
 ░▒▓█████████████▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░         ░▒▓█▓▒░     
                                                                   
                                                                   
""" + TextColor.RED + """
WiSpy: Wireless Network Security Scanner
Author : Debajyoti0-0 (Original) & Gemini (Refactor/Upgrade)
Version: 1.1.0 (Refactored)
Github : https://github.com/Debajyoti0-0/ (Original Project)""" + TextColor.RESET)

def display_main_menu(interface_name, interface_mode_val, mac_address_val):
    clear_screen()
    display_banner()
    print(f"{TextColor.GREEN}--------------------------------------------------------------------------------{TextColor.RESET}")
    print(f"{TextColor.BLUE}[+] Selected Interface:{TextColor.RESET}\t{TextColor.YELLOW}{interface_name if interface_name else 'None'}{TextColor.RESET}")
    print(f"{TextColor.BLUE}[+] Interface Mode:{TextColor.RESET}\t\t{TextColor.YELLOW}{interface_mode_val if interface_name else 'N/A'}{TextColor.RESET}")
    print(f"{TextColor.BLUE}[+] MAC Address:{TextColor.RESET}\t\t{TextColor.YELLOW}{mac_address_val if interface_name else 'N/A'}{TextColor.RESET}")
    print(f"{TextColor.GREEN}--------------------------------------------------------------------------------{TextColor.RESET}")
    
    menu_options = {
        "1": "Start Monitor Mode",
        "2": "Stop Monitor Mode",
        "3": "Scan Networks (airodump-ng)",
        "4": "Capture Handshake (airodump-ng + aireplay-ng)",
        "5": "Deauthentication Attacks (aireplay-ng)",
        "6": "MAC Address Randomizer (macchanger)",
        "7": "Crack Handshake (aircrack-ng, custom wordlist)",
        "8": "Crack Handshake (aircrack-ng + crunch)",
        "9": "Create Wordlist (crunch)",
        "10": "WPS Network Attacks (Reaver, Bully, Wifite)",
        "11": "Scan for WPS Networks (airodump-ng --wps)",
        "12": f"{TextColor.CYAN}Detect Weak Encryption (Placeholder){TextColor.RESET}",
        "13": f"{TextColor.CYAN}Detect Rogue APs (Placeholder){TextColor.RESET}",
        "14": f"{TextColor.CYAN}Start Deauth Attack Detection (Placeholder){TextColor.RESET}",
        "0": "Exit",
        "R": "Reselect Network Interface" # New option
    }

    for key, value in menu_options.items():
        print(f"({key}) {value}")
    print(f"{TextColor.GREEN}--------------------------------------------------------------------------------{TextColor.RESET}")

def main():
    check_root()
    set_env_vars()

    selected_interface = None
    current_mac = "N/A"
    current_mode = "N/A"

    while True: # Outer loop for interface selection
        network_interfaces = get_network_interfaces()
        if not network_interfaces:
            clear_screen()
            display_banner()
            print(f"{TextColor.RED}[!] No suitable network interfaces found. Ensure wireless adapters are connected and drivers are loaded.{TextColor.RESET}")
            print(f"{TextColor.YELLOW}Common wireless interface names: wlan0, wlan1, ath0, etc.{TextColor.RESET}")
            if input(f"{InputColor.BOLD}{InputColor.BLUE}Try scanning for interfaces again? (y/n): {InputColor.RESET}").lower() != 'y':
                print(f"{TextColor.YELLOW}[^] Exiting WiSpy. Goodbye! 👋{TextColor.RESET}")
                exit(0)
            continue # Retry getting interfaces

        clear_screen()
        display_banner()
        print(f"{TextColor.GREEN}--------------------------------------------------------------------------------{TextColor.RESET}")
        print(f"{TextColor.CYAN}\n[+] Available network interfaces:{TextColor.RESET}")
        for i, iface_name in enumerate(network_interfaces):
            print(f"{TextColor.CYAN}\t{i + 1}) {iface_name}{TextColor.RESET}")
        print(f"\n{TextColor.CYAN}\t0) Exit WiSpy{TextColor.RESET}")

        try:
            choice_str = input(f"{InputColor.BOLD}{InputColor.MAGENTA}\n[?] Choose the number of the interface to use: {InputColor.RESET}")
            if not choice_str: # User pressed Enter
                print(f"{TextColor.RED}[!] No choice made. Please select an interface or exit.{TextColor.RESET}")
                time.sleep(2)
                continue

            choice = int(choice_str)

            if choice == 0:
                print(f"{TextColor.YELLOW}[^] Exiting WiSpy as per your choice. Goodbye! 👋{TextColor.RESET}")
                exit(0)
            
            if 1 <= choice <= len(network_interfaces):
                selected_interface = network_interfaces[choice - 1]
                current_mac = get_mac_address(selected_interface)
                current_mode = get_interface_mode(selected_interface) # Initial mode
                print(f"{TextColor.GREEN}[+] Interface '{selected_interface}' selected.{TextColor.RESET}")
                time.sleep(1)
                break # Exit interface selection loop, proceed to main menu
            else:
                print(f"{TextColor.RED}[!] Invalid choice. Please select a number from the list.{TextColor.RESET}")
                time.sleep(2)
        except ValueError:
            print(f"{TextColor.RED}[!] Invalid input. Please enter a number.{TextColor.RESET}")
            time.sleep(2)
        except KeyboardInterrupt:
            print(f"\n{TextColor.YELLOW}[^] Exiting WiSpy. Goodbye! 👋{TextColor.RESET}")
            exit(0)

    # Main application loop
    while True:
        if selected_interface: # Refresh status before displaying menu
            current_mac = get_mac_address(selected_interface)
            current_mode = get_interface_mode(selected_interface)
        
        display_main_menu(selected_interface, current_mode, current_mac)
        
        try:
            user_choice = input(TextColor.CYAN + "[?] Enter your choice: " + TextColor.RESET).strip().upper()
            log_action(f"User selected menu option: {user_choice}")
        except KeyboardInterrupt:
            log_action("User exited via KeyboardInterrupt")
            print(f"\n{TextColor.YELLOW}[^] Exiting WiSpy. Goodbye! 👋{TextColor.RESET}")
            break

        if not selected_interface and user_choice not in ["0", "R"]:
            print(f"{TextColor.RED}[!] No interface selected. Please choose 'R' to reselect or '0' to exit.{TextColor.RESET}")
            input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")
            continue

        if user_choice == "1":
            start_monitor_mode(selected_interface)
            # Interface name might change (e.g. wlan0 to wlan0mon)
            # For simplicity, we tell user to reselect. A more advanced way is to detect new name.
            print(f"{TextColor.YELLOW}[!] Interface mode changed. If interface name changed (e.g. to {selected_interface}mon), please Reselect (R).{TextColor.RESET}")
            input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")
        elif user_choice == "2":
            stop_monitor_mode(selected_interface) # Pass current name. airmon-ng stop usually works with mon name.
            print(f"{TextColor.YELLOW}[!] Interface mode changed. Please Reselect (R) if needed.{TextColor.RESET}")
            input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")
        elif user_choice == "3":
            scan_networks(selected_interface)
        elif user_choice == "4":
            get_handshake(selected_interface)
        elif user_choice == "5":
            deauth_main(selected_interface)
        elif user_choice == "6":
            mac_randomizer(selected_interface)
            # MAC address changed, current_mac will refresh at start of loop
        elif user_choice == "7":
            clear_screen()
            print(f"{TextColor.PURPLE}--- Crack Handshake with Custom Wordlist ---{TextColor.RESET}")
            h_file = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Path to handshake file (.cap, .pcap): {InputColor.RESET}").strip()
            w_file = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Path to wordlist file: {InputColor.RESET}").strip()
            if h_file and w_file:
                crack_handshake_custom(h_file, w_file)
            else:
                print(f"{TextColor.RED}[!] Handshake file and wordlist path are required.{TextColor.RESET}")
                input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{TextColor.RESET}")
        elif user_choice == "8":
            clear_screen()
            print(f"{TextColor.PURPLE}--- Crack Handshake with Crunch Generated Wordlist ---{TextColor.RESET}")
            bssid_val = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] BSSID of the target network: {InputColor.RESET}").strip()
            h_file_val = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Path to handshake file: {InputColor.RESET}").strip()
            try:
                min_l = int(input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Min password length (e.g., 8): {InputColor.RESET}"))
                max_l = int(input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Max password length (e.g., 10): {InputColor.RESET}"))
                
                print(TextColor.CYAN + """
Character Set Options for Crunch:
(1) Lowercase (a-z)           (2) Uppercase (A-Z)
(3) Numeric (0-9)             (4) Symbols (!#$%/=?{}[]-*:;)
(5) Lower + Upper             (6) Lower + Numeric
(7) Upper + Numeric           (8) Symbol + Numeric
(9) Lower + Upper + Numeric   (10) Lower + Upper + Symbol
(11) Lower + Upper + Numeric + Symbol
(12) Your Custom Characters
                """ + TextColor.RESET)
                set_choice = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Character set choice: {InputColor.RESET}").strip()
                custom_set = None
                if set_choice == "12":
                    custom_set = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter custom characters: {InputColor.RESET}").strip()

                if bssid_val and h_file_val:
                    crack_handshake_generated_wordlist(bssid_val, h_file_val, min_l, max_l, set_choice, custom_set)
                else:
                    print(f"{TextColor.RED}[!] BSSID and handshake file are required.{TextColor.RESET}")
            except ValueError:
                print(f"{TextColor.RED}[!] Invalid length. Please enter numbers.{TextColor.RESET}")
            input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")

        elif user_choice == "9":
            create_wordlist()
        elif user_choice == "10":
            wps_network_attacks(selected_interface)
        elif user_choice == "11":
            scan_for_wps_networks(selected_interface)
        elif user_choice == "12":
            detect_weak_encryption(selected_interface)
        elif user_choice == "13":
            # known_aps_file = input("Path to known APs config (optional, press Enter to skip): ").strip()
            detect_rogue_aps(selected_interface) # Pass known_aps_file if implemented
        elif user_choice == "14":
            start_deauth_attack_detection(selected_interface)
        elif user_choice == "R": # Reselect interface
            # Effectively breaks inner loop to go to outer interface selection loop
            selected_interface = None # Reset selected interface
            current_mac = "N/A"
            current_mode = "N/A"
            # Need to break this inner while loop and restart the outer one.
            # This is achieved by setting a flag or just letting it loop to interface selection again.
            # For now, directly call main() but this creates recursion. Better to restructure.
            # A simple way: break this loop, and the outer loop condition will re-trigger interface selection
            # For that, the outer loop needs to be `while True` and `main_app_loop_active` flag.
            # Simpler: set selected_interface to None and let it re-enter interface selection part.
            # The current structure will re-enter the interface selection if we `continue` here
            # after setting selected_interface to None, and the very first part of the script is interface selection.
            # Let's try restarting the main selection process:
            print(f"{TextColor.YELLOW}Returning to interface selection...{TextColor.RESET}")
            time.sleep(1)
            # This recursive call is not ideal but matches the single-file script's implicit reset.
            # A better way would be a state machine or breaking out of this loop to the top.
            # For now, to keep it simple, this will work.
            main() # Restart the whole process
            return # Exit current main instance

        elif user_choice == "0":
            print(TextColor.YELLOW + "[^] Exiting WiSpy. Goodbye! 👋" + TextColor.RESET)
            break # Exit main application loop
        else:
            print(TextColor.RED + "[!] Invalid choice. Please try again." + TextColor.RESET)
            input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")

if __name__ == "__main__":
    main()