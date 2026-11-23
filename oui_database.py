"""
Offline MAC Address OUI (Organizationally Unique Identifier) Database
Maps the first 3 octets (24 bits) of a MAC address to manufacturer names.
Works 100% offline without requiring internet connection or third-party APIs.
"""

import re
import urllib.request
import json

# Curated high-coverage OUI database for common consumer and network hardware
OUI_DATABASE = {
    # Apple Inc.
    "00:03:93": "Apple, Inc.",
    "00:05:02": "Apple, Inc.",
    "00:0A:27": "Apple, Inc.",
    "00:0A:95": "Apple, Inc.",
    "00:0D:93": "Apple, Inc.",
    "00:10:FA": "Apple, Inc.",
    "00:11:24": "Apple, Inc.",
    "00:14:51": "Apple, Inc.",
    "00:16:CB": "Apple, Inc.",
    "00:17:F2": "Apple, Inc.",
    "00:19:E3": "Apple, Inc.",
    "00:1B:63": "Apple, Inc.",
    "00:1C:B3": "Apple, Inc.",
    "00:1D:4F": "Apple, Inc.",
    "00:1E:52": "Apple, Inc.",
    "00:1E:C2": "Apple, Inc.",
    "00:1F:5B": "Apple, Inc.",
    "00:1F:F3": "Apple, Inc.",
    "00:21:E9": "Apple, Inc.",
    "00:22:41": "Apple, Inc.",
    "00:23:12": "Apple, Inc.",
    "00:23:32": "Apple, Inc.",
    "00:23:6C": "Apple, Inc.",
    "00:23:DF": "Apple, Inc.",
    "00:24:36": "Apple, Inc.",
    "00:25:00": "Apple, Inc.",
    "00:25:4B": "Apple, Inc.",
    "00:25:BC": "Apple, Inc.",
    "00:26:08": "Apple, Inc.",
    "00:26:4A": "Apple, Inc.",
    "00:26:B0": "Apple, Inc.",
    "00:26:BB": "Apple, Inc.",
    "04:0C:CE": "Apple, Inc.",
    "04:15:52": "Apple, Inc.",
    "04:26:65": "Apple, Inc.",
    "04:48:9A": "Apple, Inc.",
    "04:54:53": "Apple, Inc.",
    "08:00:07": "Apple, Inc.",
    "08:66:98": "Apple, Inc.",
    "0C:BC:9F": "Apple, Inc.",
    "10:1C:0C": "Apple, Inc.",
    "10:40:F3": "Apple, Inc.",
    "10:93:E9": "Apple, Inc.",
    "10:9A:DD": "Apple, Inc.",
    "14:10:9F": "Apple, Inc.",
    "18:AF:61": "Apple, Inc.",
    "20:A2:E4": "Apple, Inc.",
    "24:A0:74": "Apple, Inc.",
    "28:CF:E9": "Apple, Inc.",
    "30:90:AB": "Apple, Inc.",
    "34:36:3B": "Apple, Inc.",
    "3C:07:54": "Apple, Inc.",
    "3C:22:FB": "Apple, Inc.",
    "40:B3:95": "Apple, Inc.",
    "44:FB:42": "Apple, Inc.",
    "48:60:5F": "Apple, Inc.",
    "50:BC:96": "Apple, Inc.",
    "58:55:CA": "Apple, Inc.",
    "60:C5:47": "Apple, Inc.",
    "64:20:0C": "Apple, Inc.",
    "70:56:81": "Apple, Inc.",
    "78:4F:43": "Apple, Inc.",
    "7C:D1:C3": "Apple, Inc.",
    "80:49:71": "Apple, Inc.",
    "84:38:35": "Apple, Inc.",
    "88:66:A5": "Apple, Inc.",
    "8C:85:90": "Apple, Inc.",
    "90:B2:1F": "Apple, Inc.",
    "94:94:26": "Apple, Inc.",
    "98:01:A7": "Apple, Inc.",
    "9C:20:7B": "Apple, Inc.",
    "A4:83:E7": "Apple, Inc.",
    "AC:BC:32": "Apple, Inc.",
    "B4:F1:DA": "Apple, Inc.",
    "B8:78:26": "Apple, Inc.",
    "B8:E8:56": "Apple, Inc.",
    "BC:52:B7": "Apple, Inc.",
    "C0:CC:F8": "Apple, Inc.",
    "C8:69:CD": "Apple, Inc.",
    "D0:23:DB": "Apple, Inc.",
    "D4:90:9C": "Apple, Inc.",
    "D8:96:95": "Apple, Inc.",
    "DC:2B:61": "Apple, Inc.",
    "E0:B9:BA": "Apple, Inc.",
    "E4:E4:AB": "Apple, Inc.",
    "F0:18:98": "Apple, Inc.",
    "F4:F1:5A": "Apple, Inc.",
    "F8:FF:C2": "Apple, Inc.",
    "FC:FC:48": "Apple, Inc.",

    # Samsung Electronics
    "00:07:AB": "Samsung Electronics",
    "00:12:47": "Samsung Electronics",
    "00:16:32": "Samsung Electronics",
    "00:1A:8A": "Samsung Electronics",
    "00:21:19": "Samsung Electronics",
    "00:24:54": "Samsung Electronics",
    "08:FC:52": "Samsung Electronics",
    "14:89:FD": "Samsung Electronics",
    "18:22:7E": "Samsung Electronics",
    "20:D5:BF": "Samsung Electronics",
    "24:F5:AA": "Samsung Electronics",
    "28:98:7B": "Samsung Electronics",
    "34:23:BA": "Samsung Electronics",
    "40:0E:85": "Samsung Electronics",
    "44:80:EB": "Samsung Electronics",
    "48:44:F7": "Samsung Electronics",
    "50:C8:E5": "Samsung Electronics",
    "54:92:BE": "Samsung Electronics",
    "5C:0A:5B": "Samsung Electronics",
    "60:A1:0A": "Samsung Electronics",
    "64:1C:B0": "Samsung Electronics",
    "78:47:1D": "Samsung Electronics",
    "84:25:19": "Samsung Electronics",
    "90:18:7C": "Samsung Electronics",
    "98:0D:2E": "Samsung Electronics",
    "A8:06:00": "Samsung Electronics",
    "AC:5F:3E": "Samsung Electronics",
    "B4:79:A7": "Samsung Electronics",
    "B8:5A:73": "Samsung Electronics",
    "BC:44:86": "Samsung Electronics",
    "C4:73:1E": "Samsung Electronics",
    "D0:59:99": "Samsung Electronics",
    "DC:71:44": "Samsung Electronics",
    "E4:E0:C5": "Samsung Electronics",
    "E8:50:8B": "Samsung Electronics",
    "F4:7B:5E": "Samsung Electronics",

    # Intel Corporation (PCs, Laptops, Wi-Fi Chips)
    "00:02:B3": "Intel Corporation",
    "00:03:47": "Intel Corporation",
    "00:04:23": "Intel Corporation",
    "00:0E:0C": "Intel Corporation",
    "00:13:02": "Intel Corporation",
    "00:15:00": "Intel Corporation",
    "00:16:EA": "Intel Corporation",
    "00:19:D1": "Intel Corporation",
    "00:1B:21": "Intel Corporation",
    "00:1E:67": "Intel Corporation",
    "00:21:6A": "Intel Corporation",
    "00:23:14": "Intel Corporation",
    "00:24:D7": "Intel Corporation",
    "34:13:E8": "Intel Corporation",
    "48:51:B7": "Intel Corporation",
    "7C:57:58": "Intel Corporation",
    "80:86:F2": "Intel Corporation",
    "A4:34:D9": "Intel Corporation",
    "AC:E0:10": "Intel Corporation",
    "C8:5B:76": "Intel Corporation",
    "E8:2A:44": "Intel Corporation",
    "F4:6A:DD": "Intel Corporation",

    # TP-Link (Routers, Switches, Smart Home)
    "00:19:E0": "TP-Link Technologies",
    "00:21:27": "TP-Link Technologies",
    "00:23:CD": "TP-Link Technologies",
    "00:25:86": "TP-Link Technologies",
    "14:CC:20": "TP-Link Technologies",
    "1C:3B:F3": "TP-Link Technologies",
    "30:B5:C2": "TP-Link Technologies",
    "50:3A:A0": "TP-Link Technologies",
    "54:AF:97": "TP-Link Technologies",
    "60:E3:27": "TP-Link Technologies",
    "74:DA:38": "TP-Link Technologies",
    "90:F6:52": "TP-Link Technologies",
    "98:48:27": "TP-Link Technologies",
    "B0:4E:26": "TP-Link Technologies",
    "C0:4A:00": "TP-Link Technologies",
    "D8:07:B6": "TP-Link Technologies",
    "E8:48:B8": "TP-Link Technologies",
    "E8:94:F6": "TP-Link Technologies",
    "EC:08:6B": "TP-Link Technologies",

    # Netgear
    "00:09:5B": "Netgear Inc.",
    "00:0F:B5": "Netgear Inc.",
    "00:14:6C": "Netgear Inc.",
    "00:18:4D": "Netgear Inc.",
    "00:1E:2A": "Netgear Inc.",
    "00:24:B2": "Netgear Inc.",
    "20:E5:2A": "Netgear Inc.",
    "44:94:FC": "Netgear Inc.",
    "9C:3D:CF": "Netgear Inc.",
    "B0:7F:B9": "Netgear Inc.",
    "C4:04:15": "Netgear Inc.",

    # Cisco / Linksys
    "00:00:0C": "Cisco Systems",
    "00:01:42": "Cisco Systems",
    "00:01:43": "Cisco Systems",
    "00:04:4D": "Cisco Systems",
    "00:06:53": "Cisco Systems",
    "00:0B:46": "Cisco Systems",
    "00:13:19": "Linksys",
    "00:18:39": "Linksys",
    "00:1C:10": "Cisco-Linksys",
    "00:25:9C": "Cisco Systems",

    # Asus (Routers, Laptops, Motherboards)
    "00:0C:6E": "ASUSTek Computer",
    "00:15:F2": "ASUSTek Computer",
    "00:18:F3": "ASUSTek Computer",
    "00:1E:8C": "ASUSTek Computer",
    "04:D9:F5": "ASUSTek Computer",
    "10:BF:48": "ASUSTek Computer",
    "2C:4D:54": "ASUSTek Computer",
    "38:D5:47": "ASUSTek Computer",
    "40:16:7E": "ASUSTek Computer",
    "60:45:CB": "ASUSTek Computer",
    "AC:9E:17": "ASUSTek Computer",

    # D-Link
    "00:05:5D": "D-Link Corporation",
    "00:0D:88": "D-Link Corporation",
    "00:11:95": "D-Link Corporation",
    "00:17:9A": "D-Link Corporation",
    "00:19:5B": "D-Link Corporation",
    "14:D6:4D": "D-Link Corporation",
    "28:10:7B": "D-Link Corporation",
    "78:54:2E": "D-Link Corporation",

    # Huawei Technologies
    "00:18:82": "Huawei Technologies",
    "00:1E:10": "Huawei Technologies",
    "00:25:9E": "Huawei Technologies",
    "00:46:4B": "Huawei Technologies",
    "04:25:C5": "Huawei Technologies",
    "10:C6:1F": "Huawei Technologies",
    "24:DF:6A": "Huawei Technologies",
    "38:F8:89": "Huawei Technologies",
    "48:46:FB": "Huawei Technologies",
    "70:7B:E8": "Huawei Technologies",
    "AC:E2:15": "Huawei Technologies",
    "CC:96:A0": "Huawei Technologies",
    "F4:55:9C": "Huawei Technologies",

    # Xiaomi Communications
    "00:9E:C8": "Xiaomi Communications",
    "18:59:36": "Xiaomi Communications",
    "28:6C:07": "Xiaomi Communications",
    "34:80:B3": "Xiaomi Communications",
    "50:64:2B": "Xiaomi Communications",
    "64:09:80": "Xiaomi Communications",
    "78:11:DC": "Xiaomi Communications",
    "8C:BE:BE": "Xiaomi Communications",
    "AC:C1:EE": "Xiaomi Communications",
    "D4:97:0B": "Xiaomi Communications",
    "EC:D0:9F": "Xiaomi Communications",

    # Google LLC (Pixel, Nest, Chromecast)
    "00:1A:11": "Google, LLC",
    "3C:5A:B4": "Google, LLC",
    "54:60:09": "Google, LLC",
    "64:16:66": "Google, LLC",
    "94:EB:CD": "Google, LLC",
    "A4:77:33": "Google, LLC",
    "D8:6C:63": "Google, LLC",
    "F4:F5:D8": "Google, LLC",
    "F8:0F:F9": "Google, LLC",

    # Amazon Technologies (Echo, Fire TV, Kindle, Blink, Ring)
    "00:FC:8B": "Amazon Technologies",
    "18:74:2E": "Amazon Technologies",
    "34:D2:70": "Amazon Technologies",
    "40:B4:CD": "Amazon Technologies",
    "44:65:0D": "Amazon Technologies",
    "50:F5:DA": "Amazon Technologies",
    "68:37:E9": "Amazon Technologies",
    "74:C2:46": "Amazon Technologies",
    "AC:63:BE": "Amazon Technologies",
    "F0:81:73": "Amazon Technologies",
    "FC:65:DE": "Amazon Technologies",

    # Raspberry Pi Foundation
    "28:CD:C1": "Raspberry Pi Foundation",
    "B8:27:EB": "Raspberry Pi Foundation",
    "DC:A6:32": "Raspberry Pi Foundation",
    "E4:5F:01": "Raspberry Pi Foundation",

    # Espressif Inc. (ESP32, ESP8266 - Smart Plugs, Smart Bulbs, IoT)
    "18:FE:34": "Espressif Systems",
    "24:0A:C4": "Espressif Systems",
    "24:6F:28": "Espressif Systems",
    "2C:3A:E8": "Espressif Systems",
    "30:AE:A4": "Espressif Systems",
    "3C:61:05": "Espressif Systems",
    "3C:71:BF": "Espressif Systems",
    "4C:11:AE": "Espressif Systems",
    "54:5A:A6": "Espressif Systems",
    "60:01:94": "Espressif Systems",
    "68:C6:3A": "Espressif Systems",
    "84:0D:8E": "Espressif Systems",
    "84:F3:EB": "Espressif Systems",
    "94:B9:7E": "Espressif Systems",
    "A4:CF:12": "Espressif Systems",
    "AC:67:B2": "Espressif Systems",
    "C4:4F:33": "Espressif Systems",
    "D8:A0:1D": "Espressif Systems",

    # Dell Inc.
    "00:14:22": "Dell Inc.",
    "00:18:8B": "Dell Inc.",
    "00:21:70": "Dell Inc.",
    "14:FE:B5": "Dell Inc.",
    "18:03:73": "Dell Inc.",
    "34:17:EB": "Dell Inc.",
    "74:86:7A": "Dell Inc.",
    "B8:2A:72": "Dell Inc.",
    "BC:30:5B": "Dell Inc.",
    "D4:BE:D9": "Dell Inc.",

    # HP Inc. (Computers & Printers)
    "00:01:E6": "HP Inc.",
    "00:08:02": "HP Inc.",
    "00:16:35": "HP Inc.",
    "00:1E:0B": "HP Inc.",
    "10:60:4B": "HP Inc.",
    "30:8D:99": "HP Inc.",
    "48:0F:CF": "HP Inc.",
    "64:51:06": "HP Inc.",
    "9C:8E:99": "HP Inc.",
    "B4:B5:2F": "HP Inc.",

    # Lenovo
    "00:12:FE": "Lenovo",
    "00:21:CC": "Lenovo",
    "38:59:F9": "Lenovo",
    "54:EE:75": "Lenovo",
    "70:72:0D": "Lenovo",
    "80:96:B1": "Lenovo",
    "A4:8C:DB": "Lenovo",

    # Microsoft (Surface, Xbox)
    "00:0D:3A": "Microsoft Corporation",
    "00:12:5A": "Microsoft Corporation",
    "00:17:FA": "Microsoft Corporation",
    "28:18:78": "Microsoft Corporation",
    "30:59:B7": "Microsoft Corporation",
    "50:1A:C5": "Microsoft Corporation",
    "7C:ED:8D": "Microsoft Corporation",
    "DC:B4:C4": "Microsoft Corporation",

    # Sony (PlayStation, Smart TV, Audio)
    "00:04:1F": "Sony Interactive",
    "00:13:15": "Sony Interactive",
    "00:15:C1": "Sony Interactive",
    "00:1D:0D": "Sony Interactive",
    "00:24:8D": "Sony Interactive",
    "70:9E:29": "Sony Interactive",
    "F8:46:1C": "Sony Interactive",
    "FC:0F:E6": "Sony Interactive",

    # LG Electronics (Smart TVs, Appliances)
    "00:1C:62": "LG Electronics",
    "00:1E:75": "LG Electronics",
    "10:F9:6F": "LG Electronics",
    "34:FC:EF": "LG Electronics",
    "58:A2:B5": "LG Electronics",
    "A8:23:FE": "LG Electronics",
    "C8:08:E9": "LG Electronics",

    # Roku Inc.
    "00:0D:4B": "Roku, Inc.",
    "08:05:81": "Roku, Inc.",
    "20:F5:43": "Roku, Inc.",
    "AC:3A:7A": "Roku, Inc.",
    "D8:31:34": "Roku, Inc.",

    # Printers (Canon, Brother, Epson)
    "00:00:85": "Canon Inc.",
    "00:1E:8F": "Canon Inc.",
    "18:0C:AC": "Canon Inc.",
    "00:80:77": "Brother Industries",
    "30:05:5C": "Brother Industries",
    "00:00:48": "Seiko Epson",
    "00:26:AB": "Seiko Epson",

    # Modems / ISPs / Gateways
    "00:00:CA": "Arris Group",
    "00:15:CE": "Arris Group",
    "00:1D:CE": "Arris Group",
    "00:10:7B": "Technicolor",
    "00:19:70": "Technicolor",
    "00:04:0E": "AVM GmbH (FRITZ!Box)",
    "00:1A:4F": "AVM GmbH (FRITZ!Box)",
    "34:81:C4": "AVM GmbH (FRITZ!Box)",
    "00:13:49": "Zyxel Communications",
    "00:19:CB": "Zyxel Communications",
    "04:18:D6": "Ubiquiti Networks",
    "24:A4:3C": "Ubiquiti Networks",
    "80:2A:A8": "Ubiquiti Networks",
    "48:8F:5A": "MikroTik",
    "6C:3B:6B": "MikroTik",
}


def normalize_mac(mac: str) -> str:
    """Normalize MAC address string into standard uppercase XX:XX:XX:XX:XX:XX format."""
    if not mac:
        return ""
    clean = re.sub(r"[^0-9a-fA-F]", "", mac).upper()
    if len(clean) >= 6:
        # Group in pairs of 2
        return ":".join(clean[i : i + 2] for i in range(0, min(len(clean), 12), 2))
    return mac.upper()


def lookup_vendor(mac: str) -> str:
    """
    Looks up the manufacturer/vendor of a given MAC address.
    Checks the local high-speed OUI table first.
    """
    if not mac:
        return "Unknown Vendor"

    norm = normalize_mac(mac)
    # Check 3 octets (e.g. 00:1A:2B)
    prefix_3 = ":".join(norm.split(":")[:3]) if ":" in norm else norm[:6]
    if prefix_3 in OUI_DATABASE:
        return OUI_DATABASE[prefix_3]

    # Special check for randomized / locally administered MACs
    # In Wi-Fi, 2nd least-significant bit of first byte is 1 for private/randomized MACs (x2, x6, xA, xE)
    first_byte = norm.split(":")[0] if ":" in norm else norm[:2]
    try:
        val = int(first_byte, 16)
        if (val & 0x02) != 0:
            return "Private / Randomized MAC (iOS/Android/Windows)"
    except Exception:
        pass

    return "Generic / Unregistered Vendor"
