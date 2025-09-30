import subprocess
import os


def get_coredns_ip():
    """
    Get the IP address of the CoreDNS container.
    Returns the container IP or falls back to a default.
    """
    try:
        # Try to get the CoreDNS container IP
        result = subprocess.run(
            ['docker', 'inspect', 'wireguard-coredns', '--format={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Fallback to default IP if container not found or error
    return '172.19.0.3'


def get_dnsmasq_ip():
    """
    Get the IP address of the dnsmasq container.
    Returns the container IP or falls back to a default.
    """
    try:
        # Try to get the dnsmasq container IP
        result = subprocess.run(
            ['docker', 'inspect', 'wireguard-webadmin-dns', '--format={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Fallback to default IP if container not found or error
    return '172.19.0.2'


def get_optimal_dns_config():
    """
    Get the optimal DNS configuration for new instances.
    Returns a tuple of (primary_dns, secondary_dns)
    """
    coredns_ip = get_coredns_ip()
    return f"{coredns_ip}:5354", '8.8.8.8'
