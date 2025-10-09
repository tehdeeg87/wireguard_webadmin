# WireGuard Peer Discovery API

A lightweight FastAPI microservice for internal peer discovery in WireGuard mesh networks. This service allows WireGuard peers to register themselves and resolve hostnames to IP addresses without requiring external DNS or mDNS services.

## Features

- **Peer Registration**: Peers can register themselves with hostname and IP
- **Hostname Resolution**: Resolve peer hostnames to IP addresses
- **Real DNS Server**: Built-in DNS server that answers actual DNS queries (port 53)
- **Automatic Cleanup**: Expired peer records are automatically removed
- **Persistence**: Optional JSON file persistence for peer records
- **RESTful API**: Simple HTTP API for all operations
- **Docker Ready**: Containerized for easy deployment
- **DNS Caching**: Built-in DNS response caching for better performance

## API Endpoints

### Register Peer
```bash
POST /register
Content-Type: application/json

{
  "hostname": "my-peer",
  "ip": "10.8.0.2"
}
```

### Resolve Hostname
```bash
GET /resolve/{hostname}
```

### List All Peers
```bash
GET /list
```

### Health Check
```bash
GET /
```

## Quick Start

### Using Docker Compose

1. Add to your `docker-compose.yml`:
```yaml
version: "3.8"
services:
  discovery-api:
    build: ./discovery-api
    ports:
      - "5000:5000"
    volumes:
      - discovery_data:/app/data
    networks:
      - wgnet

  wireguard-webadmin:
    # ... your existing config
    depends_on:
      - discovery-api
    networks:
      - wgnet

volumes:
  discovery_data:

networks:
  wgnet:
    driver: bridge
```

2. Start the services:
```bash
docker-compose up -d
```

### Using the Peer Registration Script

Each WireGuard peer can register itself using the provided script:

```bash
# Copy the script to your peer container
docker cp discovery-api/peer-register.sh your-peer-container:/usr/local/bin/

# Make it executable
docker exec your-peer-container chmod +x /usr/local/bin/peer-register.sh

# Setup DNS resolution (configures /etc/resolv.conf)
docker exec your-peer-container /usr/local/bin/peer-register.sh setup-dns

# Start registration (runs continuously)
docker exec -d your-peer-container /usr/local/bin/peer-register.sh

# Or register once
docker exec your-peer-container /usr/local/bin/peer-register.sh once

# Resolve a hostname
docker exec your-peer-container /usr/local/bin/peer-register.sh resolve other-peer

# List all peers
docker exec your-peer-container /usr/local/bin/peer-register.sh list
```

### DNS Resolution

The discovery API includes a built-in DNS server that answers actual DNS queries. Once peers are registered and DNS is configured:

```bash
# These will now work with real DNS resolution:
ping mypeer.local
nslookup otherpeer.local
dig @discovery-api otherpeer.local
```

The DNS server automatically:
- Resolves registered peer hostnames to their IP addresses
- Handles `.local` domain suffixes
- Caches responses for better performance
- Returns proper DNS error codes for unknown hostnames

## Configuration

### Environment Variables

- `DISCOVERY_URL`: Discovery API URL (default: http://discovery-api:5000)
- `PEER_HOSTNAME`: Peer hostname (default: hostname)
- `WG_INTERFACE`: WireGuard interface (default: wg0)
- `REGISTER_INTERVAL`: Registration interval in seconds (default: 300)

### TTL Settings

Peer records expire after 10 minutes by default. This can be modified in `app/utils.py`:

```python
peer_store = PeerStore(ttl_minutes=10, persist_file="/app/data/peers.json")
```

## Integration with WireGuard Web Admin

This discovery API can be integrated with your WireGuard web admin to provide hostname resolution for peer configurations. The API is designed to be lightweight and can run alongside your existing WireGuard web admin container.

## Development

### Local Development

```bash
cd discovery-api
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### Testing

```bash
# Register a peer
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"hostname": "test-peer", "ip": "10.8.0.100"}'

# Resolve hostname
curl http://localhost:5000/resolve/test-peer

# List all peers
curl http://localhost:5000/list
```

## License

This project is part of the WireGuard Web Admin system.
