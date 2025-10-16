#!/bin/bash
set -e

echo "🚀 Starting WireGuard WebAdmin with DNS Integration..."

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for database to be ready..."
    while ! python3 manage.py migrate --check >/dev/null 2>&1; do
        echo "   Database not ready, waiting..."
        sleep 2
    done
    echo "✅ Database is ready"
}

# Function to configure existing dnsmasq
configure_existing_dnsmasq() {
    echo "🔧 Configuring existing dnsmasq service..."
    
    # Add hosts file configuration to dnsmasq if not already present
    if ! grep -q "addn-hosts=/shared_hosts/hosts_static" /etc/dnsmasq.conf; then
        echo "addn-hosts=/shared_hosts/hosts_static" >> /etc/dnsmasq.conf
        echo "✅ Added hosts file configuration to dnsmasq"
    else
        echo "✅ dnsmasq already configured"
    fi
    
    # Create a dnsmasq config file for our hosts
    cat > /etc/dnsmasq.d/wireguard-hosts.conf << EOF
# WireGuard WebAdmin DNS configuration
addn-hosts=/shared_hosts/hosts_static
domain=vpn.local
expand-hosts
EOF
    echo "✅ Created dnsmasq configuration file"
}

# Function to initialize DNS
initialize_dns() {
    echo "📡 Initializing DNS..."
    
    # Update DNS hosts file
    python3 manage.py update_dns --reload
    
    echo "✅ DNS initialized successfully"
}

# Function to show status
show_status() {
    echo "📊 DNS Status:"
    python3 manage.py update_dns --status
    
    echo ""
    echo "📁 Hosts file contents:"
    cat /shared_hosts/hosts_static || echo "No hosts file yet"
}

# Main execution
main() {
    echo "🎯 Starting WireGuard WebAdmin DNS Integration..."
    
    # Wait for database
    wait_for_db
    
    # Run migrations
    echo "🔄 Running database migrations..."
    python3 manage.py migrate --noinput
    
    # Configure existing dnsmasq
    configure_existing_dnsmasq
    
    # Initialize DNS
    initialize_dns
    
    # Show status
    show_status
    
    echo ""
    echo "🎉 WireGuard WebAdmin with DNS Integration is ready!"
    echo "   - Peers will automatically get DNS resolution"
    echo "   - Create peers with names like 'server1', 'laptop2'"
    echo "   - They'll be resolvable as 'server1.vpn.local', 'laptop2.vpn.local'"
    echo ""
    echo "⚠️  Note: The existing dnsmasq service will automatically pick up our configuration"
    echo "   If DNS doesn't work immediately, restart dnsmasq:"
    echo "   docker exec wireguard-webadmin service dnsmasq restart"
    echo ""
    
    # Start the main application
    exec "$@"
}

# Run main function with all arguments
main "$@"
