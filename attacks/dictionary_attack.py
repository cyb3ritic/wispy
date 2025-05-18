
import os
import time
from scapy.all import *
from rich.table import Table
from rich.prompt import Prompt
import subprocess
from pathlib import Path
import re


def dictionary_attack(self):
    """Optimized dictionary attack with wordlist"""
    if not self.selected_network and not Path("handshake").exists():
        self.console.print("[bold red]Please select a target network first![/]")
        return

    network = self.networks[self.selected_network] if self.selected_network else None
    
    # Check if network is WPA3
    is_wpa3 = False
    if network and 'security' in network:
        if isinstance(network['security'], str) and "WPA3" in network['security']:
            is_wpa3 = True
        elif isinstance(network['security'], list) and any("WPA3" in sec for sec in network['security']):
            is_wpa3 = True
    
    self.console.print("\n[bold yellow]Dictionary Attack:[/]")
    self.console.print("1. 📦 Use Handshake File")
    if is_wpa3:
        self.console.print("3. 🛡️ Use WPA3 SAE Hash")
    self.console.print("0. ↩️ Back")
    
    choice = Prompt.ask("Select an option")
    
    if choice == "0":
        return
    elif choice == "1":
        # Use Handshake File for dictionary attack
        handshake_dir = Path("handshake")
        if not handshake_dir.exists():
            self.console.print("[bold yellow]Creating handshake directory...[/]")
            handshake_dir.mkdir(exist_ok=True)
            self.console.print("[bold red]No handshake files found! Capture a handshake first.[/]")
            return
            
        # Check for existing handshake files
        handshake_files = list(handshake_dir.glob("*.cap"))
        if not handshake_files:
            self.console.print("[bold red]No handshake files found in 'handshake' directory![/]")
            return
            
        # List available handshake files
        self.console.print("\n[bold green]Available Handshake Files:[/]")
        for idx, file in enumerate(handshake_files, 1):
            # Check if file contains handshake
            result = subprocess.run(["aircrack-ng", str(file)], capture_output=True, text=True)
            status = "[green]✓ Valid" if "1 handshake" in result.stdout else "[red]✗ Invalid"
            self.console.print(f"{idx}. {file.name} - {status}")
            
        # Let user select handshake file
        file_choice = Prompt.ask("\nSelect handshake file (0 to cancel)", choices=["0"] + [str(i) for i in range(1, len(handshake_files) + 1)])
        if file_choice == "0":
            return
            
        selected_file = handshake_files[int(file_choice) - 1]
        
        # Verify selected file has handshake
        result = subprocess.run(["aircrack-ng", str(selected_file)], capture_output=True, text=True)
        if "1 handshake" not in result.stdout:
            self.console.print(f"[bold red]Selected file does not contain a valid handshake![/]")
            return
    
    # Continue with shared code for both options
    # Ask for wordlist
    self.console.print("\n[bold yellow]Select Wordlist:[/]")
    self.console.print("1. Use default wordlist (wordlists/10-million-password-list-top-1000000.txt)")
    self.console.print("2. Use rockyou wordlist (/usr/share/wordlists/rockyou.txt)")
    self.console.print("3. Specify custom wordlist path")
    wordlist_choice = Prompt.ask("Choose wordlist option", choices=["1", "2", "3"])
    
    if wordlist_choice == "1":
        wordlist = "wordlists/10-million-password-list-top-1000000.txt"
        if not os.path.exists(wordlist):
            self.console.print(f"[bold red]Default wordlist not found: {wordlist}[/]")
            return
    elif wordlist_choice == "2":
        wordlist = "/usr/share/wordlists/rockyou.txt"
        if not os.path.exists(wordlist):
            self.console.print(f"[bold red]Rockyou wordlist not found: {wordlist}[/]")
            return
    else:
        wordlist = Prompt.ask("Enter path to wordlist")
        if not os.path.exists(wordlist):
            self.console.print(f"[bold red]Wordlist not found: {wordlist}[/]")
            return
    
    # Start the cracking process with visual progress display
    self.console.print(f"\n[bold green]Starting dictionary attack against: {selected_file.name}[/]")
    self.console.print(f"[bold blue]Using wordlist: {wordlist}[/]")
    self.console.print("[bold yellow]This process may take some time. Press Ctrl+C to stop.[/]")
    
    start_time = time.time()
    password_found = False
    last_progress = 0
    last_speed = "0 k/s"
    last_tested_keys = 0
    total_keys = 0
    eta = "Unknown"
    current_key = ""
    process = None  # Define process here so we can access it in finally block
    
    # Create a function to update the status display
    def create_status_display():
        # Create a simple progress bar with just percent completion
        progress_percent = last_progress / 100
        filled_length = int(50 * progress_percent)
        empty_length = 50 - filled_length
        
        if progress_percent < 0.3:
            color = "bright_red"
        elif progress_percent < 0.6:
            color = "bright_yellow"
        elif progress_percent < 0.9:
            color = "bright_green"
        else:
            color = "bright_blue"
            
        # Only show progress bar, don't use panel
        progress_bar = f"[{color}]{'━' * filled_length}[/][dim]{'╍' * empty_length}[/] [bold {color}]{last_progress:.2f}%[/]"
        
        return progress_bar
    
    # Run aircrack-ng in real-time with output processing
    # Add -a 2 parameter to specify WPA/WPA2 attack mode
    # Add -q for quieter output (less verbose)
    # Add -e to specify the ESSID if known
    bssid = None
    essid = None
    is_wpa3 = False
    
    # Get network info from handshake if possible
    try:
        aircrack_check = subprocess.run(["aircrack-ng", str(selected_file)], 
                                        capture_output=True, text=True)
        
        # Parse aircrack-ng output line by line looking for network information
        lines = aircrack_check.stdout.splitlines()
        header_line_idx = -1
        
        # First find the header line with BSSID and ESSID
        for i, line in enumerate(lines):
            if "BSSID" in line and "ESSID" in line:
                header_line_idx = i
                break
        
        # If we found the header, check the next line(s) for actual data
        if header_line_idx >= 0 and header_line_idx + 1 < len(lines):
            for i in range(header_line_idx + 1, min(header_line_idx + 5, len(lines))):
                data_line = lines[i].strip()
                if data_line and not data_line.startswith("Choosing"):
                    # Line format is typically: BSSID              ESSID
                    parts = data_line.split(None, 1)  # Split on first whitespace
                    if len(parts) >= 2 and len(parts[0]) == 17:  # MAC address length
                        bssid = parts[0].strip()
                        essid = parts[1].strip()
                        
                        # Check if WPA3 by looking for WPA3 in output
                        if "WPA3" in aircrack_check.stdout:
                            is_wpa3 = True
                            self.console.print("[bold blue]WPA3 network detected[/]")
                        
                        self.logger.info(f"Extracted from handshake - BSSID: {bssid}, ESSID: {essid}, WPA3: {is_wpa3}")
                        break
    except Exception as e:
        self.logger.error(f"Error extracting network info: {str(e)}")
        
            # Construct command with all needed parameters
    if choice == "2":
        # For PMKID, we use hashcat mode 16800
        cmd = ["hashcat", "-m", "16800", "-a", "0", "-w", "3", "--force", str(selected_file), wordlist]
        self.console.print("[bold blue]Using hashcat for PMKID cracking (mode 16800)[/]")
    elif is_wpa3:
        # For WPA3, we use hashcat instead for better compatibility
        cmd = ["hashcat", "-m", "22000", "-a", "0", "-w", "3", "--force", str(selected_file), wordlist]
        self.console.print("[bold blue]Using hashcat for WPA3 handshake cracking[/]")
    else:
        # Standard WPA/WPA2 attack with aircrack-ng
        cmd = ["aircrack-ng", "-a", "2", "-w", wordlist]
        
        # Add ESSID if available - only if it looks valid
        if essid and essid != "ESSID" and len(essid) > 0 and "Encryption" not in essid:
            cmd.extend(["-e", essid])
            self.console.print(f"[bold blue]Using network ESSID: {essid}[/]")
            
        # Finally add handshake file
        cmd.append(str(selected_file))        
    try:
        # Add extra parameters to make output format more organized
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            text=True,
            bufsize=1
        )
        
        # Initialize Rich Live display before starting to read process output
        from rich.live import Live
        
        # Save all output for later analysis
        all_output = []
        output_lines = []
        
        with Live(create_status_display(), refresh_per_second=4) as live:
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line:  # Skip empty lines
                    all_output.append(line)
                    output_lines.append(line)
                    self.logger.debug(f"Aircrack output: {line}")
                
                # Extract progress information - using regex for more precise matching
                try:
                    # Find progress percentage
                    progress_match = re.search(r'(\d+\.\d+)%', line)
                    if progress_match:
                        last_progress = float(progress_match.group(1))
                    
                    # For hashcat, progress is displayed differently
                    if is_wpa3 and "Progress.....: " in line:
                        progress_parts = line.split("Progress.....: ")[1].split("%")[0].strip()
                        try:
                            last_progress = float(progress_parts)
                        except:
                            pass
                    
                    # Find tested keys count
                    keys_match = re.search(r'(\d+)/(\d+) keys tested', line)
                    if keys_match:
                        last_tested_keys = int(keys_match.group(1))
                        total_keys = int(keys_match.group(2))
                    
                    # For hashcat, speed is displayed differently
                    if is_wpa3 and "Speed.#1" in line:
                        speed_parts = line.split("Speed.#1.....: ")[1].strip()
                        last_speed = speed_parts
                    else:
                        # Find speed (k/s or M/s)
                        speed_match = re.search(r'(\d+[\.,]\d+ [kMG]?/s)', line)
                        if speed_match:
                            last_speed = speed_match.group(1)
                    
                    # Find ETA
                    eta_match = re.search(r'time left: ([^)]+)', line)
                    if eta_match:
                        eta = eta_match.group(1)
                    
                    # For hashcat, ETA is displayed differently
                    if is_wpa3 and "Time.Estimated..." in line:
                        eta_parts = line.split("Time.Estimated...: ")[1].strip()
                        eta = eta_parts
                    
                    # Check for direct password patterns
                    # Common patterns in aircrack-ng output
                    direct_key_patterns = [
                        r'KEY FOUND!\s*\[\s*([^\]]+)\s*\]',  # KEY FOUND! [ password ]
                        r'KEY FOUND:\s*\[\s*([^\]]+)\s*\]',   # KEY FOUND: [ password ]
                        r'The password is "([^"]+)"',         # The password is "password"
                        r'Password:\s*([^\s]+)',              # Password: password
                        r'FOUND KEY:\s*([^\s]+)'              # FOUND KEY: password
                    ]
                    
                    # Add hashcat specific patterns
                    if is_wpa3:
                        hashcat_patterns = [
                            r'Status\.+: Cracked',  # Look for success status
                            r'Hash\.Target\.+: (.+?):(.+?)$'  # Extract password from hash line
                        ]
                        direct_key_patterns.extend(hashcat_patterns)
                    
                    found_in_this_line = False
                    for pattern in direct_key_patterns:
                        match = re.search(pattern, line)
                        if match:
                            # For hashcat status pattern
                            if pattern == r'Status\.+: Cracked':
                                # Password will be extracted later
                                continue
                                
                                # For hashcat hash pattern
                                if pattern == r'Hash\.Target\.+: (.+?):(.+?)$' and len(match.groups()) >= 2:
                                    password_candidate = match.group(2).strip()
                                else:
                                    password_candidate = match.group(1).strip()
                                    
                                # Validate password (ignore status info)
                                if (password_candidate and 
                                    not any(x in password_candidate for x in ["second", "%", "Master", "KEY", "Decrypting"])):
                                    current_key = password_candidate
                                    password_found = True
                                    
                                    # Şifreyi konsola getirme işlemi burada tamamen devre dışı bırakılıyor
                                    # Sonuç tablosunda göstereceğiz
                                    
                                    self.logger.info(f"Password found for {network['ssid'] if network else selected_file.name}: {current_key}")
                                    process.terminate()
                                    found_in_this_line = True
                                    break
                    
                    if found_in_this_line:
                        break
                    
                    # Update the screen with every line
                    if len(line) > 0:
                        status_display = create_status_display()
                        live.update(status_display)
                    
                    # Show at least minimal progress while reading wordlist
                    if any(x in line.lower() for x in ["reading", "loaded"]) and last_progress < 0.1:
                        last_progress = 0.05
                    
                    # Update one more time when process finishes
                    if process.poll() is not None:
                        last_progress = 100.0  # Process completed
                        status_display = create_status_display()
                        live.update(status_display)
                        break
                except Exception as e:
                    self.logger.error(f"Error parsing aircrack output: {str(e)}")
        
        # Process has completed - check if we missed finding the password by analyzing full output
        if not password_found:
            # First, join all output into a single string for full-text analysis
            full_output = '\n'.join(all_output)
            
            # Look for various password patterns in the full output
            key_found_patterns = [
                r'KEY FOUND!\s*\[\s*([^\]]+)\s*\]',      # KEY FOUND! [ password ]
                r'KEY FOUND:\s*\[\s*([^\]]+)\s*\]',       # KEY FOUND: [ password ]
                r'The password is "([^"]+)"',             # The password is "password"
                r'Password:\s*([^\s]+)',                  # Password: password
                r'FOUND KEY:\s*([^\s]+)'                  # FOUND KEY: password
            ]
            
            # Add WPA3/hashcat specific pattern
            if is_wpa3:
                key_found_patterns.append(r'Hash\.Target\.+: (.+?):(.+?)$')
                
            for pattern in key_found_patterns:
                match = re.search(pattern, full_output)
                if match:
                    # For hashcat hash pattern
                    if pattern == r'Hash\.Target\.+: (.+?):(.+?)$' and len(match.groups()) >= 2:
                        password_candidate = match.group(2).strip()
                    else:
                        password_candidate = match.group(1).strip()
                        
                    if (password_candidate and 
                        not any(x in password_candidate for x in ["second", "%", "Master", "KEY", "Decrypting"])):
                        current_key = password_candidate
                        password_found = True
                        self.logger.info(f"Password found in output analysis: {current_key}")
                        break
            
            # If still not found, scan line by line
            if not password_found:
                # For other patterns
                secondary_patterns = [
                    r'([a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>/?]{8,63})'  # For typical WiFi passwords
                ]
                
                # Scan through all output to find key
                for i, line in enumerate(output_lines):
                    if "KEY FOUND" in line or "FOUND KEY" in line or "Cracked" in line:
                        # Check next few lines for key
                        for j in range(i, min(i+5, len(output_lines))):
                            next_line = output_lines[j]
                            
                            # Scan for common patterns in each line
                            colon_parts = next_line.split(":")
                            if len(colon_parts) >= 2 and not any(x in next_line for x in ["BSSID", "Index", "second", "%"]):
                                password_candidate = colon_parts[-1].strip()
                                if (password_candidate and 
                                    not any(x in password_candidate for x in ["second", "%", "Master", "KEY", "Decrypting"])):
                                    current_key = password_candidate
                                    password_found = True
                                    self.logger.info(f"Password found from line analysis: {current_key}")
                                    break
                        
                        if password_found:
                            break
                                
                # If nothing found, look for hex pattern with brackets (common aircrack output format)
                if not password_found:
                    bracket_matches = re.findall(r'\[\s*([a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>/?]{8,63})\s*\]', full_output)
                    for match in bracket_matches:
                        if not any(x in match for x in ["second", "%", "Master", "KEY", "Decrypting"]):
                            current_key = match
                            password_found = True
                            self.logger.info(f"Password found from bracket pattern: {current_key}")
                            break
        
        # Additional validation to prevent false positives
        if password_found:
            # Make sure the password is valid (contains only valid characters and length)
            # Check for common timing information that might be misinterpreted as password
            if (len(current_key) > 64 or
                len(current_key) < 8 or
                current_key.lower().startswith("master") or
                "second" in current_key.lower() or
                "minute" in current_key.lower() or
                "hour" in current_key.lower() or
                "progress" in current_key.lower() or
                "remaining" in current_key.lower() or
                "key" in current_key.lower() or
                "tested" in current_key.lower() or
                re.search(r'\d+\s*(?:second|minute|hour)', current_key, re.IGNORECASE) or
                re.search(r'\d+[:.]\d+[:.]\d+', current_key) or  # Matches time formats like 00:00:00
                re.search(r'\d+\.\d+%', current_key) or  # Matches percentage
                re.search(r'\[.*\d+[\.:]\d+.*\]', current_key)):  # Matches something with time in brackets
                self.logger.warning(f"Invalid password detected: {current_key} - marking as not found")
                password_found = False
                current_key = ""
        
        # Show detailed results in a table at the end of the process
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Results table
        result_table = Table(show_header=True, header_style="bold magenta", title="[bold blue]Dictionary Attack Results[/]")
        result_table.add_column("Target", style="cyan")
        result_table.add_column("Status", style="green")
        result_table.add_column("Tested Keys", style="yellow")
        result_table.add_column("Speed", style="magenta")
        result_table.add_column("Time", style="blue")
        result_table.add_column("Password", style="red")
        
        if password_found and current_key and len(current_key) >= 8 and len(current_key) <= 63:
            status = "[bold green]✓ CRACKED[/]"
            password_display = f"[bold red]{current_key}[/]"
        else:
            status = "[bold red]✗ FAILED[/]"
            password_display = "[dim]Not Found[/dim]"
            # Reset these in case there was a false positive
            password_found = False
            current_key = ""
        
        result_table.add_row(
            str(selected_file.name),
            status,
            str(last_tested_keys),
            last_speed,
            elapsed_str,
            password_display
        )
        
        self.console.print("\n")
        self.console.print(result_table)
        
        if not password_found:
            self.logger.warning(f"Failed to crack password for {selected_file}")
            
    except KeyboardInterrupt:
        self.console.print("\n[bold yellow]Dictionary attack interrupted by user[/]")
        self.logger.info("Dictionary attack interrupted by user")
    except Exception as e:
        self.console.print(f"\n[bold red]Error during dictionary attack: {str(e)}[/]")
        self.logger.error(f"Error during dictionary attack: {str(e)}")
    finally:
        # Always clean up processes
        if process:
            try:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    try:
                        process.wait(timeout=2)
                    except:
                        pass
            except:
                pass
        
        # Also make sure to kill any remaining aircrack-ng or hashcat processes
        try:
            if is_wpa3:
                subprocess.run(["pkill", "-9", "-f", "hashcat"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-9", "-f", "aircrack-ng"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass