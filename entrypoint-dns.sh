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

# Function to configure dnsmasq
configure_dnsmasq() {
    echo "🔧 Configuring dnsmasq..."
    
    # Add hosts file configuration to dnsmasq if not already present
    if ! grep -q "addn-hosts=/shared_hosts/hosts_static" /etc/dnsmasq.conf; then
        echo "addn-hosts=/shared_hosts/hosts_static" >> /etc/dnsmasq.conf
        echo "✅ Added hosts file configuration to dnsmasq"
    else
        echo "✅ dnsmasq already configured"
    fi
}

# Function to start dnsmasq
start_dnsmasq() {
    echo "🌐 Starting dnsmasq..."
    
    # Kill any existing dnsmasq processes
    pkill -f dnsmasq || true
    
    # Remove stale PID files
    rm -f /run/dnsmasq/dnsmasq.pid
    
    # Start dnsmasq with our configuration
    dnsmasq --no-daemon --log-queries --addn-hosts=/shared_hosts/hosts_static &
    
    echo "✅ dnsmasq started successfully"
}

# Function to initialize DNS
initialize_dns() {
    echo "📡 Initializing DNS..."
    
    # Wait a moment for dnsmasq to start
    sleep 2
    
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
    
    # Configure dnsmasq
    configure_dnsmasq
    
    # Start dnsmasq
    start_dnsmasq
    
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
    
    # Start the main application
    exec "$@"
}

# Run main function with all arguments
main "$@"
