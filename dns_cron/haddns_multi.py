#!/usr/bin/env python3
"""
HADDNS Multi-Instance - Handshake-Aware Dynamic DNS for Multiple WireGuard Instances
Monitors WireGuard peer handshakes across all instances and updates DNS records dynamically
"""

import subprocess
import json
import time
import os
import sys
import glob
from datetime import datetime

# Configuration
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

def discover_wireguard_interfaces():
    """Discover all WireGuard interfaces"""
    interfaces = []
    
    try:
        # Get all WireGuard interfaces
        output = subprocess.check_output(['wg', 'show', 'interfaces'], 
                                       stderr=subprocess.DEVNULL).decode()
        
        for interface in output.strip().split():
            if interface:
                interfaces.append(interface)
        
        log_message(f"Discovered WireGuard interfaces: {interfaces}")
        return interfaces
    except subprocess.CalledProcessError as e:
        log_message(f"Error discovering interfaces: {e}")
        return []
    except Exception as e:
        log_message(f"Unexpected error discovering interfaces: {e}")
        return []

def load_peer_mappings():
    """Load peer mappings from all instance files"""
    all_mappings = {}
    
    # Look for peer mapping files for all instances
    mapping_files = glob.glob("/etc/wireguard/peer_hostnames_wg*.json")
    
    for mapping_file in mapping_files:
        try:
            with open(mapping_file, 'r') as f:
                mappings = json.load(f)
                all_mappings.update(mappings)
                log_message(f"Loaded mappings from {mapping_file}: {len(mappings)} peers")
        except Exception as e:
            log_message(f"Error loading {mapping_file}: {e}")
    
    # Also check for the main mapping file
    main_mapping_file = "/etc/wireguard/peer_hostnames.json"
    if os.path.exists(main_mapping_file):
        try:
            with open(main_mapping_file, 'r') as f:
                mappings = json.load(f)
                all_mappings.update(mappings)
                log_message(f"Loaded mappings from {main_mapping_file}: {len(mappings)} peers")
        except Exception as e:
            log_message(f"Error loading {main_mapping_file}: {e}")
    
    log_message(f"Total peer mappings loaded: {len(all_mappings)}")
    return all_mappings

def get_all_handshakes(interfaces):
    """Get latest handshakes from all WireGuard interfaces"""
    all_handshakes = {}
    
    for interface in interfaces:
        try:
            output = subprocess.check_output(['wg', 'show', interface, 'latest-handshakes'], 
                                           stderr=subprocess.DEVNULL).decode()
            
            for line in output.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) == 2:
                    pubkey = parts[0].strip()
                    timestamp = int(parts[1].strip())
                    all_handshakes[pubkey] = timestamp
            
            log_message(f"Retrieved handshakes from {interface}: {len([l for l in output.strip().split('\n') if l])} peers")
        except subprocess.CalledProcessError as e:
            log_message(f"Error getting handshakes from {interface}: {e}")
        except Exception as e:
            log_message(f"Unexpected error getting handshakes from {interface}: {e}")
    
    log_message(f"Total handshake records: {len(all_handshakes)}")
    return all_handshakes

def build_host_records(peer_map, handshakes):
    """Build active host records based on recent handshakes"""
    now = int(time.time())
    active_records = []
    active_count = 0
    
    for pubkey, info in peer_map.items():
        if not isinstance(info, dict) or 'ip' not in info or 'hostname' not in info:
            log_message(f"Invalid peer info for {pubkey}: {info}")
            continue
            
        last_handshake = handshakes.get(pubkey, 0)
        
        # Check if peer has recent handshake
        if last_handshake > 0 and (now - last_handshake) < HANDSHAKE_TTL:
            record = f"{info['ip']}\t{info['hostname']}"
            active_records.append(record)
            active_count += 1
            log_message(f"Active peer: {info['hostname']} ({info['ip']}) - last handshake: {now - last_handshake}s ago")
        else:
            if last_handshake > 0:
                log_message(f"Inactive peer: {info.get('hostname', pubkey[:8])} - last handshake: {now - last_handshake}s ago")
            else:
                log_message(f"No handshake data for peer: {info.get('hostname', pubkey[:8])}")
    
    log_message(f"Active peers: {active_count}")
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
            f.write("# WireGuard HADDNS Multi-Instance - Handshake-Aware Dynamic DNS\n")
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
    log_message("Starting HADDNS multi-instance handshake monitoring")
    
    # Discover all WireGuard interfaces
    interfaces = discover_wireguard_interfaces()
    if not interfaces:
        log_message("No WireGuard interfaces found - exiting")
        return
    
    # Load peer mappings
    peer_map = load_peer_mappings()
    if not peer_map:
        log_message("No peer mappings found - exiting")
        return
    
    # Get handshakes from all interfaces
    handshakes = get_all_handshakes(interfaces)
    if not handshakes:
        log_message("No handshake data available - exiting")
        return
    
    # Build active records
    active_records = build_host_records(peer_map, handshakes)
    
    # Update hosts file
    if update_hosts_file(active_records):
        # Reload dnsmasq
        reload_dnsmasq()
        log_message(f"HADDNS multi-instance update completed - {len(active_records)} active peers")
    else:
        log_message("HADDNS multi-instance update failed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("HADDNS interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_message(f"HADDNS error: {e}")
        sys.exit(1)
