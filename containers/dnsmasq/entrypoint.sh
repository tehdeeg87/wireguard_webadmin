#!/bin/bash
CONFIG_FILE="/etc/dnsmasq/wireguard_webadmin_dns.conf"
HOSTS_DIR="/etc/dnsmasq/hosts"
DEFAULT_CONFIG_CONTENT="
no-dhcp-interface=
server=1.1.1.1
server=1.0.0.1

listen-address=0.0.0.0
bind-interfaces

# Per-instance hosts files
addn-hosts=/etc/dnsmasq/hosts/peers_wg0.hosts
addn-hosts=/etc/dnsmasq/hosts/peers_wg1.hosts
addn-hosts=/etc/dnsmasq/hosts/peers_wg2.hosts
addn-hosts=/etc/dnsmasq/hosts/peers_wg3.hosts
addn-hosts=/etc/dnsmasq/hosts/peers_wg4.hosts
"

create_default_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Config file not found, creating a new one..."
        echo "$DEFAULT_CONFIG_CONTENT" > "$CONFIG_FILE"
    fi
}

create_hosts_files() {
    # Create hosts directory if it doesn't exist
    mkdir -p "$HOSTS_DIR"
    
    # Create empty hosts files for each instance if they don't exist
    for i in {0..4}; do
        hosts_file="$HOSTS_DIR/peers_wg${i}.hosts"
        if [ ! -f "$hosts_file" ]; then
            echo "# Hosts file for WireGuard instance wg${i}" > "$hosts_file"
            echo "# Generated automatically - do not edit manually" >> "$hosts_file"
            echo "" >> "$hosts_file"
        fi
    done
}

start_dnsmasq() {
    dnsmasq -C "$CONFIG_FILE" &
    # Watch both config file and hosts directory for changes
    while inotifywait -e modify,create,delete "$CONFIG_FILE" "$HOSTS_DIR"; do
        echo "Configuration or hosts files changed, reloading dnsmasq..."
        pkill dnsmasq
        sleep 2
        dnsmasq -C "$CONFIG_FILE" &
    done
}


handle_sigint() {
    echo "SIGINT received. Stopping inotifywait and dnsmasq..."
    pkill inotifywait
    pkill dnsmasq
    exit 0
}

trap handle_sigint SIGINT

create_default_config
create_hosts_files
start_dnsmasq
