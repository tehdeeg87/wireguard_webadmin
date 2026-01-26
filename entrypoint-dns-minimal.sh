#!/bin/bash
set -e

echo "🚀 Starting WireGuard WebAdmin with DNS Integration..."

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for database to be ready..."
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        # Use test_db_connection.py to get detailed error messages
        if python3 /app/test_db_connection.py 2>&1 | grep -q "Connection successful"; then
            echo "✅ Database is ready"
            return 0
        else
            attempt=$((attempt + 1))
            if [ $attempt -lt $max_attempts ]; then
                echo "   Database not ready, waiting... (attempt $attempt/$max_attempts)"
                # Show the actual error on first attempt
                if [ $attempt -eq 1 ]; then
                    echo ""
                    echo "   Connection error details:"
                    python3 /app/test_db_connection.py 2>&1 | grep -E "(ERROR|WARNING|Please check)" | sed 's/^/   /'
                    echo ""
                fi
                sleep 2
            else
                echo ""
                echo "❌ Database connection failed after $max_attempts attempts"
                echo "   Final connection test:"
                python3 /app/test_db_connection.py
                exit 1
            fi
        fi
    done
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
