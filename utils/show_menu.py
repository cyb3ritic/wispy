
import time
from scapy.all import *
from rich.prompt import Prompt
from rich.panel import Panel
import threading


def show_main_menu(self):
    """Shows the main menu"""
    self.current_menu = "main"
    while True:
        try:
            self.console.print("\n[bold yellow]Main Menu[/]")
            self.console.print("1. 📡 Start Monitor Mode")
            if self.scanning:
                self.console.print("[bold green]🔍 Network Scan Active[/]")
            self.console.print("2. 🔍 Start/Stop Network Scan")
            self.console.print("3. 🎯 Select Target Network")
            self.console.print("4. ⚔️ Attack Techniques")
            self.console.print("5. 🔧 Tools")
            self.console.print("6. 🛡️ Security Audit")
            self.console.print("0. ❌ Exit")
            
            choice = Prompt.ask("Select an option")
            self.logger.info(f"Main menu selection: {choice}")
            
            if choice == "1":
                if not self.start_monitor_mode():
                    continue
            elif choice == "2":
                # Check if monitor mode is active
                if not self.interface_name.endswith("mon"):
                    self.console.print("[bold yellow]⚠️ Monitor mode is not active![/]")
                    self.console.print("[bold blue]Enabling monitor mode automatically...[/]")
                    if not self.start_monitor_mode():
                        self.console.print("[bold red]❌ Failed to enable monitor mode. Please try again.[/]")
                        continue
                
                self.scanning = not self.scanning
                if self.scanning:
                    scan_thread = threading.Thread(target=self.scan_networks)
                    scan_thread.daemon = True
                    scan_thread.start()
                    self.console.print("[bold green]Network scan started. Press Ctrl+C to stop.[/]")
                else:
                    self.console.print("[bold yellow]Stopping network scan...[/]")
            elif choice == "3":
                self.select_target_network()
            elif choice == "4":
                self.current_menu = "attack"
                self.show_attack_menu()
            elif choice == "5":
                self.current_menu = "tools"
                self.show_tools_menu()
            elif choice == "6":
                self.security_audit()
            elif choice == "0":
                if self.scanning:
                    self.console.print("[bold yellow]Stopping network scan...[/]")
                    self.scanning = False
                    time.sleep(1)
                self.logger.info("Program shutting down...")
                self.cleanup_and_exit()

        except KeyboardInterrupt:
            if self.scanning:
                self.scanning = False
                self.console.print("\n[bold yellow]Stopping network scan...[/]")
                time.sleep(1)
                continue
            else:
                if self.current_menu == "main":
                    self.logger.info("Program shutting down...")
                    self.cleanup_and_exit()
                else:
                    self.logger.info("Returning to main menu")
                    self.console.print("\n[bold yellow]Returning to main menu...[/]")
                    self.current_menu = "main"
                    continue



def show_attack_menu(self):
    """Shows attack techniques menu"""
    while True:
        if self.selected_network:
            network = self.networks[self.selected_network]
            self.console.print(Panel(f"[bold cyan]Selected Network: {network['ssid']} ({self.selected_network})[/]"))
        
        self.console.print("\n[bold yellow]Attack Techniques:[/]")
        self.console.print("1. 📦 WPA/WPA2/WPA3 Handshake Capture")
        self.console.print("2. ⚡ Deauthentication Attack")
        self.console.print("3. 📚 Dictionary Attack")
        self.console.print("4. 🕵️ Evil Twin Attack")
        self.console.print("0. ↩️ Back to Main Menu")
        
        choice = Prompt.ask("Select an option")
        
        if choice == "1":
            self.capture_handshake()
        elif choice == "2":
            self.show_deauth_menu()
        elif choice == "3":
            self.dictionary_attack()
        elif choice == "4":
            self.evil_twin_attack()
        elif choice == "0":
            self.current_menu = "main"
            return
        



def show_tools_menu(self):
    """Shows tools menu"""
    while True:
        self.console.print("\n[bold yellow]Tools:[/]")
        self.console.print("1. 📡 WiFi Adapter Settings")
        self.console.print("2. 📊 Network Statistics")
        self.console.print("3. 📱 Client Analysis")
        self.console.print("4. 🔍 WiFi Signal Analyzer")
        self.console.print("5. 🕵️ WiFi Hidden SSID Discovery")
        self.console.print("0. ↩️ Back to Main Menu")
        
        choice = Prompt.ask("Select an option")
        
        if choice == "1":
            self.wifi_adapter_settings()
        elif choice == "2":
            self.show_network_stats()
        elif choice == "3":
            self.client_analysis()
        elif choice == "4":
            self.signal_analyzer()
        elif choice == "5":
            self.hidden_ssid_discovery()
        elif choice == "0":
            break



def show_deauth_menu(self):
    """Shows deauthentication attack menu"""
    while True:
        self.console.print("\n[bold yellow]Deauthentication Attack:[/]")
        self.console.print("1. 🌐 All Clients Attack")
        self.console.print("2. 🎯 Single Client Attack")
        self.console.print("0. ↩️ Back")
        
        choice = Prompt.ask("Select an option")
        
        if choice == "1":
            self.deauth_all_clients()
        elif choice == "2":
            self.deauth_single_client()
        elif choice == "0":
            break
