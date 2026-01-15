import sys
import os
import time
import socket
import platform
import json
import requests
import hashlib
import subprocess

class ForensixAgent:
    """
    Standalone Remote Forensic Agent.
    Intended to be compiled to a single binary (e.g. using PyInstaller).
    """
    
    SERVER_URL = "http://localhost:8000/api/acquisition/agent/heartbeat"
    
    def __init__(self, server_url=None):
        if server_url:
            self.SERVER_URL = server_url
        self.hostname = socket.gethostname()
        self.os_info = f"{platform.system()} {platform.release()}"
        self.agent_id = None

    def collect_volatile_data(self):
        """Collects volatile system data"""
        data = {
            'timestamp': time.time(),
            'os': self.os_info,
            'network_connections': self._get_netstat(),
            'processes': self._get_processes(),
        }
        return data

    def _get_netstat(self):
        try:
            # Cross-platform basic netstat
            if platform.system() == "Windows":
                output = subprocess.check_output(['netstat', '-an'], text=True)
            else:
                output = subprocess.check_output(['netstat', '-an'], text=True)
            return output[:2000] # Truncate for demo
        except Exception:
            return "Netstat failed"

    def _get_processes(self):
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output(['tasklist'], text=True)
            else:
                output = subprocess.check_output(['ps', 'aux'], text=True)
            return output[:2000] # Truncate for demo
        except Exception:
            return "Process list failed"

    def stream_memory(self):
        """
        Dumps memory using available tools (LiME/WinPmem).
        Mocked for this implementation.
        """
        print("Starting memory dump...")
        # Mocking a 100MB dump
        dummy_data = os.urandom(1024 * 1024 * 10) 
        return dummy_data

    def run(self):
        print(f"ForensixAgent active on {self.hostname}")
        print("Collecting volatile data...")
        data = self.collect_volatile_data()
        print(f"Collected {len(str(data))} bytes of volatile evidence.")
        # In real life, this would post to the server
        return data

if __name__ == "__main__":
    agent = ForensixAgent()
    agent.run()
