import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class PhysicalDiscoveryService:
    """Service to discover physical block devices (HDDs, USBs, etc.)"""

    @staticmethod
    def list_devices():
        """Returns a list of physical block devices using lsblk"""
        try:
            # We filter for 'disk' type to avoid listing every partition/loop device by default
            # But we include TYPE so we can filter if needed.
            cmd = [
                "lsblk",
                "--json",
                "-o",
                "NAME,SIZE,MODEL,PATH,TYPE,MOUNTPOINT,SERIAL",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            devices = []
            for dev in data.get("blockdevices", []):
                # Filter: We want physical disks, or partitions if the user is specific
                # For high-level selection, 'disk' is usually what they want for full imaging
                if dev.get("type") in ["disk", "part"]:
                    devices.append(
                        {
                            "name": dev.get("name"),
                            "model": dev.get("model") or "Unknown Device",
                            "size": dev.get("size"),
                            "path": dev.get("path"),
                            "type": dev.get("type"),
                            "mountpoint": dev.get("mountpoint"),
                            "serial": dev.get("serial"),
                            "is_mounted": bool(dev.get("mountpoint")),
                        }
                    )
            return devices
        except Exception as e:
            logger.error(f"Failed to list block devices: {e}")
            return []
