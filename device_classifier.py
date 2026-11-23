"""
Device Classifier & Fingerprinting Engine
Determines device roles, friendly names, estimated operating system,
and appropriate visual icon based on MAC OUI, hostnames, open ports, and network roles.
"""

from typing import Dict, Any, List


def classify_device(
    ip: str,
    mac: str,
    vendor: str,
    hostname: str,
    open_ports: List[int],
    is_gateway: bool = False,
    is_local_machine: bool = False,
) -> Dict[str, Any]:
    """
    Classify a network host into a specific device type and friendly name.
    """
    vendor_lower = (vendor or "").lower()
    host_lower = (hostname or "").lower()
    ports_set = set(open_ports or [])

    # Default fallbacks
    device_type = "Network Device"
    friendly_name = hostname if hostname and not hostname.startswith("ip-") else f"Device ({ip})"
    os_estimate = "Unknown OS"
    icon = "device"
    badge_color = "secondary"

    # 1. Gateway / Modem / Router (Top priority)
    if is_gateway:
        device_type = "Modem / Gateway Router"
        icon = "router"
        badge_color = "warning"
        os_estimate = "Embedded Linux / RouterOS"
        if "tp-link" in vendor_lower:
            friendly_name = "TP-Link Modem / Router"
        elif "netgear" in vendor_lower:
            friendly_name = "Netgear Modem / Gateway"
        elif "fritz" in vendor_lower or "avm" in vendor_lower:
            friendly_name = "AVM FRITZ!Box Gateway"
        elif "cisco" in vendor_lower or "linksys" in vendor_lower:
            friendly_name = "Cisco / Linksys Gateway"
        elif "asus" in vendor_lower:
            friendly_name = "ASUS Wi-Fi Router"
        elif "huawei" in vendor_lower:
            friendly_name = "Huawei Broadband Gateway"
        elif "technicolor" in vendor_lower or "arris" in vendor_lower:
            friendly_name = "ISP Cable/DSL Modem"
        else:
            friendly_name = f"Default Gateway ({ip})"
        return {
            "device_type": device_type,
            "friendly_name": friendly_name,
            "os_estimate": os_estimate,
            "icon": icon,
            "badge_color": badge_color,
            "is_gateway": True,
        }

    # 2. Local Machine (the computer running this script)
    if is_local_machine:
        device_type = "Host Computer (This PC)"
        icon = "desktop"
        badge_color = "primary"
        friendly_name = hostname if hostname else "My Computer"
        os_estimate = "Current Host OS"

    # 3. Apple Ecosystem (iPhone, iPad, Mac)
    elif "apple" in vendor_lower or 62078 in ports_set or "iphone" in host_lower or "ipad" in host_lower:
        badge_color = "apple"
        if "iphone" in host_lower or (62078 in ports_set and "ipad" not in host_lower):
            device_type = "Apple iPhone"
            friendly_name = hostname if "iphone" in host_lower else "Apple iPhone"
            os_estimate = "iOS"
            icon = "smartphone"
        elif "ipad" in host_lower:
            device_type = "Apple iPad"
            friendly_name = hostname if "ipad" in host_lower else "Apple iPad"
            os_estimate = "iPadOS"
            icon = "tablet"
        elif "mac" in host_lower or "macbook" in host_lower or 548 in ports_set:
            device_type = "Apple Mac / MacBook"
            friendly_name = hostname if hostname else "Apple MacBook"
            os_estimate = "macOS"
            icon = "laptop"
        elif "watch" in host_lower:
            device_type = "Apple Watch"
            friendly_name = hostname if hostname else "Apple Watch"
            os_estimate = "watchOS"
            icon = "smartwatch"
        elif "apple-tv" in host_lower or "appletv" in host_lower:
            device_type = "Apple TV"
            friendly_name = hostname if hostname else "Apple TV"
            os_estimate = "tvOS"
            icon = "tv"
        else:
            device_type = "Apple Device (iPhone/Mac)"
            friendly_name = hostname if hostname else "Apple Device"
            os_estimate = "iOS / macOS"
            icon = "smartphone"

    # 4. Android & Mobile Phones
    elif any(brand in vendor_lower for brand in ["samsung", "xiaomi", "huawei", "oneplus", "oppo", "vivo", "realme", "google"]) and not any(tv in host_lower for tv in ["tv", "bravia"]):
        icon = "smartphone"
        badge_color = "success"
        os_estimate = "Android"
        if "samsung" in vendor_lower:
            device_type = "Samsung Galaxy Smartphone"
            friendly_name = hostname if hostname else "Samsung Galaxy"
        elif "xiaomi" in vendor_lower:
            device_type = "Xiaomi Smartphone"
            friendly_name = hostname if hostname else "Xiaomi Phone"
        elif "google" in vendor_lower:
            if "pixel" in host_lower or 8008 not in ports_set:
                device_type = "Google Pixel Smartphone"
                friendly_name = hostname if hostname else "Google Pixel"
            else:
                device_type = "Google Cast / Nest"
                friendly_name = "Google Nest / Chromecast"
                icon = "iot"
        else:
            device_type = "Android Smartphone"
            friendly_name = hostname if hostname else f"{vendor.split()[0]} Phone"

    # 5. Windows PC / Laptops
    elif (
        any(pc_vendor in vendor_lower for pc_vendor in ["dell", "hp", "lenovo", "intel", "microsoft", "acer", "asus"])
        or 3389 in ports_set  # RDP
        or 445 in ports_set   # SMB
        or 139 in ports_set
        or "desktop-" in host_lower
        or "laptop-" in host_lower
        or "-pc" in host_lower
    ):
        badge_color = "info"
        if 3389 in ports_set or "desktop-" in host_lower or "laptop-" in host_lower:
            os_estimate = "Windows 10 / 11"
        else:
            os_estimate = "Windows / Linux"

        if "laptop" in host_lower or "thinkpad" in host_lower or "xps" in host_lower:
            device_type = "Laptop PC"
            icon = "laptop"
        else:
            device_type = "Desktop / Laptop PC"
            icon = "desktop"

        if hostname:
            friendly_name = hostname
        else:
            vendor_name = vendor.split()[0] if vendor and "generic" not in vendor_lower else "Personal"
            friendly_name = f"{vendor_name} PC ({ip})"

    # 6. Smart TVs & Streaming Devices
    elif (
        any(tv_brand in vendor_lower for tv_brand in ["sony", "lg", "roku", "vizio"])
        or any(tv_kw in host_lower for tv_kw in ["tv", "bravia", "webos", "roku", "chromecast", "firetv", "shield"])
        or 8008 in ports_set  # Cast API
        or 8009 in ports_set
    ):
        device_type = "Smart TV / Streaming Box"
        icon = "tv"
        badge_color = "purple"
        os_estimate = "Smart TV OS (Android TV / Tizen / webOS / Roku)"
        if "roku" in host_lower or "roku" in vendor_lower:
            friendly_name = "Roku Streaming Player"
        elif "lg" in vendor_lower or "webos" in host_lower:
            friendly_name = "LG Smart TV"
        elif "samsung" in vendor_lower or "tizen" in host_lower:
            friendly_name = "Samsung Smart TV"
        elif "sony" in vendor_lower or "bravia" in host_lower:
            friendly_name = "Sony BRAVIA TV"
        elif "chromecast" in host_lower:
            friendly_name = "Google Chromecast"
        else:
            friendly_name = hostname if hostname else "Smart TV"

    # 7. Network Printers
    elif (
        any(p in vendor_lower for p in ["canon", "epson", "brother", "lexmark", "xerox"])
        or any(p in host_lower for p in ["printer", "laserjet", "deskjet", "epson", "brother"])
        or 9100 in ports_set  # JetDirect
        or 631 in ports_set   # IPP
        or 515 in ports_set   # LPD
    ):
        device_type = "Network Printer"
        icon = "printer"
        badge_color = "secondary"
        os_estimate = "Embedded Printer Firmware"
        friendly_name = hostname if hostname else f"{vendor.split()[0]} Printer"

    # 8. Smart Home & IoT Sensors
    elif (
        any(iot in vendor_lower for iot in ["espressif", "tuya", "philips", "sonoff", "shelly", "belkin", "amazon"])
        or "raspberry" in vendor_lower
        or "echo" in host_lower
        or "nest" in host_lower
        or "alexa" in host_lower
    ):
        badge_color = "warning"
        if "raspberry" in vendor_lower:
            device_type = "Raspberry Pi (SBC / Server)"
            icon = "server"
            os_estimate = "Raspberry Pi OS / Linux"
            friendly_name = hostname if hostname else "Raspberry Pi"
        elif "amazon" in vendor_lower or "echo" in host_lower:
            device_type = "Amazon Echo / Smart Speaker"
            icon = "speaker"
            os_estimate = "Fire OS / Linux"
            friendly_name = hostname if hostname else "Amazon Echo"
        elif "espressif" in vendor_lower:
            device_type = "Smart Home IoT Sensor (ESP32/ESP8266)"
            icon = "iot"
            os_estimate = "FreeRTOS / ESP-IDF"
            friendly_name = hostname if hostname else "ESP32 IoT Node"
        else:
            device_type = "Smart Home IoT Device"
            icon = "iot"
            os_estimate = "Embedded IoT Firmware"
            friendly_name = hostname if hostname else "Smart Device"

    # 9. Gaming Consoles
    elif (
        "playstation" in host_lower
        or "xbox" in host_lower
        or "nintendo" in host_lower
        or "nintendo" in vendor_lower
    ):
        device_type = "Gaming Console"
        icon = "gaming"
        badge_color = "purple"
        os_estimate = "Console OS"
        if "playstation" in host_lower or "sony" in vendor_lower:
            friendly_name = "PlayStation Console"
        elif "xbox" in host_lower or "microsoft" in vendor_lower:
            friendly_name = "Xbox Console"
        else:
            friendly_name = "Nintendo Switch"

    # 10. Randomized / Private MAC mobile devices
    elif "randomized" in vendor_lower:
        device_type = "Mobile Device (Private MAC)"
        friendly_name = hostname if hostname else f"Mobile Device ({ip})"
        icon = "smartphone"
        os_estimate = "iOS 14+ / Android 10+ (MAC Randomized)"
        badge_color = "secondary"

    return {
        "device_type": device_type,
        "friendly_name": friendly_name,
        "os_estimate": os_estimate,
        "icon": icon,
        "badge_color": badge_color,
        "is_gateway": False,
    }
