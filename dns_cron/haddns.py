#!/usr/bin/env python3
"""
HADDNS - Handshake-Aware Dynamic DNS
Monitors WireGuard peer handshakes and updates DNS records dynamically
"""

import subprocess
import json
import time
import os
import sys
from datetime import datetime

# Configuration
WG_INTERFACE = "wg0"
PEER_MAP = "/etc/wireguard/peer_hostnames.json"  # mounted from main container
HOSTS_FILE = "/shared_hosts/hosts"
HANDSHAKE_TTL = 300  # seconds (5 min)
LOG_FILE = "/var/log/haddns.log"

def log_message(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    # Print to stdout (for cron logs)
    print(log_entry.strip())
    
    # Also write to log file
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")

def load_peer_mapping():
    """Load peer mapping from JSON file"""
    if not os.path.exists(PEER_MAP):
        log_message(f"Missing mapping file: {PEER_MAP}")
        return {}
    
    try:
        with open(PEER_MAP, 'r') as f:
            mapping = json.load(f)
        log_message(f"Loaded {len(mapping)} peer mappings")
        return mapping
    except Exception as e:
        log_message(f"Error loading peer mapping: {e}")
        return {}

def get_handshakes():
    """Get latest handshakes from WireGuard interface"""
    try:
        output = subprocess.check_output(['wg', 'show', WG_INTERFACE, 'latest-handshakes'], 
                                       stderr=subprocess.DEVNULL).decode()
        handshakes = {}
        
        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) == 2:
                pubkey = parts[0].strip()
                timestamp = int(parts[1].strip())
                handshakes[pubkey] = timestamp
        
        log_message(f"Retrieved {len(handshakes)} handshake records")
        return handshakes
    except subprocess.CalledProcessError as e:
        log_message(f"Error getting handshakes: {e}")
        return {}
    except Exception as e:
        log_message(f"Unexpected error getting handshakes: {e}")
        return {}

def build_host_records(peer_map, handshakes):
    """Build active host records based on recent handshakes"""
    now = int(time.time())
    active_records = []
    
    for pubkey, info in peer_map.items():
        if not isinstance(info, dict) or 'ip' not in info or 'hostname' not in info:
            log_message(f"Invalid peer info for {pubkey}: {info}")
            continue
            
        last_handshake = handshakes.get(pubkey, 0)
        
        # Check if peer has recent handshake
        if last_handshake > 0 and (now - last_handshake) < HANDSHAKE_TTL:
            record = f"{info['ip']}\t{info['hostname']}"
            active_records.append(record)
            log_message(f"Active peer: {info['hostname']} ({info['ip']}) - last handshake: {now - last_handshake}s ago")
        else:
            if last_handshake > 0:
                log_message(f"Inactive peer: {info.get('hostname', pubkey[:8])} - last handshake: {now - last_handshake}s ago")
            else:
                log_message(f"No handshake data for peer: {info.get('hostname', pubkey[:8])}")
    
    return active_records

def update_hosts_file(records):
    """Update the shared hosts file"""
    try:
        # Create shared hosts directory if it doesn't exist
        hosts_dir = os.path.dirname(HOSTS_FILE)
        os.makedirs(hosts_dir, exist_ok=True)
        
        # Create backup of current hosts file
        if os.path.exists(HOSTS_FILE):
            backup_file = f"{HOSTS_FILE}.backup.{int(time.time())}"
            os.rename(HOSTS_FILE, backup_file)
            log_message(f"Created backup: {backup_file}")
        
        # Write new hosts file
        with open(HOSTS_FILE, 'w') as f:
            f.write("# WireGuard HADDNS - Handshake-Aware Dynamic DNS\n")
            f.write(f"# Generated automatically - do not edit manually\n")
            f.write(f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Active peers: {len(records)}\n\n")
            
            for record in records:
                f.write(f"{record}\n")
        
        log_message(f"Updated hosts file with {len(records)} active peer records")
        return True
        
    except Exception as e:
        log_message(f"Error updating hosts file: {e}")
        return False

def reload_dnsmasq():
    """Reload dnsmasq to pick up new hosts file"""
    # Note: dnsmasq will automatically pick up changes to the hosts file
    # No need to send HUP signal in this containerized environment
    log_message("dnsmasq will automatically pick up hosts file changes")
    return True

def main():
    """Main HADDNS function"""
    log_message("Starting HADDNS handshake monitoring")
    
    # Load peer mapping
    peer_map = load_peer_mapping()
    if not peer_map:
        log_message("No peer mapping found - exiting")
        return
    
    # Get current handshakes
    handshakes = get_handshakes()
    if not handshakes:
        log_message("No handshake data available - exiting")
        return
    
    # Build active records
    active_records = build_host_records(peer_map, handshakes)
    
    # Update hosts file
    if update_hosts_file(active_records):
        # Reload dnsmasq
        reload_dnsmasq()
        log_message(f"HADDNS update completed - {len(active_records)} active peers")
    else:
        log_message("HADDNS update failed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("HADDNS interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_message(f"HADDNS error: {e}")
        sys.exit(1)
