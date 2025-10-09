#!/bin/bash

# Simple DNS Update Script for WireGuard Peer Hostnames
# Fetches peer hostname mappings from Django API and updates shared hosts file

set -e

# Configuration
WEBADMIN_URL="${WEBADMIN_URL:-http://wireguard-webadmin:8000}"
API_ENDPOINT="${API_ENDPOINT:-/api/peers/hosts/}"
HOSTS_FILE="${HOSTS_FILE:-/shared_hosts/hosts}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to update hosts file
update_hosts_file() {
    local hosts_content="$1"
    
    # Create backup of current hosts file
    if [ -f "$HOSTS_FILE" ]; then
        cp "$HOSTS_FILE" "${HOSTS_FILE}.backup.$(date +%s)"
    fi
    
    # Update hosts file
    echo "$hosts_content" > "$HOSTS_FILE"
    log "Updated hosts file with $(echo "$hosts_content" | wc -l) entries"
}

# Main function
main() {
    log "Starting peer hostname update process"
    
    local api_url="${WEBADMIN_URL}${API_ENDPOINT}"
    log "Fetching peer hostnames from: $api_url"
    
    # Fetch JSON data from API
    local json_data
    if ! json_data=$(curl -s --connect-timeout 10 --max-time 30 "$api_url"); then
        log "ERROR: Failed to fetch data from API"
        exit 1
    fi
    
    # Check if we got valid JSON
    if ! echo "$json_data" | jq empty 2>/dev/null; then
        log "ERROR: Invalid JSON response from API"
        exit 1
    fi
    
    # Convert JSON to hosts file format
    local hosts_content
    hosts_content=$(echo "$json_data" | jq -r 'to_entries[] | "\(.value) \(.key)"' 2>/dev/null)
    
    if [ -z "$hosts_content" ]; then
        log "WARNING: No peer hostnames found in API response"
        exit 1
    fi
    
    # Add header to hosts file
    local header="# WireGuard Peer Hostnames
# Generated automatically - do not edit manually
# Last updated: $(date)
"
    
    # Combine header with peer entries
    echo -e "${header}${hosts_content}" > /tmp/peer_hosts.tmp
    
    # Update the hosts file
    update_hosts_file "$(cat /tmp/peer_hosts.tmp)"
    
    # Clean up
    rm -f /tmp/peer_hosts.tmp
    
    log "Successfully updated peer hostnames"
}

# Run main function
main "$@"