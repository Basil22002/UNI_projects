"""
Network Scanner Engine
Discovers active devices on the local area network (LAN), retrieves their IP, MAC,
manufacturer, hostname, latency, open ports, and device classification.
Includes both real socket/ARP scanning and university presentation demo mode.
"""

import socket
import subprocess
import platform
import struct
import time
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

from oui_database import lookup_vendor, normalize_mac
from device_classifier import classify_device


class NetworkScanner:
    def __init__(self):
        self.is_scanning = False
        self.progress = 0
        self.status_message = "Ready"
        self.devices: List[Dict[str, Any]] = []
        self.last_scan_time: Optional[str] = None
        self.local_ip: str = "127.0.0.1"
        self.gateway_ip: Optional[str] = None
        self.subnet: str = "192.168.1.0/24"
        self._lock = threading.Lock()
        self._detect_network_info()

    def _detect_network_info(self):
        """Detect local IP address, default gateway, and probable subnet."""
        # Detect local IP by creating a dummy socket to a public IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            # Doesn't actually send packets across internet, just chooses default route interface
            s.connect(("8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            self.local_ip = "127.0.0.1"

        # Detect default gateway (Modem / Router)
        self.gateway_ip = self._find_default_gateway()

        # Derive subnet
        if self.local_ip and self.local_ip != "127.0.0.1":
            parts = self.local_ip.split(".")
            self.subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        elif self.gateway_ip:
            parts = self.gateway_ip.split(".")
            self.subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        else:
            self.subnet = "192.168.1.0/24"

    def _find_default_gateway(self) -> Optional[str]:
        """Detect default gateway IP on Linux, macOS, or Windows."""
        # 1. Linux /proc/net/route
        if os.path.exists("/proc/net/route"):
            try:
                with open("/proc/net/route", "r") as f:
                    for line in f:
                        fields = line.strip().split()
                        if len(fields) >= 3 and fields[1] == "00000000":
                            gw_hex = fields[2]
                            gw_int = int(gw_hex, 16)
                            gw_ip = socket.inet_ntoa(struct.pack("<L", gw_int))
                            return gw_ip
            except Exception:
                pass

        # 2. Try 'ip route' or 'route -n'
        try:
            res = subprocess.run(["ip", "route", "show", "default"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=1)
            for line in res.stdout.splitlines():
                if "default via" in line:
                    parts = line.split()
                    idx = parts.index("via")
                    if idx + 1 < len(parts):
                        return parts[idx + 1]
        except Exception:
            pass

        # 3. Windows route print
        if platform.system() == "Windows":
            try:
                res = subprocess.run(["route", "print", "0.0.0.0"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2)
                for line in res.stdout.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 5 and parts[0] == "0.0.0.0":
                        return parts[2]
            except Exception:
                pass

        # Fallback assumption if local_ip is detected
        if self.local_ip and self.local_ip != "127.0.0.1":
            parts = self.local_ip.split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}.1"

        return "192.168.1.1"

    def _get_arp_table(self) -> Dict[str, str]:
        """
        Reads system ARP cache to map IP addresses to MAC addresses.
        Works across Linux (/proc/net/arp & ip neigh), macOS (arp -a), and Windows (arp -a).
        """
        arp_cache = {}

        # Linux /proc/net/arp
        if os.path.exists("/proc/net/arp"):
            try:
                with open("/proc/net/arp", "r") as f:
                    lines = f.readlines()[1:]  # skip header
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 4:
                            ip = parts[0]
                            mac = parts[3]
                            if mac != "00:00:00:00:00:00":
                                arp_cache[ip] = normalize_mac(mac)
            except Exception:
                pass

        # Fallback to 'arp -a' or 'ip neigh' command
        if not arp_cache:
            try:
                cmd = ["arp", "-a"] if platform.system() != "Linux" else ["ip", "neigh"]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2)
                for line in res.stdout.splitlines():
                    # Parse standard patterns
                    # Linux 'ip neigh': 192.168.1.100 dev eth0 lladdr 3c:22:fb:... REACHABLE
                    # Windows 'arp -a': 192.168.1.100       3c-22-fb-...      dynamic
                    match_ip = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                    match_mac = re.search(r"([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})", line)
                    if match_ip and match_mac:
                        ip = match_ip.group(1)
                        mac = match_mac.group(1)
                        if mac.replace(":", "").replace("-", "") != "000000000000":
                            arp_cache[ip] = normalize_mac(mac)
            except Exception:
                pass

        return arp_cache

    def _ping_host(self, ip: str, timeout_sec: float = 0.5) -> Optional[float]:
        """
        Sends a single ICMP echo ping to an IP address.
        Returns latency in milliseconds if responsive, otherwise None.
        """
        sys_name = platform.system()
        if sys_name == "Windows":
            cmd = ["ping", "-n", "1", "-w", str(int(timeout_sec * 1000)), ip]
        elif sys_name == "Darwin":
            cmd = ["ping", "-c", "1", "-W", str(int(timeout_sec * 1000)), ip]
        else:
            cmd = ["ping", "-c", "1", "-W", str(int(timeout_sec)), ip]

        start_t = time.time()
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout_sec + 0.3)
            if res.returncode == 0:
                elapsed = (time.time() - start_t) * 1000.0
                return round(elapsed, 1)
        except Exception:
            pass

        # If ICMP is blocked, try a quick TCP socket connect to common ports
        for test_port in [80, 443, 22, 53, 445]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.15)
                t0 = time.time()
                result = s.connect_ex((ip, test_port))
                s.close()
                if result == 0:  # Connection established
                    return round((time.time() - t0) * 1000.0, 1)
            except Exception:
                pass

        return None

    def _query_netbios_name(self, ip: str) -> Optional[str]:
        """
        Sends an RFC 1002 NetBIOS adapter status query to UDP 137.
        Windows PCs, Samba shares, and many network printers reply with their exact host name.
        """
        try:
            # NetBIOS Name Query packet
            packet = (
                b"\x82\x28\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"
                b"\x20CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x00\x00!\x00\x01"
            )
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.3)
            sock.sendto(packet, (ip, 137))
            data, _ = sock.recvfrom(1024)
            sock.close()
            if len(data) > 57:
                # Number of names at byte 56
                num_names = data[56]
                if num_names > 0:
                    name_bytes = data[57:72].rstrip()
                    name = name_bytes.decode("ascii", errors="ignore").strip()
                    if name and not name.startswith("\x00"):
                        return name
        except Exception:
            pass
        return None

    def _resolve_hostname(self, ip: str) -> str:
        """Resolves hostname using reverse DNS, then falls back to NetBIOS."""
        # 1. Reverse DNS
        try:
            host, _, _ = socket.gethostbyaddr(ip)
            if host and host != ip:
                # Clean up local domains like .local, .lan, .home
                clean = re.sub(r"\.(local|lan|home|home\.arpa|broadband)$", "", host, flags=re.I)
                return clean
        except Exception:
            pass

        # 2. NetBIOS lookup
        nb_name = self._query_netbios_name(ip)
        if nb_name:
            return nb_name

        return ""

    def _scan_open_ports(self, ip: str) -> List[int]:
        """Quickly checks a targeted list of diagnostic ports."""
        target_ports = [22, 53, 80, 443, 445, 631, 3389, 8008, 8080, 9100, 62078]
        open_ports = []

        def check_port(p):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                res = s.connect_ex((ip, p))
                s.close()
                if res == 0:
                    return p
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=len(target_ports)) as executor:
            results = executor.map(check_port, target_ports)
            for port in results:
                if port:
                    open_ports.append(port)

        return sorted(open_ports)

    def _get_local_mac(self) -> str:
        """Attempts to retrieve the local machine's MAC address."""
        try:
            import uuid
            mac_num = uuid.getnode()
            mac_str = ":".join(("%012X" % mac_num)[i : i + 2] for i in range(0, 12, 2))
            return mac_str
        except Exception:
            return "00:00:00:00:00:00"

    def run_real_scan(self, subnet_cidr: Optional[str] = None):
        """
        Executes a multi-threaded discovery scan across the target subnet.
        """
        with self._lock:
            self.is_scanning = True
            self.progress = 5
            self.status_message = "Detecting network gateway & interfaces..."
            self.devices = []

        self._detect_network_info()
        target_subnet = subnet_cidr or self.subnet

        # Extract base IP
        base_match = re.match(r"^(\d{1,3}\.\d{1,3}\.\d{1,3})\.", target_subnet)
        if not base_match:
            base_match = re.match(r"^(\d{1,3}\.\d{1,3}\.\d{1,3})\.", self.local_ip)
        prefix = base_match.group(1) if base_match else "192.168.1"

        ip_list = [f"{prefix}.{i}" for i in range(1, 255)]

        # Always ensure gateway is included
        if self.gateway_ip and self.gateway_ip not in ip_list:
            ip_list.insert(0, self.gateway_ip)

        with self._lock:
            self.progress = 15
            self.status_message = f"Sweeping subnet {prefix}.0/24 (254 addresses)..."

        responsive_hosts: Dict[str, float] = {}

        # Step 1: Subnet Ping Sweep using ThreadPool
        def probe(ip):
            rtt = self._ping_host(ip, timeout_sec=0.3)
            return ip, rtt

        completed_count = 0
        total_ips = len(ip_list)

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(probe, ip) for ip in ip_list]
            for future in as_completed(futures):
                ip, rtt = future.result()
                completed_count += 1
                if rtt is not None:
                    responsive_hosts[ip] = rtt
                with self._lock:
                    self.progress = int(15 + (completed_count / total_ips) * 45)

        # Step 2: Read ARP table for MAC addresses
        with self._lock:
            self.progress = 65
            self.status_message = "Reading ARP table & resolving MAC addresses..."

        arp_table = self._get_arp_table()

        # Add any hosts found in ARP cache even if ping was silent
        for ip, mac in arp_table.items():
            if ip.startswith(prefix) and ip not in responsive_hosts:
                responsive_hosts[ip] = 1.0

        # Include local machine
        if self.local_ip and self.local_ip not in responsive_hosts:
            responsive_hosts[self.local_ip] = 0.1

        # Step 3: Fingerprint each responsive host
        discovered_devices = []
        host_items = list(responsive_hosts.items())
        total_hosts = len(host_items)

        with self._lock:
            self.progress = 75
            self.status_message = f"Identifying details for {total_hosts} devices..."

        def inspect_host(ip, latency):
            is_gw = (ip == self.gateway_ip) or (ip.endswith(".1") and self.gateway_ip is None)
            is_me = (ip == self.local_ip)

            # MAC Address
            mac = arp_table.get(ip, "")
            if is_me and not mac:
                mac = self._get_local_mac()
            if not mac:
                mac = "Unknown MAC"

            # Vendor
            vendor = lookup_vendor(mac) if mac != "Unknown MAC" else "Unknown Vendor"

            # Hostname
            hostname = self._resolve_hostname(ip)
            if is_me and not hostname:
                hostname = socket.gethostname()

            # Port probe (only on active discovered devices)
            open_ports = self._scan_open_ports(ip)

            # Classify
            classification = classify_device(
                ip=ip,
                mac=mac,
                vendor=vendor,
                hostname=hostname,
                open_ports=open_ports,
                is_gateway=is_gw,
                is_local_machine=is_me,
            )

            device_info = {
                "ip": ip,
                "mac": mac,
                "vendor": vendor,
                "hostname": hostname or "N/A",
                "friendly_name": classification["friendly_name"],
                "device_type": classification["device_type"],
                "os_estimate": classification["os_estimate"],
                "icon": classification["icon"],
                "badge_color": classification["badge_color"],
                "is_gateway": is_gw,
                "is_local_machine": is_me,
                "latency_ms": latency,
                "open_ports": open_ports,
                "status": "Online",
            }
            return device_info

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(inspect_host, ip, lat) for ip, lat in host_items]
            for f in as_completed(futures):
                dev = f.result()
                discovered_devices.append(dev)

        # Sort devices: Gateway first, then by IP numerically
        def sort_key(d):
            if d.get("is_gateway"):
                return (0, 0, 0, 0)
            try:
                return (1, *[int(x) for x in d["ip"].split(".")])
            except Exception:
                return (1, 999, 999, 999)

        discovered_devices.sort(key=sort_key)

        with self._lock:
            self.devices = discovered_devices
            self.progress = 100
            self.is_scanning = False
            self.status_message = f"Scan complete. Found {len(discovered_devices)} device(s)."
            self.last_scan_time = time.strftime("%Y-%m-%d %H:%M:%S")

    def run_demo_scan(self):
        """
        Simulates a realistic home/office network for university presentations
        and testing when offline or inside restricted network sandboxes.
        """
        with self._lock:
            self.is_scanning = True
            self.progress = 10
            self.status_message = "Initializing Lab Simulation Scanner..."
            self.devices = []

        stages = [
            (25, "Sweeping simulated 192.168.1.0/24 subnet..."),
            (50, "Sending ARP queries & detecting default gateway..."),
            (75, "Analyzing mDNS, NetBIOS & Apple Mobile Device services..."),
            (90, "Classifying device roles & estimated OS..."),
        ]

        for p, msg in stages:
            time.sleep(0.35)
            with self._lock:
                self.progress = p
                self.status_message = msg

        time.sleep(0.3)

        # Simulated device fleet with authentic vendors, MACs, ports, and OS
        demo_devices = [
            {
                "ip": "192.168.1.1",
                "mac": "C0:4A:00:2B:1A:E8",
                "vendor": "TP-Link Technologies",
                "hostname": "tplinkwifi.net",
                "friendly_name": "TP-Link Archer AX50 Modem / Router",
                "device_type": "Modem / Gateway Router",
                "os_estimate": "OpenWrt / Linux RouterOS",
                "icon": "router",
                "badge_color": "warning",
                "is_gateway": True,
                "is_local_machine": False,
                "latency_ms": 1.2,
                "open_ports": [53, 80, 443, 1900],
                "status": "Online",
            },
            {
                "ip": "192.168.1.45",
                "mac": "34:13:E8:90:FA:21",
                "vendor": "Intel Corporation",
                "hostname": "ThinkPad-E14",
                "friendly_name": "Host Computer (This PC)",
                "device_type": "Host Computer (This PC)",
                "os_estimate": "Linux (Ubuntu / Mint)",
                "icon": "laptop",
                "badge_color": "primary",
                "is_gateway": False,
                "is_local_machine": True,
                "latency_ms": 0.1,
                "open_ports": [22, 5000],
                "status": "Online",
            },
            {
                "ip": "192.168.1.102",
                "mac": "3C:22:FB:4A:8D:19",
                "vendor": "Apple, Inc.",
                "hostname": "Sarahs-iPhone.local",
                "friendly_name": "Apple iPhone 15 Pro",
                "device_type": "Apple iPhone",
                "os_estimate": "iOS 17.5",
                "icon": "smartphone",
                "badge_color": "apple",
                "is_gateway": False,
                "is_local_machine": False,
                "latency_ms": 14.8,
                "open_ports": [62078],
                "status": "Online",
            },
            {
                "ip": "192.168.1.108",
                "mac": "F4:F1:5A:1C:89:33",
                "vendor": "Apple, Inc.",
                "hostname": "Alex-MacBook-Pro.local",
                "friendly_name": "Apple MacBook Pro M3",
                "device_type": "Apple Mac / MacBook",
                "os_estimate": "macOS Sonoma",
                "icon": "laptop",
                "badge_color": "apple",
                "is_gateway": False,
                "is_local_machine": False,
                "latency_ms": 6.3,
                "open_ports": [22, 548, 5000],
                "status": "Online",
            },
            {
                "ip": "192.168.1.115",
                "mac": "78:47:1D:9C:20:4B",
                "vendor": "Samsung Electronics",
                "hostname": "Galaxy-S24-Ultra",
                "friendly_name": "Samsung Galaxy S24 Ultra",
                "device_type": "Samsung Galaxy Smartphone",
                "os_estimate": "Android 14 (One UI 6.1)",
                "icon": "smartphone",
                "badge_color": "success",
                "is_gateway": False,
                "is_local_machine": False,
                "latency_ms": 18.2,
                "open_ports": [],
                "status": "Online",
            },
            {
                "ip": "192.168.1.140",
                "mac": "74:86:7A:B3:5D:80",
                "vendor": "Dell Inc.",
                "hostname": "DESKTOP-GAMING",
                "friendly_name": "Dell XPS Gaming PC",
                "device_type": "Desktop / Laptop PC",
                "os_estimate": "Windows 11 Pro",
                "icon": "desktop",
                "badge_color": "info",
                "is_gateway": False,
                "is_local_machine": False,
                "latency_ms": 4.5,
                "open_ports": [139, 445, 3389],
                "status": "Online",
            },
            {
                "ip": "192.168.1.155",
                "mac": "58:A2:B5:7F:02:11",
                "vendor": "LG Electronics",
                "hostname": "LG-webOSTV-C3",
                "friendly_name": "LG 65-inch OLED Smart TV",
                "device_type": "Smart TV / Streaming Box",
                "os_estimate": "webOS 23",
                "icon": "tv",
                "badge_color": "purple",
                "is_gateway": False,
                "is_local_machine": False,
                "latency_ms": 22.1,
                "open_ports": [8008, 8009, 8080],
                "status": "Online",
            },
            {
                "ip": "192.168.1.200",
                "mac": "48:0F:CF:91:A4:77",
                "vendor": "HP Inc.",
                "hostname": "HP-LaserJet-M404n",
                "friendly_name": "HP LaserJet Network Printer",
                "device_type": "Network Printer",
                "os_estimate": "HP JetDirect Firmware",
                "icon": "printer",
                "badge_color": "secondary",
                "is_gateway": False,
                "is_local_machine": False,
                "latency_ms": 9.4,
                "open_ports": [80, 443, 515, 631, 9100],
                "status": "Online",
            },
            {
                "ip": "192.168.1.210",
                "mac": "24:0A:C4:6E:9B:10",
                "vendor": "Espressif Systems",
                "hostname": "espressif-smartplug",
                "friendly_name": "Living Room Smart Plug (ESP32)",
                "device_type": "Smart Home IoT Sensor (ESP32/ESP8266)",
                "os_estimate": "FreeRTOS / ESP-IDF",
                "icon": "iot",
                "badge_color": "warning",
                "is_gateway": False,
                "is_local_machine": False,
                "latency_ms": 28.7,
                "open_ports": [80],
                "status": "Online",
            },
            {
                "ip": "192.168.1.220",
                "mac": "B8:27:EB:D3:55:09",
                "vendor": "Raspberry Pi Foundation",
                "hostname": "homeassistant.local",
                "friendly_name": "Raspberry Pi Home Server",
                "device_type": "Raspberry Pi (SBC / Server)",
                "os_estimate": "Debian Linux (Home Assistant OS)",
                "icon": "server",
                "badge_color": "warning",
                "is_gateway": False,
                "is_local_machine": False,
                "latency_ms": 3.1,
                "open_ports": [22, 80, 8123],
                "status": "Online",
            },
        ]

        with self._lock:
            self.devices = demo_devices
            self.progress = 100
            self.is_scanning = False
            self.status_message = f"Demo scan complete. Simulated {len(demo_devices)} connected devices."
            self.last_scan_time = time.strftime("%Y-%m-%d %H:%M:%S")

    def get_status(self) -> Dict[str, Any]:
        """Returns the current scanner status and discovered device list."""
        with self._lock:
            return {
                "is_scanning": self.is_scanning,
                "progress": self.progress,
                "status_message": self.status_message,
                "device_count": len(self.devices),
                "devices": self.devices,
                "last_scan_time": self.last_scan_time,
                "local_ip": self.local_ip,
                "gateway_ip": self.gateway_ip,
                "subnet": self.subnet,
            }
