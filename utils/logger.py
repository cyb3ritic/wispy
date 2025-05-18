
from scapy.all import *
from datetime import datetime
import logging
from pathlib import Path
import shutil



class Logger:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path("logs") / self.timestamp
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.main_log = self.log_dir / "main.log"
        self.attack_log = self.log_dir / "attacks.log"
        self.network_log = self.log_dir / "networks.log"
        self.client_log = self.log_dir / "clients.log"
        self.evil_twin_log = self.log_dir / "evil_twin.log"
        self.dns_log = self.log_dir / "dns_queries.log"
        self.traffic_log = self.log_dir / "traffic.log"
        
        self.logger = logging.getLogger("WiFiAngel")
        self.logger.setLevel(logging.WARNING)
        
        detailed_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        attack_formatter = logging.Formatter('%(asctime)s - %(attack_type)s - %(message)s')
        network_formatter = logging.Formatter('%(asctime)s - %(network)s - %(message)s')
        client_formatter = logging.Formatter('%(asctime)s - %(client)s - %(message)s')
        evil_twin_formatter = logging.Formatter('%(asctime)s - %(evil_twin)s - %(message)s')
        dns_formatter = logging.Formatter('%(asctime)s - %(client_ip)s - %(query)s - %(type)s')
        traffic_formatter = logging.Formatter('%(asctime)s - %(src)s - %(dst)s - %(bytes)s - %(protocol)s')
        
        self.main_handler = logging.FileHandler(self.main_log)
        self.main_handler.setFormatter(detailed_formatter)
        
        self.attack_handler = logging.FileHandler(self.attack_log)
        self.attack_handler.setFormatter(attack_formatter)
        
        self.network_handler = logging.FileHandler(self.network_log)
        self.network_handler.setFormatter(network_formatter)
        
        self.client_handler = logging.FileHandler(self.client_log)
        self.client_handler.setFormatter(client_formatter)
        
        self.evil_twin_handler = logging.FileHandler(self.evil_twin_log)
        self.evil_twin_handler.setFormatter(evil_twin_formatter)
        
        self.dns_handler = logging.FileHandler(self.dns_log)
        self.dns_handler.setFormatter(dns_formatter)
        
        self.traffic_handler = logging.FileHandler(self.traffic_log)
        self.traffic_handler.setFormatter(traffic_formatter)
        
        self.logger.addHandler(self.main_handler)
        
        self.attack_logger = logging.getLogger("WiFiAngel.Attacks")
        self.attack_logger.setLevel(logging.WARNING)
        self.attack_logger.addHandler(self.attack_handler)
        
        self.network_logger = logging.getLogger("WiFiAngel.Networks")
        self.network_logger.setLevel(logging.WARNING)
        self.network_logger.addHandler(self.network_handler)
        
        self.client_logger = logging.getLogger("WiFiAngel.Clients")
        self.client_logger.setLevel(logging.WARNING)
        self.client_logger.addHandler(self.client_handler)
        
        self.evil_twin_logger = logging.getLogger("WiFiAngel.EvilTwin")
        self.evil_twin_logger.setLevel(logging.WARNING)
        self.evil_twin_logger.addHandler(self.evil_twin_handler)
        
        self.dns_logger = logging.getLogger("WiFiAngel.DNS")
        self.dns_logger.setLevel(logging.WARNING)
        self.dns_logger.addHandler(self.dns_handler)
        
        self.traffic_logger = logging.getLogger("WiFiAngel.Traffic")
        self.traffic_logger.setLevel(logging.WARNING)
        self.traffic_logger.addHandler(self.traffic_handler)
    
    def log_attack(self, attack_type, message, **kwargs):
        extra = {'attack_type': attack_type}
        extra.update(kwargs)
        self.attack_logger.info(message, extra=extra)
        self.info(f"Attack: {attack_type} - {message}")
    
    def log_network(self, network_ssid, message, **kwargs):
        extra = {'network': network_ssid}
        extra.update(kwargs)
        self.network_logger.info(message, extra=extra)
        self.info(f"Network: {network_ssid} - {message}")
    
    def log_client(self, client_mac, message, **kwargs):
        extra = {'client': client_mac}
        extra.update(kwargs)
        self.client_logger.info(message, extra=extra)
        self.info(f"Client: {client_mac} - {message}")
    
    def log_evil_twin(self, message, **kwargs):
        extra = {'evil_twin': kwargs.get('ssid', 'Unknown')}
        extra.update(kwargs)
        self.evil_twin_logger.info(message, extra=extra)
        self.info(f"Evil Twin: {message}")
    
    def log_dns_query(self, client_ip, query, query_type):
        extra = {
            'client_ip': client_ip,
            'query': query,
            'type': query_type
        }
        self.dns_logger.info(f"DNS Query: {query}", extra=extra)
    
    def log_traffic(self, src, dst, bytes_count, protocol):
        extra = {
            'src': src,
            'dst': dst,
            'bytes': bytes_count,
            'protocol': protocol
        }
        self.traffic_logger.info(f"Traffic: {src} -> {dst}", extra=extra)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)

    def generate_report(self):
        report_file = self.log_dir / f"report_{self.timestamp}.html"
        
        with open(self.main_log) as f:
            main_logs = f.readlines()
        with open(self.attack_log) as f:
            attack_logs = f.readlines()
        with open(self.network_log) as f:
            network_logs = f.readlines()
        with open(self.client_log) as f:
            client_logs = f.readlines()
            
        html_content = f"""
        <html>
        <head>
            <title>WiFiAngel Security Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                .section {{ margin: 20px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .attack {{ background-color: #ffe6e6; }}
                .network {{ background-color: #e6ffe6; }}
                .client {{ background-color: #e6e6ff; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>WiFiAngel Security Analysis Report</h1>
            <p>Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <div class="section">
                <h2>Attack Summary</h2>
                <table>
                    <tr><th>Timestamp</th><th>Attack Type</th><th>Details</th></tr>
                    {''.join(f"<tr><td>{line.split(' - ')[0]}</td><td>{line.split(' - ')[1]}</td><td>{' - '.join(line.split(' - ')[2:]).strip()}</td></tr>" for line in attack_logs)}
                </table>
            </div>
            
            <div class="section">
                <h2>Network Activity</h2>
                <table>
                    <tr><th>Timestamp</th><th>Network</th><th>Activity</th></tr>
                    {''.join(f"<tr><td>{line.split(' - ')[0]}</td><td>{line.split(' - ')[1]}</td><td>{' - '.join(line.split(' - ')[2:]).strip()}</td></tr>" for line in network_logs)}
                </table>
            </div>
            
            <div class="section">
                <h2>Client Connections</h2>
                <table>
                    <tr><th>Timestamp</th><th>Client</th><th>Activity</th></tr>
                    {''.join(f"<tr><td>{line.split(' - ')[0]}</td><td>{line.split(' - ')[1]}</td><td>{' - '.join(line.split(' - ')[2:]).strip()}</td></tr>" for line in client_logs)}
                </table>
            </div>
            
            <div class="section">
                <h2>System Events</h2>
                <table>
                    <tr><th>Timestamp</th><th>Level</th><th>Message</th></tr>
                    {''.join(f"<tr><td>{line.split(' - ')[0]}</td><td>{line.split(' - ')[1]}</td><td>{' - '.join(line.split(' - ')[2:]).strip()}</td></tr>" for line in main_logs)}
                </table>
            </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        return report_file