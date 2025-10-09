import asyncio
import threading
import time
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import PeerRegistration, PeerResponse, ErrorResponse, StatusResponse, PeerRecord
from .utils import peer_store
from .dns_server import start_dns_server

# Create FastAPI app
app = FastAPI(
    title="WireGuard Peer Discovery API",
    description="Internal peer discovery service for WireGuard mesh networks",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def cleanup_worker():
    """Background worker to clean up expired peers"""
    while True:
        try:
            removed_count = peer_store.cleanup_expired()
            if removed_count > 0:
                print(f"Cleaned up {removed_count} expired peer(s)")
            time.sleep(60)  # Run cleanup every minute
        except Exception as e:
            print(f"Error in cleanup worker: {e}")
            time.sleep(60)


# Start background cleanup thread
cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
cleanup_thread.start()

# Start DNS server
start_dns_server()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "WireGuard Peer Discovery API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/register", response_model=StatusResponse)
async def register_peer(peer: PeerRegistration):
    """Register or refresh a peer record"""
    try:
        peer_store.register_peer(peer.hostname, peer.ip)
        return StatusResponse(
            status="ok",
            message=f"Peer {peer.hostname} registered with IP {peer.ip}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.get("/resolve/{hostname}", response_model=PeerResponse)
async def resolve_peer(hostname: str):
    """Resolve a peer hostname to its IP address"""
    peer = peer_store.resolve_peer(hostname)
    if not peer:
        raise HTTPException(
            status_code=404,
            detail=f"Hostname '{hostname}' not found"
        )
    
    return PeerResponse(hostname=peer.hostname, ip=peer.ip)


@app.get("/list", response_model=List[PeerRecord])
async def list_peers():
    """List all currently registered peers"""
    return peer_store.list_peers()


@app.get("/stats")
async def get_stats():
    """Get API statistics"""
    peers = peer_store.list_peers()
    return {
        "total_peers": len(peers),
        "peers": [
            {
                "hostname": peer.hostname,
                "ip": peer.ip,
                "last_seen": peer.last_seen.isoformat()
            }
            for peer in peers
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
