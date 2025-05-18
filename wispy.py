#!/usr/bin/env python3
"""
WiSpy - Wireless Network Security Analysis Tool
"""

import sys
import os
import shutil
import time
import platform as system_platform
import gc
from scapy.all import *
from rich.console import Console, Group
from rich.table import Table
from rich.prompt import Prompt
from rich.layout import Layout
from rich.live import Live
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import subprocess
from pathlib import Path
import shutil
import concurrent.futures
from utils.logger import Logger # logger module

def check_root():
    if os.geteuid() != 0:
        print("[bold red]❌ Root privileges are required to run this application!")
        print("[yellow]Please run with 'sudo'.[/]")
        sys.exit(1)

def check_os():
    os_name = system_platform.system().lower()
    if os_name != "linux":
        print(f"[bold red]❌ This application only runs on Linux operating systems!")
        print(f"[yellow]Detected operating system: {system_platform.system()}[/]")
        sys.exit(1)
    
    try:
        with open("/etc/os-release") as f:
            os_info = f.read()
            if "kali" not in os_info.lower() and "debian" not in os_info.lower() and "ubuntu" not in os_info.lower():
                print("[bold yellow]⚠️ Warning: This application has been tested on Kali Linux.")
                print("Unexpected issues may occur on other Linux distributions.[/]")
    except:
        pass

def check_required_packages():
    required_packages = {
        'aircrack-ng': ['aircrack-ng', 'airodump-ng', 'aireplay-ng'],
        'hashcat': ['hashcat'],
        'hcxdumptool': ['hcxdumptool'],
        'hostapd': ['hostapd'],
        'dnsmasq': ['dnsmasq'],
        'macchanger': ['macchanger'],
        'reaver': ['reaver'],
        'python3-scapy': ['scapy']
    }
    
    missing_packages = []
    
    for package, commands in required_packages.items():
        for cmd in commands:
            if shutil.which(cmd) is None:
                missing_packages.append(package)
                break
    
    if missing_packages:
        print("[bold red]❌ Missing packages:[/]")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        
        print("\n[yellow]To install missing packages:[/]")
        print(f"[white]sudo apt update && sudo apt install -y {' '.join(missing_packages)}[/]")
        sys.exit(1)

def main():
    console = Console()
    
    check_root()
    check_os()
    check_required_packages()
    
    wifi_spy = WiSpy()
    wifi_spy.run()

class WiSpy:

    # show main menu
    from utils.show_menu import show_main_menu, show_attack_menu, show_tools_menu, show_deauth_menu

    # wifi adaptor setting
    from utils.interface_handler import wifi_adapter_settings, change_adapter_mode, change_channel, show_adapter_info, start_monitor_mode


    # attack module

    from attacks.dictionary_attack import dictionary_attack
        # evil twin and cleanup
    from attacks.evil_twin import evil_twin_attack, cleanup_evil_twin
        # capture handshake
    from attacks.handshake_capture import capture_handshake
        # deauth all clients
    from attacks.deauther import deauth_all_clients, deauth_single_client
        # security audit
    from audit.security_audit import security_audit

    def __init__(self):
        if os.geteuid() != 0:
            print("[bold red]❌ Root privileges are required to run WiFiAngel.[/]")
            sys.exit(1)

        self.console = Console()
        self.networks = {}
        self.clients = {}
        self.interface_name = None
        self.selected_network = None
        self.scanning = False
        self.current_menu = "main"
        self.layout = Layout()
        self.live = Live("", console=self.console, auto_refresh=False)
        self.logger = Logger()
        
        banner = """[bold blue]
╔════════════════════════════════════════════════════════════════╗
║                                                              
║   [bold red]🛡️  WiSpy 2025[/]   [bold yellow]📶 Wireless Network Analysis Tool[/]      
║                                                              
║   [green]Secure  •  Analyze  •  Defend[/]                               
║                                                              
║   [cyan]https://github.com/yourrepo/wispy[/]                        
║                                                              
╠════════════════════════════════════════════════════════════════╣
║   [white]Scan | Audit | Attack | Protect | Learn | Evolve[/]            
╚════════════════════════════════════════════════════════════════╝

"""
        self.console.print(banner)
        
        try:
            required_tools = ['airmon-ng', 'airodump-ng', 'aireplay-ng', 'hashcat', 'hcxdumptool']
            missing_tools = []
            
            for tool in required_tools:
                if shutil.which(tool) is None:
                    missing_tools.append(tool)
            
            if missing_tools:
                self.console.print(f"[bold red]❌ Missing required tools: {', '.join(missing_tools)}[/]")
                self.console.print("[yellow]Please install the missing tools using:[/]")
                self.console.print("[white]sudo apt install aircrack-ng hashcat hcxdumptool[/]")
                sys.exit(1)

            interfaces = subprocess.check_output(["iwconfig"], stderr=subprocess.STDOUT).decode()
            wifi_interfaces = []
            
            for line in interfaces.split('\n'):
                if "IEEE 802.11" in line:
                    wifi_interfaces.append(line.split()[0])
            
            if not wifi_interfaces:
                raise Exception("❌ No wireless network adapter found!")
            
            if len(wifi_interfaces) > 1:
                self.console.print("\n[yellow]Multiple wireless interfaces found:[/]")
                for i, iface in enumerate(wifi_interfaces, 1):
                    self.console.print(f"{i}. {iface}")
                choice = Prompt.ask("Select interface number", choices=[str(i) for i in range(1, len(wifi_interfaces)+1)])
                self.interface_name = wifi_interfaces[int(choice)-1]
            else:
                self.interface_name = wifi_interfaces[0]
                
            self.console.print(f"[bold green]✓ WiFi adapter initialized successfully: {self.interface_name}[/]")
            self.logger.info(f"WiFi adapter initialized: {self.interface_name}")
            
        except Exception as e:
            self.logger.error(f"Could not initialize WiFi adapter: {str(e)}")
            self.console.print(f"[bold red]❌ Could not initialize WiFi adapter: {str(e)}[/]")
            sys.exit(1)

    def _packet_sniffer(self):
        while self.scanning:
            try:
                sniff(iface=self.interface_name, 
                     prn=self.packet_handler, 
                     store=0,
                     timeout=0.3,
                     count=150)
            except Exception as e:
                if self.scanning:
                    self.logger.error(f"Sniffing error: {str(e)}")
                time.sleep(0.1)

    def _results_updater(self):
        while self.scanning:
            try:
                if self.networks:
                    self.print_results()
                time.sleep(0.3)
            except Exception as e:
                self.logger.error(f"Results update error: {str(e)}")
                time.sleep(0.1)

    def scan_networks(self):
        self.logger.info("Starting network scan")
        self.live.start()
        
        if not hasattr(self, '_networks_lock'):
            self._networks_lock = threading.Lock()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            futures.append(executor.submit(self._packet_sniffer))
            futures.append(executor.submit(self._results_updater))
            
            try:
                while self.scanning:
                    time.sleep(0.1)
                    for future in futures:
                        if future.done() and future.exception():
                            self.logger.error(f"Scan thread error: {future.exception()}")
                            self.scanning = False
                            break
            except KeyboardInterrupt:
                self.scanning = False
                self.console.print("\n[bold yellow]Stopping network scan...[/]")
            finally:
                self.live.stop()
                for future in futures:
                    try:
                        future.result(timeout=1.0)
                    except:
                        pass
                self.logger.info("Network scan stopped")
                gc.collect()

    def packet_handler(self, pkt):
        try:
            if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
                bssid = pkt[Dot11].addr3
                
                try:
                    if pkt.haslayer(Dot11Elt) and pkt[Dot11Elt].ID == 0:
                        ssid = pkt[Dot11Elt].info.decode('utf-8', errors='ignore')
                    else:
                        ssid = "<Hidden Network>"
                except:
                    ssid = "<Hidden Network>"
                
                try:
                    channel = int(ord(pkt[Dot11Elt:3].info))
                except:
                    channel = 0
                
                try:
                    if pkt.haslayer(RadioTap) and hasattr(pkt[RadioTap], 'dBm_AntSignal'):
                        signal = pkt[RadioTap].dBm_AntSignal
                    else:
                        signal = -100
                except Exception:
                    signal = -100
                
                security = self._get_security_info(pkt)
                
                wps = self._check_wps(pkt)
                
                with self._networks_lock:
                    if bssid not in self.networks:
                        self.networks[bssid] = {
                            'ssid': ssid,
                            'signal': signal,
                            'cipher': "/".join(security),
                            'clients': set(),
                            'channel': channel,
                            'first_seen': datetime.now(),
                            'last_seen': datetime.now(),
                            'packets': 1,
                            'data_packets': 0,
                            'wps': wps
                        }
                        self.logger.debug(f"New network found: {ssid} ({bssid})")
                    else:
                        self.networks[bssid].update({
                            'last_seen': datetime.now(),
                            'signal': signal,
                            'packets': self.networks[bssid]['packets'] + 1
                        })
            
            elif pkt.haslayer(Dot11) and pkt.type == 2:
                bssid = pkt[Dot11].addr3
                with self._networks_lock:
                    if bssid in self.networks:
                        self.networks[bssid]['data_packets'] += 1
                        
                        src = pkt[Dot11].addr2
                        dst = pkt[Dot11].addr1
                        
                        if src and src != bssid and src not in self.networks[bssid]['clients']:
                            self.networks[bssid]['clients'].add(src)
                            self.logger.debug(f"New client found: {src} -> {self.networks[bssid]['ssid']}")
                        
                        if dst and dst != bssid and dst not in self.networks[bssid]['clients']:
                            self.networks[bssid]['clients'].add(dst)
                            self.logger.debug(f"New client found: {dst} -> {self.networks[bssid]['ssid']}")
                        
        except Exception as e:
            self.logger.error(f"Packet processing error: {str(e)}")

    def _get_security_info(self, pkt):
        security = []
        cap = pkt[Dot11Beacon].cap if pkt.haslayer(Dot11Beacon) else pkt[Dot11ProbeResp].cap
        
        if cap.privacy:
            elt = pkt[Dot11Elt]
            while isinstance(elt, Dot11Elt):
                if elt.ID == 48:
                    security.append("WPA2")
                    
                    rsn_info = elt.info
                    if len(rsn_info) >= 8:
                        auth_key_count = rsn_info[7]
                        if auth_key_count > 0 and len(rsn_info) >= 8 + 4*auth_key_count:
                            for i in range(auth_key_count):
                                auth_suite = rsn_info[8+4*i:12+4*i]
                                if auth_suite[3] == 8:
                                    security.append("WPA3")
                                    break
                                    
                elif elt.ID == 221 and elt.info.startswith(b'\x00P\xf2\x01\x01\x00'):
                    security.append("WPA")
                elif elt.ID == 221 and elt.info.startswith(b'\x50\x6f\x9a\x1c'):
                    security.append("WPA3")
                elt = elt.payload
            if not security:
                security.append("WEP")
        else:
            security.append("OPEN")
        
        return security

    def _check_wps(self, pkt):
        try:
            elt = pkt[Dot11Elt]
            while isinstance(elt, Dot11Elt):
                if elt.ID == 221 and elt.info.startswith(b'\x00P\xf2\x04'):
                    return True
                elt = elt.payload
            return False
        except:
            return False

    def get_security(self, pkt):
        """Determines security type"""
        cap = pkt[Dot11Beacon].cap
        security = []
        
        if cap.privacy:
            elt = pkt[Dot11Elt]
            while isinstance(elt, Dot11Elt):
                if elt.ID == 48:  # RSN
                    security.append("WPA2")
                    
                    # Check for WPA3 (SAE authentication in RSN)
                    rsn_info = elt.info
                    if len(rsn_info) >= 8:
                        auth_key_count = rsn_info[7]
                        if auth_key_count > 0 and len(rsn_info) >= 8 + 4*auth_key_count:
                            # Check for SAE (Suite type 00-0F-AC:8)
                            for i in range(auth_key_count):
                                auth_suite = rsn_info[8+4*i:12+4*i]
                                if auth_suite[3] == 8:  # SAE authentication method
                                    security.append("WPA3")
                                    break
                                    
                elif elt.ID == 221 and elt.info.startswith(b'\x00P\xf2\x01\x01\x00'):
                    security.append("WPA")
                elif elt.ID == 221 and elt.info.startswith(b'\x50\x6f\x9a\x1c'):
                    security.append("WPA3")
                elt = elt.payload
            if not security:
                security.append("WEP")
        else:
            security.append("Open")
        
        return "/".join(security)

    def print_results(self):
        """Shows results in table format"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No")
        table.add_column("BSSID")
        table.add_column("SSID")
        table.add_column("Channel")
        table.add_column("Security")
        table.add_column("Signal")
        table.add_column("Clients")

        for idx, (bssid, data) in enumerate(self.networks.items(), 1):
            table.add_row(
                str(idx),
                bssid,
                data['ssid'],
                str(data['channel']),
                data['cipher'],
                str(data['signal']),
                str(len(data['clients']))
            )

        # Update Live display
        self.live.update(table)
        self.live.refresh()

    def signal_analyzer(self):
        """Analyzes WiFi signal strength and quality in real time using live packet data."""
        if not self.selected_network:
            self.console.print("[bold red]Please select a target network first![/]")
            return

        bssid = self.selected_network
        network = self.networks[bssid]
        signal_data = []

        def create_signal_table():
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Time", style="cyan")
            table.add_column("Signal Strength (dBm)", style="green")
            table.add_column("Quality", style="yellow")
            table.add_column("Interference", style="red")

            for data in signal_data[-10:]:  # Show last 10 measurements
                quality = "Excellent" if data[1] > -50 else "Good" if data[1] > -60 else "Fair" if data[1] > -70 else "Poor"
                table.add_row(
                    data[0],
                    str(data[1]),
                    quality,
                    data[2]
                )
            return table

        stop_event = threading.Event()

        def live_signal_sniffer():
            """Sniffs packets and updates signal strength for the selected BSSID."""
            try:
                def pkt_handler(pkt):
                    if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
                        if pkt[Dot11].addr3 == bssid:
                            try:
                                if pkt.haslayer(RadioTap) and hasattr(pkt[RadioTap], 'dBm_AntSignal'):
                                    signal = pkt[RadioTap].dBm_AntSignal
                                else:
                                    signal = -100
                            except Exception:
                                signal = -100
                            with self._networks_lock:
                                self.networks[bssid]['signal'] = signal
                while not stop_event.is_set():
                    sniff(
                        iface=self.interface_name,
                        prn=pkt_handler,
                        store=0,
                        timeout=0.5,
                        count=20,
                        stop_filter=lambda x: stop_event.is_set()
                    )
            except Exception as e:
                self.logger.error(f"Signal analyzer sniffer error: {str(e)}")

        try:
            # Start background sniffer thread for live signal updates
            sniffer_thread = threading.Thread(target=live_signal_sniffer, daemon=True)
            sniffer_thread.start()

            with Live(create_signal_table(), refresh_per_second=2) as live:
                while not stop_event.is_set():
                    current_time = datetime.now().strftime("%H:%M:%S")
                    with self._networks_lock:
                        signal_strength = self.networks[bssid]['signal']
                    # Check for interference
                    interference = "Low"
                    for other_bssid, other_net in self.networks.items():
                        if other_bssid != bssid and abs(other_net['channel'] - network['channel']) <= 1:
                            interference = "High"
                            break
                    signal_data.append((current_time, signal_strength, interference))
                    live.update(create_signal_table())
                    time.sleep(0.5)
        except KeyboardInterrupt:
            stop_event.set()
            self.console.print("\n[bold yellow]Signal analysis stopped.[/]")
        finally:
            stop_event.set()

    

    def select_target_network(self):
        """Allows user to select a target network"""
        if not self.networks:
            self.console.print("[bold red]❌ No networks found. Please scan first![/]")
            return

        # Create network selection table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No", style="cyan", justify="center")
        table.add_column("BSSID", style="green")
        table.add_column("SSID", style="yellow")
        table.add_column("Channel", style="blue", justify="center")
        table.add_column("Signal", style="magenta", justify="center")
        table.add_column("Security", style="red")
        table.add_column("Clients", style="cyan", justify="center")

        # Add networks to table
        for idx, (bssid, network) in enumerate(self.networks.items(), 1):
            table.add_row(
                str(idx),
                bssid,
                network['ssid'],
                str(network['channel']),
                str(network['signal']),
                network['cipher'],
                str(len(network['clients']))
            )

        self.console.print(table)
        self.console.print("\n[bold yellow]Select target network (0 to cancel):[/]")

        try:
            choice = int(Prompt.ask("Enter network number"))
            if choice == 0:
                return
            
            if 1 <= choice <= len(self.networks):
                self.selected_network = list(self.networks.keys())[choice - 1]
                network = self.networks[self.selected_network]
                self.console.print(f"\n[bold green]✓ Selected network: {network['ssid']} ({self.selected_network})[/]")
                self.logger.info(f"Selected target network: {network['ssid']} ({self.selected_network})")
            else:
                self.console.print("[bold red]❌ Invalid network number![/]")
        except ValueError:
            self.console.print("[bold red]❌ Invalid input![/]")

    def cleanup_and_exit(self):
        """Performs cleanup before exiting"""
        self.scanning = False
        self.console.print("[bold yellow]Performing cleanup...[/]")
        self.logger.info("Cleanup process started")
        
        try:
            # Close monitor mode
            subprocess.run(["airmon-ng", "stop", self.interface_name], stdout=subprocess.PIPE)

            # get original interface name
            if "mon" in self.interface_name:
                self.interface_name = self.interface_name.replace("mon", "")

            # Switch to managed mode
            subprocess.run(["ip", "link", "set", self.interface_name, "down"], stdout=subprocess.PIPE)
            subprocess.run(["iw", self.interface_name, "set", "type", "managed"], stdout=subprocess.PIPE)
            subprocess.run(["ip", "link", "set", self.interface_name, "up"], stdout=subprocess.PIPE)

            self.logger.info(f"{self.interface_name} switched to managed mode")
            time.sleep(1)
            
            # Start NetworkManager
            subprocess.run(["systemctl", "restart", "NetworkManager"], stdout=subprocess.PIPE)
            self.logger.info("NetworkManager started")
            
            self.console.print("[bold green]Cleanup completed.[/]")
            self.logger.info("Cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            self.console.print(f"[bold red]Error during cleanup: {str(e)}[/]")
        
        sys.exit(0)

    def run(self):
        """Main program loop"""
        try:
            while True:
                try:
                    self.show_main_menu()
                except KeyboardInterrupt:
                    if self.current_menu == "main":
                        self.logger.info("Program shutting down...")
                        self.cleanup_and_exit()
                    else:
                        self.logger.info("Returning to main menu")
                        self.console.print("\n[bold yellow]Returning to main menu...[/]")
                        self.current_menu = "main"
                        continue
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            self.cleanup_and_exit()

    def show_network_stats(self):
        """Shows detailed network statistics"""
        if not self.networks:
            self.console.print("[bold red]No networks found. Please scan first![/]")
            return

        table = Table(show_header=True, header_style="bold magenta", title="[bold blue]Network Statistics[/]")
        table.add_column("Network", style="cyan")
        table.add_column("Channel", style="green")
        table.add_column("Security", style="yellow")
        table.add_column("Signal", style="blue")
        table.add_column("Clients", style="magenta")
        table.add_column("Data Packets", style="cyan")
        table.add_column("First Seen", style="green")
        table.add_column("Last Seen", style="yellow")

        for bssid, network in self.networks.items():
            table.add_row(
                network['ssid'],
                str(network['channel']),
                network['cipher'],
                str(network['signal']),
                str(len(network['clients'])),
                str(network['data_packets']),
                network['first_seen'].strftime("%H:%M:%S"),
                network['last_seen'].strftime("%H:%M:%S")
            )

        self.console.print(table)

    def client_analysis(self):
        """Analyzes connected clients"""
        if not self.networks:
            self.console.print("[bold red]No networks found. Please scan first![/]")
            return

        table = Table(show_header=True, header_style="bold magenta", title="[bold blue]Client Analysis[/]")
        table.add_column("Client MAC", style="cyan")
        table.add_column("Connected To", style="green")
        table.add_column("Network Security", style="yellow")
        table.add_column("Data Packets", style="blue")

        for bssid, network in self.networks.items():
            for client in network['clients']:
                table.add_row(
                    client,
                    network['ssid'],
                    network['cipher'],
                    str(network['data_packets'])
                )

        self.console.print(table)

    def verify_network_services(self):
        """Verify that network services are running correctly"""
        try:
            # Check NetworkManager status with timeout
            try:
                nm_status = subprocess.run(["systemctl", "is-active", "NetworkManager"], 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5).stdout.decode().strip()
                if nm_status != "active":
                    self.console.print("[bold yellow]⚠️ NetworkManager is not active, attempting to restart...[/]")
                    try:
                        subprocess.run(["systemctl", "restart", "NetworkManager"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                        # Verify restart was successful
                        time.sleep(2)
                        nm_status = subprocess.run(["systemctl", "is-active", "NetworkManager"], 
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5).stdout.decode().strip()
                        if nm_status != "active":
                            self.console.print("[bold red]⚠️ Failed to restart NetworkManager[/]")
                    except subprocess.TimeoutExpired:
                        self.console.print("[bold red]⚠️ NetworkManager restart timed out[/]")
                    except Exception as e:
                        self.console.print(f"[bold red]⚠️ Error restarting NetworkManager: {str(e)}[/]")
            except subprocess.TimeoutExpired:
                self.console.print("[bold red]⚠️ NetworkManager status check timed out[/]")
            except Exception as e:
                self.console.print(f"[bold red]⚠️ Error checking NetworkManager: {str(e)}[/]")
            
            # Check wpa_supplicant status with timeout
            try:
                wpa_status = subprocess.run(["systemctl", "is-active", "wpa_supplicant"], 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5).stdout.decode().strip()
                if wpa_status != "active":
                    self.console.print("[bold yellow]⚠️ wpa_supplicant is not active, attempting to restart...[/]")
                    try:
                        subprocess.run(["systemctl", "restart", "wpa_supplicant"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                        # Verify restart was successful
                        time.sleep(2)
                        wpa_status = subprocess.run(["systemctl", "is-active", "wpa_supplicant"], 
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5).stdout.decode().strip()
                        if wpa_status != "active":
                            self.console.print("[bold red]⚠️ Failed to restart wpa_supplicant[/]")
                    except subprocess.TimeoutExpired:
                        self.console.print("[bold red]⚠️ wpa_supplicant restart timed out[/]")
                    except Exception as e:
                        self.console.print(f"[bold red]⚠️ Error restarting wpa_supplicant: {str(e)}[/]")
            except subprocess.TimeoutExpired:
                self.console.print("[bold red]⚠️ wpa_supplicant status check timed out[/]")
            except Exception as e:
                self.console.print(f"[bold red]⚠️ Error checking wpa_supplicant: {str(e)}[/]")
            
            # Verify interface mode with improved error handling
            try:
                iw_info = subprocess.check_output(["iwconfig", self.interface_name], stderr=subprocess.STDOUT, timeout=5).decode()
                if "Mode:Managed" not in iw_info:
                    self.console.print("[bold yellow]⚠️ Interface not in managed mode, attempting to fix...[/]")
                    try:
                        subprocess.run(["ip", "link", "set", self.interface_name, "down"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                        subprocess.run(["iw", self.interface_name, "set", "type", "managed"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                        subprocess.run(["ip", "link", "set", self.interface_name, "up"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                        
                        # Verify change was successful
                        time.sleep(2)
                        iw_info = subprocess.check_output(["iwconfig", self.interface_name], stderr=subprocess.STDOUT, timeout=5).decode()
                        if "Mode:Managed" not in iw_info:
                            self.console.print("[bold red]⚠️ Failed to set interface to managed mode[/]")
                    except subprocess.TimeoutExpired:
                        self.console.print("[bold red]⚠️ Interface mode change timed out[/]")
                    except Exception as e:
                        self.console.print(f"[bold red]⚠️ Error changing interface mode: {str(e)}[/]")
            except subprocess.TimeoutExpired:
                self.console.print("[bold red]⚠️ Interface check timed out[/]")
            except Exception as e:
                self.console.print(f"[bold red]⚠️ Could not verify interface mode: {str(e)}[/]")
            
        except Exception as e:
            self.logger.error(f"Error during network service verification: {str(e)}")
            self.console.print("[bold red]⚠️ Could not verify network services status[/]")

    def hidden_ssid_discovery(self):
        """Discovers hidden SSIDs in all available frequencies"""
        # Variables to track the original state
        original_interface = self.interface_name
        was_in_monitor_mode = self.interface_name.endswith("mon")
        
        # Check if monitor mode is active, if not switch to it
        if not was_in_monitor_mode:
            self.console.print("[bold blue]Interface is not in monitor mode, switching to monitor mode...[/]")
            if not self.start_monitor_mode():
                self.console.print("[bold red]Failed to enable monitor mode! Aborting.[/]")
                return
            self.console.print(f"[bold green]Successfully switched to monitor mode: {self.interface_name}[/]")

        hidden_networks = {}
        scanning = True
        stop_event = threading.Event()
        
        # Start time for tracking duration
        start_time = time.time()
        
        # Create header information and warning message
        self.console.print("[bold blue]Starting Hidden SSID Discovery...[/]")
        self.console.print("[bold red]⚠️ Press Ctrl+C at any time to stop the scanning process! ⚠️[/]")
        self.console.print("[bold yellow]Scanning for hidden networks and waiting for probe requests...[/]")

        def create_status_table():
            table = Table(show_header=True, header_style="bold magenta", title="[bold blue]Hidden SSID Discovery[/]")
            table.add_column("BSSID", style="cyan")
            table.add_column("Channel", style="green")
            table.add_column("Signal", style="blue")
            table.add_column("Clients", style="magenta")
            table.add_column("Encryption", style="red")
            table.add_column("Probes", style="yellow")
            
            for bssid, data in hidden_networks.items():
                probes_text = "\n".join(data['probes'][-3:]) if data['probes'] else "No probes yet"
                table.add_row(
                    bssid,
                    str(data['channel']),
                    f"{data['signal']} dBm",
                    str(len(data['clients'])),
                    data['encryption'],
                    probes_text
                )
            
            return table

        def packet_handler(pkt):
            # This function should not return anything
            if stop_event.is_set():
                return

            try:
                if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
                    bssid = pkt[Dot11].addr3
                    
                    # Check if SSID is hidden
                    if pkt.haslayer(Dot11Elt) and pkt[Dot11Elt].ID == 0:
                        ssid = pkt[Dot11Elt].info.decode('utf-8', errors='ignore')
                        if not ssid:  # Empty SSID indicates hidden network
                            # Get channel
                            try:
                                channel = int(ord(pkt[Dot11Elt:3].info))
                            except:
                                channel = 0
                            
                            # Get frequency
                            if channel >= 1 and channel <= 14:
                                frequency = 2407 + (channel * 5)
                            else:
                                frequency = 5000 + (channel * 5)
                            
                            # Get signal strength
                            try:
                                if pkt.haslayer(RadioTap) and hasattr(pkt[RadioTap], 'dBm_AntSignal'):
                                    signal = pkt[RadioTap].dBm_AntSignal
                                else:
                                    signal = -100
                            except Exception:
                                signal = -100
                            
                            # Get encryption
                            encryption = self.get_security(pkt)
                            
                            current_time = datetime.now()
                            
                            if bssid not in hidden_networks:
                                hidden_networks[bssid] = {
                                    'channel': channel,
                                    'frequency': frequency,
                                    'signal': signal,
                                    'encryption': encryption,
                                    'clients': set(),
                                    'probes': [],
                                    'first_seen': current_time,
                                    'last_seen': current_time
                                }
                            else:
                                hidden_networks[bssid].update({
                                    'signal': signal,
                                    'last_seen': current_time
                                })
                
                # Process probe requests for hidden networks only
                elif pkt.haslayer(Dot11ProbeReq):
                    client_mac = pkt[Dot11].addr2
                    if pkt.haslayer(Dot11Elt) and pkt[Dot11Elt].ID == 0:
                        probe_ssid = pkt[Dot11Elt].info.decode('utf-8', errors='ignore')
                        if probe_ssid:  # Non-empty probe request
                            for network in hidden_networks.values():
                                if probe_ssid not in network['probes']:
                                    network['probes'].append(probe_ssid)
                
                # Process data frames for client detection (only for hidden networks)
                elif pkt.haslayer(Dot11) and pkt.type == 2:
                    bssid = pkt[Dot11].addr3
                    if bssid in hidden_networks:
                        src = pkt[Dot11].addr2
                        dst = pkt[Dot11].addr1
                        
                        if src and src != bssid:
                            hidden_networks[bssid]['clients'].add(src)
                        if dst and dst != bssid:
                            hidden_networks[bssid]['clients'].add(dst)
            
            except Exception as e:
                self.logger.error(f"Error processing packet: {str(e)}")
            
            # This function should not return anything
            return

        # Create a separate stop function
        def should_stop(pkt):
            return stop_event.is_set()

        def channel_hopper():
            while not stop_event.is_set():
                for channel in range(1, 15):  # 2.4 GHz channels
                    if stop_event.is_set():
                        break
                    try:
                        subprocess.run(["iwconfig", self.interface_name, "channel", str(channel)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(0.5)
                    except:
                        pass

        try:
            # Start channel hopping thread
            hopper_thread = threading.Thread(target=channel_hopper)
            hopper_thread.daemon = True
            hopper_thread.start()

            # Use a simple manual refresh approach instead of Live for better compatibility
            while not stop_event.is_set():
                try:
                    # Display current scan information
                    elapsed = int(time.time() - start_time)
                    minutes = elapsed // 60
                    seconds = elapsed % 60
                    duration = f"{minutes:02d}:{seconds:02d}"
                    
                    # Clear screen and show updated information
                    os.system('clear' if os.name != 'nt' else 'cls')
                    
                    # Create status header
                    header = f"[bold blue]Hidden SSID Discovery - Duration: {duration}[/]"
                    self.console.print(header)
                    self.console.print(f"[bold yellow]Found {len(hidden_networks)} hidden networks[/]")
                    self.console.print("[bold red]Press Ctrl+C to stop scanning and return to main menu[/]")
                    
                    # Display network information if any found
                    if hidden_networks:
                        self.console.print(create_status_table())
                    else:
                        self.console.print("[bold yellow]Scanning for hidden networks... Please wait.[/]")
                    
                    # Perform packet sniffing for a short time
                    try:
                        sniff(iface=self.interface_name, 
                            prn=packet_handler,  # Packet processing function
                            store=0,
                            stop_filter=should_stop,  # Separate function for stop condition check
                            timeout=1)  # Short timeout for responsive updates
                    except KeyboardInterrupt:
                        self.console.print("\n[bold yellow]Stopping Hidden SSID discovery (Ctrl+C pressed)...[/]")
                        stop_event.set()
                        break
                    except Exception as e:
                        if not stop_event.is_set():
                            self.logger.error(f"Sniffing error: {str(e)}")
                        time.sleep(0.1)
                
                except KeyboardInterrupt:
                    self.console.print("\n[bold yellow]Stopping Hidden SSID discovery (Ctrl+C pressed)...[/]")
                    stop_event.set()
                    break
                
                # Biraz CPU rahatlatma
                time.sleep(0.2)
                
        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Stopping Hidden SSID discovery (Ctrl+C pressed)...[/]")
            stop_event.set()
            
        finally:
            # Clean up
            stop_event.set()
            if 'hopper_thread' in locals():
                hopper_thread.join(timeout=1.0)
            
            # Show final results if any hidden networks were found
            if hidden_networks:
                self.console.print("\n[bold green]Hidden Networks Found:[/]")
                
                # Create a more detailed final result table
                final_table = Table(show_header=True, header_style="bold magenta", title="[bold blue]Hidden Network Discovery Results[/]")
                final_table.add_column("BSSID", style="cyan")
                final_table.add_column("Channel", style="green")
                final_table.add_column("Signal", style="blue")
                final_table.add_column("Encryption", style="red")
                final_table.add_column("Discovered SSIDs", style="yellow")
                final_table.add_column("Connected Clients", style="magenta")
                
                for bssid, data in hidden_networks.items():
                    probes_text = "\n".join(data['probes']) if data['probes'] else "No SSIDs discovered"
                    clients_text = "\n".join(list(data['clients'])[:5]) if data['clients'] else "None detected"
                    
                    if len(data['clients']) > 5:
                        clients_text += f"\n... and {len(data['clients']) - 5} more"
                    
                    final_table.add_row(
                        bssid,
                        str(data['channel']),
                        f"{data['signal']} dBm",
                        data['encryption'],
                        probes_text,
                        clients_text
                    )
                
                self.console.print(final_table)
                
                # Display a summary of the scan
                total_duration = int(time.time() - start_time)
                minutes = total_duration // 60
                seconds = total_duration % 60
                
                self.console.print(f"\n[bold green]Scan completed in {minutes:02d}:{seconds:02d}[/]")
                self.console.print(f"[bold green]Found {len(hidden_networks)} hidden networks[/]")
                total_probes = sum(len(data['probes']) for data in hidden_networks.values())
                self.console.print(f"[bold green]Discovered {total_probes} potential SSIDs through probe requests[/]")
            else:
                self.console.print("\n[bold yellow]No hidden networks discovered.[/]")
            
            # Switch back to managed mode if we were not in monitor mode before
            if not was_in_monitor_mode:
                self.console.print("\n[bold blue]Switching back to managed mode...[/]")
                try:
                    # Disable monitor mode
                    subprocess.run(["airmon-ng", "stop", self.interface_name], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Get original interface name (remove "mon" suffix if present)
                    if self.interface_name.endswith("mon"):
                        self.interface_name = self.interface_name[:-3]
                    
                    # Make sure interface is in managed mode
                    subprocess.run(["ip", "link", "set", self.interface_name, "down"], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(["iw", self.interface_name, "set", "type", "managed"], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(["ip", "link", "set", self.interface_name, "up"], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Restart NetworkManager
                    subprocess.run(["systemctl", "restart", "NetworkManager"], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    self.console.print(f"[bold green]Successfully switched back to managed mode: {self.interface_name}[/]")
                    self.logger.info(f"Switched back to managed mode: {self.interface_name}")
                except Exception as e:
                    self.console.print(f"[bold red]Error switching back to managed mode: {str(e)}[/]")
                    self.logger.error(f"Error switching back to managed mode: {str(e)}")
            
            # Give user a chance to see the results
            self.console.print("\n[bold yellow]Press Enter to return to the main menu...[/]")
            input()
            
            # Return to tools menu
            self.current_menu = "tools"
    

if __name__ == '__main__':
    main()
