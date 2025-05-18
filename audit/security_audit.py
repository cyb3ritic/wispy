
from scapy.all import *
from rich.table import Table
from pathlib import Path



def security_audit(self):
    """Performs a security audit of nearby networks, including rogue AP detection"""
    if not self.networks:
        self.console.print("[bold red]No networks found. Please scan first![/]")
        return

    # --- Load known networks from wordlists/known_hosts ---
    KNOWN_NETWORKS = {}
    known_hosts_path = Path("wordlists/known_hosts")
    if known_hosts_path.exists():
        with open(known_hosts_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                ssid, bssid = line.split(":", 1)
                ssid = ssid.strip()
                bssid = bssid.strip().lower()
                if ssid not in KNOWN_NETWORKS:
                    KNOWN_NETWORKS[ssid] = set()
                KNOWN_NETWORKS[ssid].add(bssid)

    # --- Build ACCESS_POINTS dict for rogue AP detection ---
    ACCESS_POINTS = {}
    for bssid, net in self.networks.items():
        ACCESS_POINTS[bssid] = {
            "ssid": net["ssid"],
            "bssid": bssid,
            "encryption": net["cipher"],
            "signal": net["signal"],
            "wps": net["wps"]
        }

    def detect_rogue_ap(ap_info):
        """Check if access point might be a rogue/evil twin"""
        ssid = ap_info["ssid"]
        bssid = ap_info["bssid"]

        # If we have a known network file, compare with existing SSIDs
        if KNOWN_NETWORKS and ssid in KNOWN_NETWORKS and bssid not in KNOWN_NETWORKS[ssid]:
            return True

        # Always check for duplicate SSIDs with different BSSIDs (evil twin) if known_hosts is missing or empty
        for existing_ap in ACCESS_POINTS.values():
            if existing_ap["ssid"] == ssid and existing_ap["bssid"] != bssid:
                # If different encryption, almost certainly a rogue AP
                if existing_ap["encryption"] != ap_info["encryption"]:
                    return True
                # If open network claiming to be a known network, likely rogue
                if ap_info["encryption"].lower() == "open" and ssid not in ["", "[Hidden]"]:
                    return True

        return False

    # Helper to determine the highest risk level
    def get_highest_risk(risks):
        levels = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
        if not risks:
            return "Low"
        return max(risks, key=lambda r: levels.get(r, 0))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Network", style="cyan")
    table.add_column("Security Issues", style="red")
    table.add_column("Risk Level", style="yellow")
    table.add_column("Recommendations", style="green")
    table.add_column("Rogue/Evil Twin", style="bold red")

    for bssid, network in self.networks.items():
        issues = []
        risks = []
        recommendations = []
        rogue_status = "[green]No[/]"

        # Encryption checks
        cipher = network['cipher'].upper()
        if "OPEN" in cipher:
            issues.append("No encryption")
            risks.append("High")
            recommendations.append("Enable WPA2/WPA3 encryption")
        elif "WEP" in cipher:
            issues.append("WEP encryption (broken)")
            risks.append("High")
            recommendations.append("Upgrade to WPA2/WPA3")
        elif "WPA" in cipher and "WPA2" not in cipher:
            issues.append("WPA1 encryption (outdated)")
            risks.append("Medium")
            recommendations.append("Upgrade to WPA2/WPA3")

        # WPS check
        if network['wps']:
            issues.append("WPS enabled")
            risks.append("Medium")
            recommendations.append("Disable WPS")

        # Signal strength checks
        if network['signal'] > -30:
            issues.append("Signal too strong")
            risks.append("Low")
            recommendations.append("Reduce transmit power")
        elif network['signal'] < -70:
            issues.append("Signal too weak")
            risks.append("Low")
            recommendations.append("Increase transmit power or add repeaters")

        # Rogue/Evil Twin Detection
        ap_info = {
            "ssid": network["ssid"],
            "bssid": bssid,
            "encryption": network["cipher"]
        }
        if detect_rogue_ap(ap_info):
            rogue_status = "[bold red]Yes[/]"
            issues.append("Possible Rogue/Evil Twin AP detected")
            risks.append("Critical")
            recommendations.append("Investigate AP, verify BSSID and encryption")

        # Remove duplicates and empty entries
        issues = [i for i in dict.fromkeys(issues) if i]
        recommendations = [r for r in dict.fromkeys(recommendations) if r]
        risk_level = get_highest_risk(risks)

        table.add_row(
            network['ssid'] if network['ssid'] else "[Hidden]",
            "\n".join(issues) if issues else "None",
            risk_level,
            "\n".join(recommendations) if recommendations else "None",
            rogue_status
        )

    self.console.print(table)