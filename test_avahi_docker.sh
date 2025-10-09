#!/bin/bash
# Comprehensive test script for Avahi functionality in Docker containers

set -e

echo "🚀 WireGuard WebAdmin - Avahi Docker Testing"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is running"

# Make test scripts executable
chmod +x test_scripts/*.sh
print_success "Made test scripts executable"

# Create test data directory
mkdir -p test_data
print_success "Created test data directory"

# Step 1: Build and start containers
print_status "Step 1: Building and starting Docker containers..."
docker-compose -f docker-compose-test.yml down --remove-orphans
docker-compose -f docker-compose-test.yml build
docker-compose -f docker-compose-test.yml up -d

print_success "Containers started"

# Step 2: Wait for services to be ready
print_status "Step 2: Waiting for services to be ready..."
sleep 30

# Check if containers are running
print_status "Checking container status..."
docker-compose -f docker-compose-test.yml ps

# Step 3: Setup test data
print_status "Step 3: Setting up test data..."
docker exec wg-webadmin-test python /app/test_scripts/setup_test_data.py

# Step 4: Test Avahi functionality
print_status "Step 4: Testing Avahi functionality..."

# Test from main container
print_status "Testing from main container..."
docker exec wg-webadmin-test python /app/test_avahi_peer_resolution.py

# Test from peer container
print_status "Testing from peer container..."
docker exec test-peer /test_scripts/test_peer_resolution.sh

# Test from DNS container
print_status "Testing from DNS container..."
docker exec dns-test /test_scripts/test_dns_resolution.sh

# Step 5: Interactive testing
print_status "Step 5: Interactive testing options..."
echo ""
echo "🔍 You can now test Avahi functionality interactively:"
echo ""
echo "1. Test hostname resolution:"
echo "   docker exec wg-webadmin-test avahi-resolve-host-name my-phone"
echo "   docker exec wg-webadmin-test avahi-resolve-host-name my-phone.wg0.local"
echo ""
echo "2. Browse services:"
echo "   docker exec wg-webadmin-test avahi-browse -a"
echo "   docker exec wg-webadmin-test avahi-browse -t _wireguard._tcp"
echo ""
echo "3. Test from peer container:"
echo "   docker exec test-peer avahi-resolve-host-name my-phone"
echo "   docker exec test-peer ping my-phone"
echo ""
echo "4. Access the web interface:"
echo "   http://localhost:8000"
echo "   Login: admin / admin123"
echo ""
echo "5. View logs:"
echo "   docker-compose -f docker-compose-test.yml logs -f"
echo ""

# Ask if user wants to keep containers running
read -p "Do you want to keep the containers running for interactive testing? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Containers will continue running. Use 'docker-compose -f docker-compose-test.yml down' to stop them."
    print_status "You can run the test scripts again with:"
    echo "   docker exec wg-webadmin-test python /app/test_avahi_peer_resolution.py"
    echo "   docker exec test-peer /test_scripts/test_peer_resolution.sh"
    echo "   docker exec dns-test /test_scripts/test_dns_resolution.sh"
else
    print_status "Stopping containers..."
    docker-compose -f docker-compose-test.yml down
    print_success "Containers stopped"
fi

echo ""
print_success "Avahi Docker testing completed!"
echo "============================================="
