# 🌐 NetPulse: Local Network Scanner & Hardware Fingerprinter

An advanced, modern **LAN Network Scanner & Device Inspector** written in pure Python with an interactive web GUI. Designed for university networking courses, demonstrations, and network administrators.

---

## 🚀 Key Features

1. **Complete Device Discovery (Modem & Gateway Included):**
   - Automatically detects the default gateway (ISP modem/router) and marks it with special badges.
   - Discovers all active client devices across the subnet (`/24`, `/16`, or custom CIDR).
   - Multi-threaded ping sweep and real-time system ARP table ingestion.

2. **Hardware Fingerprinting & Device Identification:**
   - **Offline OUI Database:** Maps MAC address prefixes to 500+ major manufacturers (Apple, Intel, Samsung, Dell, HP, TP-Link, Cisco, Espressif, Raspberry Pi, etc.).
   - **Hostname & Protocol Resolution:** Resolves friendly names using reverse DNS (`gethostbyaddr`), NetBIOS Name Service queries (RFC 1002 on UDP 137), and service probing.
   - **Role & OS Classification:** Distinguishes between **iPhones**, **MacBooks**, **Windows PCs**, **Android phones**, **Smart TVs**, **Network Printers**, and **IoT Sensors** (ESP32/Raspberry Pi).

3. **Modern Web GUI with Floating-Style Info Cards:**
   - **Floating Info Inspector:** Hovering over any device displays a sleek, glassmorphic floating card that follows your pointer, showcasing full device specifications, open ports, MAC address, vendor, and latency.
   - **Interactive Network Topology Map:** Visualizes the network as a radial graph with the modem/router at the hub and connected nodes orbiting outward with real-time data pulses.
   - **Live Metrics Dashboard:** Device category breakdowns (Phones, PCs, Gateways, IoT).
   - **Zero External Dependencies:** Built using Python's native standard library (`http.server.ThreadingHTTPServer`, `socket`, `concurrent.futures`). Runs on any machine out-of-the-box!
   - **Lab Demo / Presentation Mode:** Built-in simulation switch to present smoothly in university lecture halls where campus Wi-Fi has Client Isolation enabled.
   - **Report Export:** 1-click download of scan results in **JSON** or **CSV** format.

---

## 📁 Project Architecture

```
network_scanner/
├── app.py                 # Main entrypoint: HTTP server, REST API, CLI runner
├── scanner.py             # Discovery engine: Ping sweep, ARP inspection, NetBIOS & port probing
├── oui_database.py        # Offline 24-bit OUI MAC vendor database
├── device_classifier.py   # Heuristic classification for device roles, friendly names & OS
├── static/
│   ├── css/
│   │   └── style.css      # Glassmorphic dark theme, animations, floating card styles
│   └── js/
│       └── app.js         # Reactive frontend controller, topology canvas, hover popover
├── templates/
│   └── index.html         # Modern single-page responsive dashboard
└── README.md              # Documentation and presentation guide
```

---

## 🛠️ How to Run

### Step 1: Launch the Application
Open your terminal in the project directory and run:
```bash
python3 app.py
```

### Step 2: Access the Dashboard
The server will start at:
👉 **[http://localhost:5000](http://localhost:5000)** (your default browser will open automatically).

### Command-Line Options:
```bash
# Run on custom port
python3 app.py --port 8080

# Run without opening web browser automatically
python3 app.py --no-browser

# Launch directly with pre-loaded demo devices
python3 app.py --demo
```

---

## 🎓 University Presentation Guide (Theory & Defense)

When presenting this project for your course, evaluators often ask specific networking questions. Here are the core concepts used in this project:

### 1. How does NetPulse discover devices?
- **Address Resolution Protocol (ARP):** Layer 2 protocol that maps IPv4 addresses to physical MAC addresses. NetPulse reads `/proc/net/arp` (Linux) and system ARP cache (`ip neigh` / `arp -a`).
- **ICMP Echo Sweep:** Sends echo requests concurrently across 254 subnet hosts using `ThreadPoolExecutor(max_workers=50)`.
- **Active TCP Socket Probing:** If firewalls block ICMP ping, NetPulse tests common diagnostic ports (80, 443, 22, 53, 445).

### 2. How does NetPulse identify device names (e.g., "iPhone", "PC")?
- **MAC OUI (Organizationally Unique Identifier):** The first 24 bits (3 octets) of a MAC address are assigned by IEEE to specific hardware vendors (e.g., `3C:22:FB` $\rightarrow$ Apple, `C0:4A:00` $\rightarrow$ TP-Link).
- **Service Fingerprinting:** Apple devices often listen on port `62078` (Apple Mobile Device Service), Windows machines respond to port `445` (SMB) or NetBIOS Name Service (UDP `137`), and Printers expose port `9100` (RAW/JetDirect) or `631` (IPP).
- **Private/Randomized MACs:** Modern smartphones (iOS 14+, Android 10+) randomize MAC addresses on Wi-Fi for privacy. NetPulse identifies locally administered MACs by inspecting the second least-significant bit of the first byte (`MAC[0] & 0x02 != 0`).

### 3. Why is there a "Lab Demo" mode?
University and corporate Wi-Fi networks (like Eduroam) frequently enforce **AP Client Isolation**. This security feature prevents wireless devices on the same access point from communicating or exchanging ARP packets with one another. The built-in Lab Demo switch allows you to demonstrate full UI, topology mapping, and floating card inspectors regardless of network restrictions.

---

## 📄 License
Created for academic coursework and educational use.
