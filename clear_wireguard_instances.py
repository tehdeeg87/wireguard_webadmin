#!/usr/bin/env python3
import sqlite3

# Connect to the database
conn = sqlite3.connect('database/db.sqlite3')
cursor = conn.cursor()

print('Clearing all WireGuard instances and related data...')

# Delete all peers first (due to foreign key constraints)
cursor.execute("DELETE FROM wireguard_peer")
print('Deleted all peers')

# Delete all peer allowed IPs
cursor.execute("DELETE FROM wireguard_peerallowedip")
print('Deleted all peer allowed IPs')

# Delete all peer status records
cursor.execute("DELETE FROM wireguard_peerstatus")
print('Deleted all peer status records')

# Delete all peer groups
cursor.execute("DELETE FROM wireguard_peergroup")
print('Deleted all peer groups')

# Delete all WireGuard instances
cursor.execute("DELETE FROM wireguard_wireguardinstance")
print('Deleted all WireGuard instances')

# Commit the changes
conn.commit()
print('Database cleared successfully!')

# Show remaining records
cursor.execute("SELECT COUNT(*) FROM wireguard_wireguardinstance")
instance_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM wireguard_peer")
peer_count = cursor.fetchone()[0]

print(f'Remaining instances: {instance_count}')
print(f'Remaining peers: {peer_count}')

conn.close()
print('Database cleanup completed')
