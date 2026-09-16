import ipaddress


def classify_ip_scope(ip: str) -> str:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "unknown"
    if addr.is_loopback:
        return "loopback"
    if addr.is_private:
        return "private"
    if addr.is_link_local or addr.is_reserved:
        return "reserved"
    return "public"
