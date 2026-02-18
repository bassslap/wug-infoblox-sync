"""
IP address utilities for calculating network space, availability, and utilization.
"""

import ipaddress
from typing import Any


def parse_network(network_cidr: str) -> ipaddress.IPv4Network:
    """Parse CIDR notation into IPv4Network object."""
    return ipaddress.IPv4Network(network_cidr, strict=False)


def get_usable_ips(network_cidr: str) -> list[str]:
    """
    Get list of usable IP addresses in a network (excluding network and broadcast).
    
    Args:
        network_cidr: Network in CIDR notation (e.g., "192.168.1.0/24")
        
    Returns:
        List of usable IP addresses as strings
    """
    network = parse_network(network_cidr)
    # Exclude network address and broadcast address
    return [str(ip) for ip in list(network.hosts())]


def get_total_ips(network_cidr: str) -> int:
    """
    Get total number of usable IP addresses in a network.
    
    Args:
        network_cidr: Network in CIDR notation
        
    Returns:
        Number of usable IPs
    """
    network = parse_network(network_cidr)
    return network.num_addresses - 2  # Exclude network and broadcast


def calculate_utilization(
    network_cidr: str, 
    used_ips: list[str]
) -> dict[str, Any]:
    """
    Calculate IP utilization for a network.
    
    Args:
        network_cidr: Network in CIDR notation
        used_ips: List of IP addresses currently in use
        
    Returns:
        Dictionary with utilization statistics
    """
    network = parse_network(network_cidr)
    total_ips = network.num_addresses - 2  # Exclude network and broadcast
    
    # Filter used IPs to only those in this network
    network_obj = ipaddress.IPv4Network(network_cidr, strict=False)
    valid_used_ips = [
        ip for ip in used_ips 
        if ipaddress.IPv4Address(ip) in network_obj
    ]
    
    used_count = len(valid_used_ips)
    available_count = total_ips - used_count
    utilization_percent = (used_count / total_ips * 100) if total_ips > 0 else 0
    
    return {
        "network": network_cidr,
        "total_ips": total_ips,
        "used_ips": used_count,
        "available_ips": available_count,
        "utilization_percent": round(utilization_percent, 2),
        "network_address": str(network.network_address),
        "broadcast_address": str(network.broadcast_address),
        "netmask": str(network.netmask),
        "prefix_length": network.prefixlen,
    }


def get_available_ips(
    network_cidr: str, 
    used_ips: list[str],
    limit: int | None = None
) -> list[str]:
    """
    Get list of available IP addresses in a network.
    
    Args:
        network_cidr: Network in CIDR notation
        used_ips: List of IP addresses currently in use
        limit: Maximum number of IPs to return (optional)
        
    Returns:
        List of available IP addresses
    """
    usable_ips = set(get_usable_ips(network_cidr))
    used_set = set(used_ips)
    available = sorted(usable_ips - used_set, key=lambda ip: ipaddress.IPv4Address(ip))
    
    if limit:
        return available[:limit]
    return available


def get_next_available_ip(
    network_cidr: str, 
    used_ips: list[str]
) -> str | None:
    """
    Get the next available IP address in a network.
    
    Args:
        network_cidr: Network in CIDR notation
        used_ips: List of IP addresses currently in use
        
    Returns:
        Next available IP address or None if network is full
    """
    available = get_available_ips(network_cidr, used_ips, limit=1)
    return available[0] if available else None


def ip_in_network(ip_address: str, network_cidr: str) -> bool:
    """
    Check if an IP address belongs to a network.
    
    Args:
        ip_address: IP address to check
        network_cidr: Network in CIDR notation
        
    Returns:
        True if IP is in network, False otherwise
    """
    try:
        ip = ipaddress.IPv4Address(ip_address)
        network = parse_network(network_cidr)
        return ip in network
    except ValueError:
        return False


def validate_ip(ip_address: str) -> bool:
    """
    Validate if a string is a valid IPv4 address.
    
    Args:
        ip_address: IP address string to validate
        
    Returns:
        True if valid IPv4 address, False otherwise
    """
    try:
        ipaddress.IPv4Address(ip_address)
        return True
    except ValueError:
        return False


def validate_network(network_cidr: str) -> bool:
    """
    Validate if a string is valid CIDR notation.
    
    Args:
        network_cidr: Network in CIDR notation
        
    Returns:
        True if valid CIDR, False otherwise
    """
    try:
        ipaddress.IPv4Network(network_cidr, strict=False)
        return True
    except ValueError:
        return False
