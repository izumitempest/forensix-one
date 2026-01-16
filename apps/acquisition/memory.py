import os
import logging
import time
import subprocess
from django.utils import timezone
from .physical import PhysicalImager

logger = logging.getLogger(__name__)


class MemoryImager(PhysicalImager):
    """
    Pillar 1: Volatile Memory Acquisition
    Supports:
    - AVML (Compressed/Raw RAM)
    - /proc/kcore fallback (Raw)
    """

    def __init__(self, task):
        super().__init__(task)
        # For memory, source is conceptually 'RAM'
        self.internal_source = "/proc/kcore" if os.path.exists("/proc/kcore") else ""

        # Ensure destination has .mem extension
        if not self.destination_path.endswith((".mem", ".raw")):
            self.destination_path += ".mem"

    def acquire(self):
        """Executes memory capture"""
        try:
            self.task.status = "running"
            self.task.started_at = timezone.now()
            self.task.save()

            self._validate_paths()

            # 1. Attempt AVML (Preferred for Linux)
            if self._try_avml():
                self._finalize_task()
                return True

            # 2. Fallback to /proc/kcore bit-stream
            if self.internal_source:
                logger.info(f"AVML not found, falling back to /proc/kcore capture")
                self._acquire_raw()
                self._finalize_task()
                return True

            raise RuntimeError(
                "No suitable memory acquisition source found or permissions denied."
            )

        except PermissionError as e:
            error_msg = (
                f"Permission Denied: '{self.internal_source}'. "
                "Forensic Tip: RAM access requires root or CAP_SYS_RAWIO. "
                "Ensure local worker is run with sudo or has raw-io capabilities."
            )
            logger.error(error_msg)
            self.task.status = "failed"
            self.task.error_message = error_msg
            self.task.save()
            return False
        except Exception as e:
            logger.error(f"Memory acquisition failed: {e}")
            self.task.status = "failed"
            self.task.error_message = str(e)
            self.task.save()
            return False

    def _try_avml(self):
        """Attempts to use AVML if present in path"""
        try:
            # Check if avml is available
            subprocess.run(["avml", "--version"], capture_output=True, check=True)

            logger.info("AVML detected. Starting compressed RAM capture...")
            # avml <destination>
            cmd = ["avml", self.destination_path]

            # Start timer for speed calculation
            start_time = time.time()

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            while process.poll() is None:
                # Update UI with 'Capturing...' status
                elapsed = time.time() - start_time
                self.task.current_speed = f"AVML Active ({elapsed:.1f}s)"
                self.task.save()
                time.sleep(2)

            if process.returncode == 0:
                logger.info("AVML capture successful.")
                return True
            else:
                stderr = process.stderr.read().decode()
                logger.warning(f"AVML failed: {stderr}")
                return False

        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
