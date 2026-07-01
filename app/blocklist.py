import json
import os
import asyncio
import subprocess
import platform
from typing import Dict
from datetime import datetime

class IPBlocklistManager:
    def __init__(self, file_path: str = "app/blocked_ips.json"):
        self.file_path = file_path
        self.blocked_ips: Dict[str, dict] = {}
        self.lock = asyncio.Lock()
        self.os_type = platform.system()
        self.auto_block_enabled = True
        
        self._load()
        self._sync_initial_firewall()

    def _run_command(self, cmd_list):
        """Execute a shell command silently. Fails gracefully if not root."""
        try:
            subprocess.run(cmd_list, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            # We don't crash the app if sudo is missing, just print a warning
            print(f"[Warning] OS Firewall command failed. Ensure you are running with 'sudo'. Command: {' '.join(cmd_list)}")
            return False

    def _clean_ip(self, ip: str) -> str:
        """Strips port from IPv4 addresses if present."""
        if '.' in ip and ':' in ip:
            return ip.split(':')[0]
        return ip

    def _block_os_ip(self, ip: str):
        """Applies the block at the OS Layer (iptables / route)."""
        clean_ip = self._clean_ip(ip)
        if self.os_type == "Darwin":
            self._run_command(["route", "-q", "add", "-host", clean_ip, "127.0.0.1", "-blackhole"])
        elif self.os_type == "Linux":
            self._run_command(["iptables", "-I", "INPUT", "-s", clean_ip, "-j", "DROP"])

    def _unblock_os_ip(self, ip: str):
        """Removes the block at the OS Layer (iptables / route)."""
        clean_ip = self._clean_ip(ip)
        if self.os_type == "Darwin":
            self._run_command(["route", "-q", "delete", "-host", clean_ip, "127.0.0.1", "-blackhole"])
        elif self.os_type == "Linux":
            self._run_command(["iptables", "-D", "INPUT", "-s", clean_ip, "-j", "DROP"])

    def _sync_initial_firewall(self):
        """On startup, ensure all IPs in the JSON are blocked in the OS."""
        if not self.blocked_ips:
            return
            
        print(f"Syncing {len(self.blocked_ips)} blocked IPs to OS Firewall...")
        for ip in self.blocked_ips:
            self._block_os_ip(ip)

    def _load(self):
        """Load blocked IPs from file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.blocked_ips = json.load(f)
            except Exception as e:
                print(f"Error loading blocklist: {e}")
                self.blocked_ips = {}
        else:
            self.blocked_ips = {}
            self._save_sync()

    def _save_sync(self):
        """Save blocked IPs to file synchronously (used on init)."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.blocked_ips, f, indent=4)
        except Exception as e:
            print(f"Error saving blocklist: {e}")

    async def _save(self):
        """Save blocked IPs to file asynchronously."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.blocked_ips, f, indent=4)
        except Exception as e:
            print(f"Error saving blocklist: {e}")

    async def add_ip(self, ip: str, reason: str = "Manual", banned_by: str = "Admin") -> bool:
        """Add an IP to the blocklist and update the OS firewall."""
        async with self.lock:
            if ip in self.blocked_ips:
                return False
            
            self.blocked_ips[ip] = {
                "reason": reason,
                "banned_by": banned_by,
                "timestamp": datetime.now().isoformat()
            }
            await self._save()
            
            # Immediately block at OS layer
            self._block_os_ip(ip)
            return True

    async def remove_ip(self, ip: str) -> bool:
        """Remove an IP from the blocklist and update the OS firewall."""
        async with self.lock:
            if ip not in self.blocked_ips:
                return False
            
            del self.blocked_ips[ip]
            await self._save()
            
            # Immediately unblock at OS layer
            self._unblock_os_ip(ip)
            return True

    def is_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked (fast, in-memory check for the middleware)."""
        return ip in self.blocked_ips

    def get_blocked_ips(self) -> Dict[str, dict]:
        """Get the full list of blocked IPs."""
        return self.blocked_ips.copy()

    def toggle_auto_block(self) -> bool:
        """Toggles the auto-block state ON or OFF."""
        self.auto_block_enabled = not self.auto_block_enabled
        return self.auto_block_enabled

    async def flush_all(self) -> int:
        """Removes all blocked IPs and clears firewall rules."""
        async with self.lock:
            count = len(self.blocked_ips)
            for ip in list(self.blocked_ips.keys()):
                self._unblock_os_ip(ip)
                del self.blocked_ips[ip]
            await self._save()
            return count

# Singleton instance
blocklist_manager = IPBlocklistManager()
