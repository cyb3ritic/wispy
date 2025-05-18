import sys
import os
import shutil
import time
import signal
import socket
import platform as system_platform
import argparse
import gc
from scapy.all import *
from rich.console import Console, Group
from rich.table import Table, Row
from rich.prompt import Prompt
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.box import ROUNDED
from datetime import datetime
import pywifi
from pywifi import const
import threading
from concurrent.futures import ThreadPoolExecutor
from itertools import islice
import subprocess
import random
import json
import glob
import logging
from pathlib import Path
import shutil
import asyncio
from bleak import BleakScanner
from zeroconf import ServiceBrowser, Zeroconf
import nmap
import concurrent.futures
import shlex
import tempfile
import ipaddress
import re
import io
import csv
import base64
from rich.progress import Progress, BarColumn, TimeRemainingColumn, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.markdown import Markdown
from rich.style import Style
from rich.text import Text
from rich.tree import Tree
import select
from rich import box
import netifaces
import traceback

def start_monitor_mode(self):
    try:
        self.console.print("[bold green]Starting monitor mode...[/]")
        self.logger.info("Starting monitor mode")
        
        subprocess.run(["systemctl", "stop", "NetworkManager"], stdout=subprocess.PIPE)
        self.logger.info("NetworkManager stopped")
        time.sleep(1)
        
        subprocess.run(["airmon-ng", "check", "kill"], stdout=subprocess.PIPE)
        subprocess.run(["airmon-ng", "start", self.interface_name], stdout=subprocess.PIPE)
        self.logger.info(f"{self.interface_name} switched to monitor mode")
        
        interfaces = subprocess.check_output(["iwconfig"], stderr=subprocess.STDOUT).decode()
        for line in interfaces.split('\n'):
            if "Mode:Monitor" in line:

                
                self.interface_name = line.split()[0]
                break
        
        self.console.print(f"[bold green]Monitor mode active: {self.interface_name}[/]")
        self.logger.info(f"Monitor mode active: {self.interface_name}")
        return True
    except Exception as e:
        self.logger.error(f"Could not start monitor mode: {str(e)}")
        self.console.print(f"[bold red]Error: {str(e)}[/]")
        return False
    

def wifi_adapter_settings(self):
    """WiFi adapter settings menu"""
    while True:
        self.console.print("\n[bold yellow]WiFi Adapter Settings:[/]")
        self.console.print(f"Current Adapter: {self.interface_name}")
        self.console.print("1. 📡 Change Adapter Mode")
        self.console.print("2. 📶 Change Channel")
        self.console.print("3. 📊 Adapter Information")
        self.console.print("0. ↩️ Back")
        
        choice = Prompt.ask("Select an option")
        
        if choice == "1":
            self.change_adapter_mode()
        elif choice == "2":
            self.change_channel()
        elif choice == "3":
            self.show_adapter_info()
        elif choice == "0":
            break


def change_adapter_mode(self):
    """Changes adapter mode menu"""
    self.console.print("\n[bold yellow]Adapter Mode:[/]")
    self.console.print("1. Monitor Mode")
    self.console.print("2. Managed Mode")
    self.console.print("0. Back")
    
    choice = Prompt.ask("Select an option")
    
    try:
        if choice == "1":
            subprocess.run(["airmon-ng", "start", self.interface_name], stdout=subprocess.PIPE)
            
            # Monitor moduna geçtikten sonra yeni arayüz adını bul
            interfaces = subprocess.check_output(["iwconfig"], stderr=subprocess.STDOUT).decode()
            for line in interfaces.split('\n'):
                if "Mode:Monitor" in line:
                    self.interface_name = line.split()[0]
                    break
            
            self.console.print(f"[bold green]Monitor mode activated on {self.interface_name}![/]")
            self.logger.info(f"Monitor mode activated on {self.interface_name}")
        elif choice == "2":
            self.console.print("[bold yellow]Switching to managed mode...[/]")
            
            # Stop monitor mode
            subprocess.run(["airmon-ng", "stop", self.interface_name], stdout=subprocess.PIPE)
            
            # Get original interface name (remove "mon" suffix if present)
            if "mon" in self.interface_name:
                self.interface_name = self.interface_name.replace("mon", "")
            
            # Switch to managed mode
            subprocess.run(["ip", "link", "set", self.interface_name, "down"], stdout=subprocess.PIPE)
            subprocess.run(["iw", self.interface_name, "set", "type", "managed"], stdout=subprocess.PIPE)
            subprocess.run(["ip", "link", "set", self.interface_name, "up"], stdout=subprocess.PIPE)
            
            # Restart NetworkManager
            subprocess.run(["systemctl", "restart", "NetworkManager"], stdout=subprocess.PIPE)
            
            # Wait for changes to apply
            time.sleep(2)
            
            # Verify the mode change
            try:
                iw_info = subprocess.check_output(["iwconfig", self.interface_name], stderr=subprocess.STDOUT).decode()
                if "Mode:Managed" in iw_info:
                    self.console.print(f"[bold green]Successfully switched to managed mode: {self.interface_name}[/]")
                    self.logger.info(f"Switched to managed mode: {self.interface_name}")
                else:
                    self.console.print("[bold yellow]Warning: Interface might not be in managed mode[/]")
            except Exception as e:
                self.console.print(f"[bold red]Error verifying interface mode: {str(e)}[/]")
    except Exception as e:
        self.console.print(f"[bold red]Error: {str(e)}[/]")


def change_channel(self):
    """Changes channel"""
    channel = Prompt.ask("Enter new channel number (1-14 or 36-165)")
    try:
        interface_name = self.interface_name
        channel = int(channel)
        os.system(f"iwconfig {interface_name} channel {channel}")
        self.console.print(f"[bold green]Channel changed to {channel}![/]")
    except ValueError:
        self.console.print("[bold red]Invalid channel number![/]")


def show_adapter_info(self):
    """Shows adapter information"""
    try:
        interface_name = self.interface_name
        info = subprocess.check_output(["iwconfig", interface_name]).decode()
        self.console.print(Panel(info, title="Adapter Information", border_style="blue"))
    except Exception as e:
        self.console.print(f"[bold red]Error: {str(e)}[/]")