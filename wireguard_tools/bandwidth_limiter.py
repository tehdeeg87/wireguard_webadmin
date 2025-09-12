#!/usr/bin/env python3
"""
Bandwidth Limiting Script for WireGuard Instances
This script generates traffic control (tc) commands to limit bandwidth for WireGuard interfaces.
"""

import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def generate_bandwidth_limiting_script(instance_id, bandwidth_mbps=50):
    """
    Generate tc commands to limit bandwidth for a WireGuard interface.
    
    Args:
        instance_id (int): WireGuard instance ID
        bandwidth_mbps (int): Bandwidth limit in Mbps
    
    Returns:
        str: tc commands for bandwidth limiting
    """
    interface = f"wg{instance_id}"
    
    # Convert Mbps to bits per second for tc
    bandwidth_bps = bandwidth_mbps * 1000000  # Convert Mbps to bps
    
    # Generate tc commands
    script_lines = [
        f"# Bandwidth limiting for {interface}",
        f"# Limit: {bandwidth_mbps} Mbps",
        "",
        f"# Remove existing qdisc if it exists",
        f"tc qdisc del dev {interface} root 2>/dev/null || true",
        "",
        f"# Add HTB qdisc as root",
        f"tc qdisc add dev {interface} root handle 1: htb default 30",
        "",
        f"# Add root class with bandwidth limit",
        f"tc class add dev {interface} parent 1: classid 1:1 htb rate {bandwidth_mbps}mbit",
        "",
        f"# Add default class for all traffic",
        f"tc class add dev {interface} parent 1:1 classid 1:30 htb rate {bandwidth_mbps}mbit ceil {bandwidth_mbps}mbit",
        "",
        f"# Add filter to direct all traffic to the default class",
        f"tc filter add dev {interface} parent 1: protocol ip prio 1 u32 match ip src 0.0.0.0/0 flowid 1:30",
        "",
        f"# Optional: Add separate classes for upload and download if needed",
        f"# Upload class (traffic from server to client)",
        f"tc class add dev {interface} parent 1:1 classid 1:10 htb rate {bandwidth_mbps//2}mbit ceil {bandwidth_mbps}mbit",
        "",
        f"# Download class (traffic from client to server)", 
        f"tc class add dev {interface} parent 1:1 classid 1:20 htb rate {bandwidth_mbps//2}mbit ceil {bandwidth_mbps}mbit",
        "",
        f"# Upload filter (outgoing traffic)",
        f"tc filter add dev {interface} parent 1: protocol ip prio 2 u32 match ip dst 0.0.0.0/0 flowid 1:10",
        "",
        f"# Download filter (incoming traffic)",
        f"tc filter add dev {interface} parent 1: protocol ip prio 3 u32 match ip src 0.0.0.0/0 flowid 1:20",
        "",
        f"echo 'Bandwidth limiting applied to {interface}: {bandwidth_mbps} Mbps'"
    ]
    
    return "\n".join(script_lines)

def generate_bandwidth_cleanup_script(instance_id):
    """
    Generate script to remove bandwidth limiting from a WireGuard interface.
    
    Args:
        instance_id (int): WireGuard instance ID
    
    Returns:
        str: tc commands for cleanup
    """
    interface = f"wg{instance_id}"
    
    script_lines = [
        f"# Remove bandwidth limiting from {interface}",
        f"tc qdisc del dev {interface} root 2>/dev/null || true",
        f"echo 'Bandwidth limiting removed from {interface}'"
    ]
    
    return "\n".join(script_lines)

def apply_bandwidth_limiting(instance_id, bandwidth_mbps=50):
    """
    Apply bandwidth limiting to a WireGuard interface.
    
    Args:
        instance_id (int): WireGuard instance ID
        bandwidth_mbps (int): Bandwidth limit in Mbps
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        script_content = generate_bandwidth_limiting_script(instance_id, bandwidth_mbps)
        
        # Write script to temporary file
        script_path = f"/tmp/wg{instance_id}_bandwidth.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        # Execute the script
        result = subprocess.run(['bash', script_path], 
                              capture_output=True, text=True, check=True)
        
        logger.info(f"Bandwidth limiting applied to wg{instance_id}: {bandwidth_mbps} Mbps")
        logger.debug(f"Script output: {result.stdout}")
        
        # Clean up temporary file
        os.remove(script_path)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to apply bandwidth limiting to wg{instance_id}: {e}")
        logger.error(f"Script stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error applying bandwidth limiting to wg{instance_id}: {e}")
        return False

def remove_bandwidth_limiting(instance_id):
    """
    Remove bandwidth limiting from a WireGuard interface.
    
    Args:
        instance_id (int): WireGuard instance ID
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        script_content = generate_bandwidth_cleanup_script(instance_id)
        
        # Write script to temporary file
        script_path = f"/tmp/wg{instance_id}_bandwidth_cleanup.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        # Execute the script
        result = subprocess.run(['bash', script_path], 
                              capture_output=True, text=True, check=True)
        
        logger.info(f"Bandwidth limiting removed from wg{instance_id}")
        logger.debug(f"Script output: {result.stdout}")
        
        # Clean up temporary file
        os.remove(script_path)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to remove bandwidth limiting from wg{instance_id}: {e}")
        logger.error(f"Script stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error removing bandwidth limiting from wg{instance_id}: {e}")
        return False

def check_bandwidth_limiting_status(instance_id):
    """
    Check if bandwidth limiting is currently applied to a WireGuard interface.
    
    Args:
        instance_id (int): WireGuard instance ID
    
    Returns:
        dict: Status information about bandwidth limiting
    """
    interface = f"wg{instance_id}"
    
    try:
        # Check if tc qdisc exists
        result = subprocess.run(['tc', 'qdisc', 'show', 'dev', interface], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and 'htb' in result.stdout:
            # Parse bandwidth information
            lines = result.stdout.strip().split('\n')
            bandwidth_info = []
            
            for line in lines:
                if 'htb' in line and 'rate' in line:
                    # Extract rate information
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'rate' and i + 1 < len(parts):
                            rate = parts[i + 1]
                            bandwidth_info.append(rate)
                            break
            
            return {
                'enabled': True,
                'interface': interface,
                'bandwidth_info': bandwidth_info,
                'raw_output': result.stdout
            }
        else:
            return {
                'enabled': False,
                'interface': interface,
                'bandwidth_info': [],
                'raw_output': result.stdout
            }
            
    except Exception as e:
        logger.error(f"Error checking bandwidth limiting status for wg{instance_id}: {e}")
        return {
            'enabled': False,
            'interface': interface,
            'error': str(e)
        }
