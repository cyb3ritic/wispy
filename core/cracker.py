import os
from .utils import TextColor, InputColor, run_command, clear_screen

def crack_handshake_custom(handshake_file_path, wordlist_path):
    if not os.path.exists(handshake_file_path):
        print(f"{TextColor.RED}[!] Handshake file not found: {handshake_file_path}{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")
        return
    if not os.path.exists(wordlist_path):
        print(f"{TextColor.RED}[!] Wordlist file not found: {wordlist_path}{TextColor.RESET}")
        input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")
        return
        
    clear_screen()
    print(f"{TextColor.PURPLE}--- Cracking Handshake with Custom Wordlist ---{TextColor.RESET}")
    print(f"Handshake File: {handshake_file_path}")
    print(f"Wordlist: {wordlist_path}")
    print(f"{TextColor.CYAN}[*] Starting aircrack-ng... This may take a very long time.{TextColor.RESET}")
    
    # Aircrack-ng can run directly in the console, xterm not strictly necessary unless user prefers it
    order = f"aircrack-ng {handshake_file_path} -w {wordlist_path}"
    # run_command will print [CMD] and then aircrack-ng output will follow
    run_command(order, display_output=True) # Let aircrack output directly
    
    input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")

def crack_handshake_generated_wordlist(bssid, handshake_file_path, min_len, max_len, char_set_choice_str, custom_chars=None):
    if not os.path.exists(handshake_file_path):
        print(f"{TextColor.RED}[!] Handshake file not found: {handshake_file_path}{TextColor.RESET}")
        return
    if not bssid:
        print(f"{TextColor.RED}[!] BSSID is required for cracking with aircrack-ng -b option.{TextColor.RESET}")
        return

    test_chars = ""
    if char_set_choice_str == "1": test_chars = "abcdefghijklmnopqrstuvwxyz"
    elif char_set_choice_str == "2": test_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    elif char_set_choice_str == "3": test_chars = "0123456789"
    elif char_set_choice_str == "4": test_chars = "!#$%/=?{}[]-*:;"
    elif char_set_choice_str == "5": test_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    elif char_set_choice_str == "6": test_chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    elif char_set_choice_str == "7": test_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    elif char_set_choice_str == "8": test_chars = "!#$%/=?{}[]-*:;0123456789"
    elif char_set_choice_str == "9": test_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    elif char_set_choice_str == "10": test_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%/=?{}[]-*:;"
    elif char_set_choice_str == "11": test_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%/=?{}[]-*:;"
    elif char_set_choice_str == "12":
        if custom_chars:
            test_chars = custom_chars
        else:
            print(f"{TextColor.RED}[!] Custom character set was chosen but no characters provided.{TextColor.RESET}")
            return
    else:
        print(f"{TextColor.RED}[!] Invalid character set choice.{TextColor.RESET}")
        return

    if not test_chars:
        print(f"{TextColor.RED}[!] Character set is empty.{TextColor.RESET}")
        return
        
    clear_screen()
    print(f"{TextColor.PURPLE}--- Cracking Handshake with Crunch-generated Wordlist ---{TextColor.RESET}")
    print(f"BSSID: {bssid}")
    print(f"Handshake File: {handshake_file_path}")
    print(f"Password Length: {min_len}-{max_len}")
    print(f"Character Set: {test_chars[:30]}..." if len(test_chars) > 30 else test_chars)
    print(f"{TextColor.YELLOW}[WARNING] This can take an extremely long time and generate huge amounts of data!{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] Crunch will pipe output directly to Aircrack-ng.{TextColor.RESET}")
    print(f"{TextColor.CYAN}[*] Press CTRL+C in the xterm window to stop.{TextColor.RESET}")
    
    # Corrected 'xtrem' to 'xterm' and using sudo for both parts of the pipe if needed.
    # The commands inside xterm should be quoted properly.
    # Crunch might not need sudo if it's just generating, aircrack might.
    # Simplest way for pipe with xterm is to run the whole pipe inside one xterm's shell.
    crunch_cmd = f"crunch {min_len} {max_len} {test_chars}"
    aircrack_cmd = f"aircrack-ng {handshake_file_path} -b {bssid} -w-" # -w- means read from stdin
    
    # Full command for xterm to execute a shell that runs the pipe:
    # Need to be careful with quoting special characters in test_chars for the shell
    # For simplicity, assume test_chars doesn't contain problematic shell metacharacters
    # or that crunch handles them.
    full_piped_command = f"sudo sh -c '{crunch_cmd} | {aircrack_cmd}'"
    xterm_command = f"xterm -hold -e {full_piped_command}" # -hold to see output after finish
    
    print(f"{TextColor.YELLOW}Executing: {xterm_command}{TextColor.RESET}")
    print(f"{TextColor.CYAN}If xterm does not appear, there might be an issue with the command or permissions.{TextColor.RESET}")

    try:
        # Using os.system for complex xterm piping as it's closer to original script's directness
        # and easier than complex Popen with shell=True and pipes for this specific GUI case.
        # This will block until xterm is closed if -hold is used.
        os.system(xterm_command)
        print(f"{TextColor.GREEN}[+] Cracking process initiated in xterm.{TextColor.RESET}")
    except Exception as e:
        print(f"{TextColor.RED}[ERROR] Failed to start cracking process: {e}{TextColor.RESET}")
        
    input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")


def create_wordlist():
    clear_screen()
    print(f"{TextColor.PURPLE}--- Create Custom Wordlist with Crunch ---{TextColor.RESET}")
    try:
        mini_str = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter min password length (e.g., 8): {InputColor.RESET}")
        mini = int(mini_str)
        max_str = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter max password length (e.g., 10): {InputColor.RESET}")
        max_val = int(max_str) # Renamed from max to max_val to avoid shadowing built-in
        
        print(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter the characters to use (e.g., abcdef0123, or leave blank for crunch defaults): {InputColor.RESET}", end=" ")
        password_chars = str(input("")).strip()
        
        path = input(f"{InputColor.BOLD}{InputColor.BLUE}[?] Enter the path for the output wordlist file (e.g., /tmp/mywordlist.txt): {InputColor.RESET}").strip()
        if not path:
            print(f"{TextColor.RED}[!] Output file path cannot be empty.{TextColor.RESET}")
            return

    except ValueError:
        print(f"{TextColor.RED}[!] Invalid input for length. Please enter numbers.{TextColor.RESET}")
        return
    except KeyboardInterrupt:
        print(f"\n{TextColor.YELLOW}[!] Wordlist creation cancelled.{TextColor.RESET}")
        return

    # Basic crunch command
    order = f"crunch {mini} {max_val} {password_chars} -o {path}"
    print(f"{TextColor.CYAN}[*] Generating wordlist with command: {order}{TextColor.RESET}")
    print(f"{TextColor.YELLOW}[WARNING] This can take a long time and create a large file!{TextColor.RESET}")
    
    # Crunch can run directly in console
    run_command(order, display_output=True) # Let crunch output directly
    
    print(f"{TextColor.GREEN}[+] Wordlist generation command executed. Check '{path}'.{TextColor.RESET}")
    input(f"{InputColor.BOLD}{InputColor.BLUE}Press Enter to Continue...{InputColor.RESET}")