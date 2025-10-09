import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from .models import PeerRecord


class PeerStore:
    def __init__(self, ttl_minutes: int = 10, persist_file: Optional[str] = None):
        self.peers: Dict[str, PeerRecord] = {}
        self.ttl_minutes = ttl_minutes
        self.persist_file = persist_file
        self.load_from_file()
    
    def register_peer(self, hostname: str, ip: str) -> None:
        """Register or refresh a peer record"""
        self.peers[hostname] = PeerRecord(
            hostname=hostname,
            ip=ip,
            last_seen=datetime.utcnow()
        )
        self.save_to_file()
    
    def resolve_peer(self, hostname: str) -> Optional[PeerRecord]:
        """Resolve a hostname to peer record"""
        peer = self.peers.get(hostname)
        if peer and self._is_peer_valid(peer):
            return peer
        return None
    
    def list_peers(self) -> List[PeerRecord]:
        """List all valid peers"""
        now = datetime.utcnow()
        valid_peers = []
        
        for peer in self.peers.values():
            if self._is_peer_valid(peer):
                valid_peers.append(peer)
            else:
                # Remove expired peers
                if peer.hostname in self.peers:
                    del self.peers[peer.hostname]
        
        self.save_to_file()
        return valid_peers
    
    def _is_peer_valid(self, peer: PeerRecord) -> bool:
        """Check if peer record is still valid (not expired)"""
        now = datetime.utcnow()
        expiry_time = peer.last_seen + timedelta(minutes=self.ttl_minutes)
        return now < expiry_time
    
    def cleanup_expired(self) -> int:
        """Remove expired peers and return count of removed peers"""
        initial_count = len(self.peers)
        now = datetime.utcnow()
        
        expired_hostnames = []
        for hostname, peer in self.peers.items():
            if not self._is_peer_valid(peer):
                expired_hostnames.append(hostname)
        
        for hostname in expired_hostnames:
            del self.peers[hostname]
        
        if expired_hostnames:
            self.save_to_file()
        
        return initial_count - len(self.peers)
    
    def save_to_file(self) -> None:
        """Save peers to JSON file for persistence"""
        if not self.persist_file:
            return
        
        try:
            data = {
                "peers": {
                    hostname: {
                        "hostname": peer.hostname,
                        "ip": peer.ip,
                        "last_seen": peer.last_seen.isoformat()
                    }
                    for hostname, peer in self.peers.items()
                }
            }
            
            with open(self.persist_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save peers to file: {e}")
    
    def load_from_file(self) -> None:
        """Load peers from JSON file"""
        if not self.persist_file or not os.path.exists(self.persist_file):
            return
        
        try:
            with open(self.persist_file, 'r') as f:
                data = json.load(f)
            
            for hostname, peer_data in data.get("peers", {}).items():
                self.peers[hostname] = PeerRecord(
                    hostname=peer_data["hostname"],
                    ip=peer_data["ip"],
                    last_seen=datetime.fromisoformat(peer_data["last_seen"])
                )
        except Exception as e:
            print(f"Warning: Could not load peers from file: {e}")


# Global peer store instance
peer_store = PeerStore(ttl_minutes=10, persist_file="/app/data/peers.json")
