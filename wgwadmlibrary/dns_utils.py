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
            ip = result.stdout.strip()
            # Validate that it's a proper IP address
            if ip and '.' in ip and len(ip.split('.')) == 4:
                return ip
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Fallback: try to get the host IP or use localhost
    try:
        # Try to get the host's IP in the Docker network
        result = subprocess.run(
            ['docker', 'inspect', 'wireguard-webadmin', '--format={{range .NetworkSettings.Networks}}{{.Gateway}}{{end}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            gateway = result.stdout.strip()
            if gateway and '.' in gateway:
                return gateway
    except:
        pass
    
    # Final fallback - use the server's external IP or localhost
    return '127.0.0.1'


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
    # Try to get CoreDNS container IP first
    coredns_ip = get_coredns_ip()
    
    # If we got a valid IP, use it with port 5354
    if coredns_ip and coredns_ip != '127.0.0.1':
        return f"{coredns_ip}:5354", '8.8.8.8'
    
    # Fallback: use the server's external IP
    try:
        # Try to get the server's external IP from environment or network interface
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        external_ip = s.getsockname()[0]
        s.close()
        return f"{external_ip}:5354", '8.8.8.8'
    except:
        # Final fallback: use localhost (for testing)
        return "127.0.0.1:5354", '8.8.8.8'
