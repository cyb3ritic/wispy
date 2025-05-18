# WiSpy - Wireless Network Security Analysis Tool

WiSpy is a comprehensive wireless network security analysis tool for Linux, designed to help you scan, audit, attack, and protect WiFi networks. It provides a rich terminal interface for both offensive and defensive wireless operations.

## Features

- **Network Scanning:** Detects nearby WiFi networks, displays security, signal, and client information.
- **Security Auditing:** Audits networks for vulnerabilities, including rogue/Evil Twin AP detection.
- **Handshake Capture:** Captures WPA/WPA2/WPA3 handshakes for password cracking.
- **Dictionary Attack:** Attempts to crack captured handshakes using large password lists.
- **Evil Twin Attack:** Creates a fake access point to capture credentials from unsuspecting clients.
- **Deauthentication:** Disconnects clients from target networks.
- **Hidden SSID Discovery:** Reveals hidden WiFi networks and their clients.
- **Live Signal Analysis:** Monitors signal strength and interference in real time.
- **Comprehensive Logging:** Generates detailed logs and HTML reports for all activities.

## Requirements

- **Operating System:** Linux (Kali, Debian, Ubuntu recommended)
- **Root Privileges:** Must be run as root (`sudo`)
- **Dependencies:**  
  - aircrack-ng  
  - hashcat  
  - hcxdumptool  
  - hostapd  
  - dnsmasq  
  - macchanger  
  - reaver  
  - python3-scapy  
  - Python 3.8+  
  - [Rich](https://github.com/Textualize/rich) (Python library)

Install dependencies on Debian/Ubuntu/Kali:
```sh
sudo apt update
sudo apt install -y aircrack-ng hashcat hcxdumptool hostapd dnsmasq macchanger reaver python3-scapy
pip install rich
```

## Usage

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourrepo/wispy.git
    cd wispy
    ```

2. **Run WiSpy as root:**
    ```sh
    sudo python3 wispy.py
    ```

3. **Follow the interactive menu to scan, audit, or attack networks.**

## Directory Structure

- `wispy.py` - Main application entry point
- `attacks/` - Attack modules (evil twin, handshake capture, etc.)
- `audit/` - Security audit logic
- `utils/` - Utility functions (logging, interface handling, menus)
- `wordlists/` - Password lists for dictionary attacks
- `logs/` - Output logs and reports

## Disclaimer

This tool is for **educational and authorized security testing** only. Unauthorized use against networks you do not own or have explicit permission to test is illegal.

## License

[MIT License](LICENSE)

---

**WiSpy** - Secure • Analyze • Defend  
https://github.com/yourrepo/wispy