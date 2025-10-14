#!/usr/bin/env python3
"""
Quick HADDNS Test - Fast validation of core functionality
"""

import subprocess
import sys

def run_cmd(cmd):
    """Run command and return success, output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except:
        return False, "", "Command failed"

def main():
    print("🚀 Quick HADDNS Test")
    print("=" * 40)
    
    tests = [
        ("Database migrations", "python manage.py makemigrations dns --dry-run"),
        ("Models import", "python manage.py shell -c \"from dns.models import HADDNSConfig, PeerHostnameMapping; print('OK')\""),
        ("HADDNS setup", "python manage.py haddns_setup --domain test.local --threshold 180"),
        ("WireGuard check", "wg --version"),
        ("dnsmasq config", "python manage.py generate_dnsmasq_config --dry-run"),
        ("HADDNS update", "python manage.py haddns_update --dry-run")
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, cmd in tests:
        success, stdout, stderr = run_cmd(cmd)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if not success and stderr:
            print(f"   Error: {stderr.strip()}")
        passed += 1 if success else 0
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! HADDNS is ready to use.")
        print("\nNext steps:")
        print("1. python manage.py haddns_setup")
        print("2. python manage.py generate_dnsmasq_config")
        print("3. systemctl restart dnsmasq")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("Run the comprehensive test for more details: python test_haddns_comprehensive.py")

if __name__ == "__main__":
    main()
