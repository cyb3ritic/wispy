# WiSpy - Wireless Network Security Analysis Tool

WiSpy is a powerful and user-friendly wireless network security analysis toolkit for Linux. It empowers security professionals, penetration testers, and enthusiasts to scan, audit, attack, and defend WiFi networks through a rich, interactive terminal interface. WiSpy brings together advanced offensive and defensive wireless operations in a single, modular platform.

## Features

- **Network Scanning:**  
  Quickly discover nearby WiFi networks, view detailed information such as SSID, BSSID, channel, encryption type, signal strength, and connected clients.

- **Security Auditing:**  
  Assess wireless networks for common vulnerabilities, including detection of rogue access points and Evil Twin attacks.

- **Handshake Capture:**  
  Seamlessly capture WPA/WPA2/WPA3 handshakes for offline password cracking and security analysis.

- **Dictionary Attack:**  
  Use customizable wordlists to attempt cracking of captured handshakes, leveraging tools like aircrack-ng and hashcat.

- **Evil Twin Attack:**  
  Deploy a fake access point to lure clients and capture credentials, with automated setup and cleanup.

- **Deauthentication:**  
  Disconnect clients from target networks using deauth attacks, either selectively or en masse.

- **Hidden SSID Discovery:**  
  Reveal and analyze hidden WiFi networks and enumerate their associated clients.

- **Live Signal Analysis:**  
  Monitor real-time signal strength, noise, and interference to optimize wireless performance or identify anomalies.

- **Comprehensive Logging:**  
  Automatically generate detailed logs and HTML reports for all activities, supporting audit trails and reporting.

## Requirements

- **Operating System:** Linux (Kali, Debian, Ubuntu recommended)
- **Root Privileges:** Must be run as root (`sudo`)
- **Dependencies:**  
  - aircrack-ng  
  - hashcat  
  - hcxdumptool  
  - hostapd  
  - dnsmasq  
  - reaver  
  - python3-scapy  
  - Python 3.8+  
  - [Rich](https://github.com/Textualize/rich) (Python library for terminal UI)

**Install dependencies on Debian/Ubuntu/Kali:**
```sh
sudo apt update
sudo apt install -y aircrack-ng hashcat hcxdumptool hostapd dnsmasq macchanger reaver python3-scapy
pip install rich
```

## Usage

1. **Clone the repository:**
    ```sh
    git clone https://github.com/cyb3ritic/wispy.git
    cd wispy
    ```

2. **Run WiSpy as root:**
    ```sh
    sudo python3 wispy.py
    ```

3. **Navigate the interactive menu:**  
   Use the intuitive menu system to scan for networks, audit security, launch attacks, or generate reports. All actions are logged for later review.

## Directory Structure

- `wispy.py` - Main application entry point and orchestrator
- `attacks/` - Attack modules (Evil Twin, handshake capture, deauth, etc.)
- `audit/` - Security audit and vulnerability assessment logic
- `utils/` - Utility functions (logging, interface handling, menus)
- `wordlists/` - Password lists for dictionary attacks
- `logs/` - Output logs and HTML reports

## Contributing

Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request on GitHub.

## Disclaimer

WiSpy is intended **solely for educational purposes and authorized security testing**. Unauthorized use against networks you do not own or have explicit permission to test is illegal and strictly prohibited.

---

**WiSpy** - Secure • Analyze • Defend  
https://github.com/yourrepo/wispy