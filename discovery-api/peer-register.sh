#!/bin/bash

# WireGuard Peer Auto-Registration Script
# This script registers the current peer with the discovery API

set -e

# Configuration
DISCOVERY_URL="${DISCOVERY_URL:-http://discovery-api:5000}"
HOSTNAME="${PEER_HOSTNAME:-$(hostname)}"
WG_INTERFACE="${WG_INTERFACE:-wg0}"
REGISTER_INTERVAL="${REGISTER_INTERVAL:-300}"  # 5 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_info() {
    log "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

get_wireguard_ip() {
    # Try to get IP from WireGuard interface
    local wg_ip
    wg_ip=$(ip -4 addr show "$WG_INTERFACE" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
    
    if [ -n "$wg_ip" ]; then
        echo "$wg_ip"
        return 0
    fi
    
    # Fallback: try to get any non-loopback IP
    wg_ip=$(ip -4 addr show | grep -oP '(?<=inet\s)10\.\d+\.\d+\.\d+' | head -1)
    
    if [ -n "$wg_ip" ]; then
        echo "$wg_ip"
        return 0
    fi
    
    return 1
}

register_peer() {
    local wg_ip
    wg_ip=$(get_wireguard_ip)
    
    if [ -z "$wg_ip" ]; then
        log_warn "Could not determine WireGuard IP address"
        return 1
    fi
    
    log_info "Registering peer: $HOSTNAME -> $wg_ip"
    
    local response
    response=$(curl -s -X POST "$DISCOVERY_URL/register" \
        -H "Content-Type: application/json" \
        -d "{\"hostname\":\"$HOSTNAME\",\"ip\":\"$wg_ip\"}" \
        --connect-timeout 10 \
        --max-time 30 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$response" | grep -q '"status":"ok"'; then
        log_info "Successfully registered with discovery API"
        return 0
    else
        log_error "Failed to register with discovery API: $response"
        return 1
    fi
}

resolve_peer() {
    local hostname="$1"
    
    if [ -z "$hostname" ]; then
        log_error "No hostname provided for resolution"
        return 1
    fi
    
    log_info "Resolving hostname: $hostname"
    
    local response
    response=$(curl -s "$DISCOVERY_URL/resolve/$hostname" \
        --connect-timeout 10 \
        --max-time 30 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        local ip
        ip=$(echo "$response" | grep -oP '"ip":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$ip" ]; then
            log_info "Resolved $hostname -> $ip"
            echo "$ip"
            return 0
        fi
    fi
    
    log_error "Failed to resolve hostname: $hostname"
    return 1
}

list_peers() {
    log_info "Listing all registered peers"
    
    local response
    response=$(curl -s "$DISCOVERY_URL/list" \
        --connect-timeout 10 \
        --max-time 30 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "$response" | grep -oP '"hostname":"[^"]*"' | cut -d'"' -f4 | while read -r hostname; do
            local ip
            ip=$(echo "$response" | grep -A1 "\"hostname\":\"$hostname\"" | grep -oP '"ip":"[^"]*"' | cut -d'"' -f4)
            log_info "  $hostname -> $ip"
        done
        return 0
    else
        log_error "Failed to list peers"
        return 1
    fi
}

# Main function
main() {
    local command="${1:-register}"
    
    case "$command" in
        "register")
            log_info "Starting peer registration daemon"
            log_info "Discovery URL: $DISCOVERY_URL"
            log_info "Hostname: $HOSTNAME"
            log_info "WireGuard Interface: $WG_INTERFACE"
            log_info "Registration Interval: ${REGISTER_INTERVAL}s"
            
            # Initial registration
            register_peer
            
            # Continuous registration loop
            while true; do
                sleep "$REGISTER_INTERVAL"
                register_peer
            done
            ;;
        "resolve")
            resolve_peer "$2"
            ;;
        "list")
            list_peers
            ;;
        "once")
            register_peer
            ;;
        *)
            echo "Usage: $0 {register|resolve <hostname>|list|once}"
            echo ""
            echo "Commands:"
            echo "  register  - Start continuous registration daemon (default)"
            echo "  resolve   - Resolve a hostname to IP address"
            echo "  list      - List all registered peers"
            echo "  once      - Register once and exit"
            echo ""
            echo "Environment Variables:"
            echo "  DISCOVERY_URL    - Discovery API URL (default: http://discovery-api:5000)"
            echo "  PEER_HOSTNAME    - Peer hostname (default: hostname)"
            echo "  WG_INTERFACE     - WireGuard interface (default: wg0)"
            echo "  REGISTER_INTERVAL - Registration interval in seconds (default: 300)"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
