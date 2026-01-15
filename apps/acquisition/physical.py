import os
import hashlib
import logging
import time
from django.utils import timezone

logger = logging.getLogger(__name__)

class PhysicalImager:
    """
    Pillar 1: Physical Acquisition Engine
    Handles forensic acquisition of physical block devices.
    Supports:
    - Raw (DD): Bit-for-bit copy
    - E01 (Expert Witness): Compressed, metadata-rich format (Mocked for now)
    """

    CHUNK_SIZE = 1024 * 1024  # 1MB Buffer

    def __init__(self, task):
        self.task = task
        self.source_path = task.source_path
        self.destination_path = task.destination_path
        self.hashes = {
            'md5': hashlib.md5(),
            'sha256': hashlib.sha256()
        }

    def acquire(self):
        """Main entry point for acquisition"""
        try:
            self.task.status = 'running'
            self.task.started_at = timezone.now()
            self.task.save()

            if not os.path.exists(self.source_path):
                raise FileNotFoundError(f"Source device not found: {self.source_path}")

            if self.task.type == 'disk_expert':
                self._acquire_e01()
            else:
                self._acquire_raw()

            self._finalize_task()
            return True

        except Exception as e:
            logger.error(f"Acquisition failed: {e}")
            self.task.status = 'failed'
            self.task.error_message = str(e)
            self.task.save()
            return False

    def _acquire_raw(self):
        """Performs a raw DD-style acquisition with hashing"""
        total_size = os.path.getsize(self.source_path)
        bytes_copied = 0
        start_time = time.time()

        with open(self.source_path, 'rb') as src, open(self.destination_path, 'wb') as dst:
            while True:
                chunk = src.read(self.CHUNK_SIZE)
                if not chunk:
                    break

                # Write to destination
                dst.write(chunk)

                # Update Hashes
                self.hashes['md5'].update(chunk)
                self.hashes['sha256'].update(chunk)

                # Update Progress
                bytes_copied += len(chunk)
                msg = self._update_progress(bytes_copied, total_size, start_time)
                
                # In a real sync scenario, we might yield or update simpler
                # For this implementation, we just update the DB every 10% or so effectively
                if bytes_copied % (self.CHUNK_SIZE * 100) == 0:
                   self.task.current_speed = msg
                   self.task.save()

    def _acquire_e01(self):
        """
        Mock implementation of E01 acquisition.
        In production, this would use pyewf or call out to ewfacquire.
        """
        logger.info("Starting E01 acquisition (Mock Mode)")
        # For now, falls back to raw but renames file for demo
        self.destination_path += ".E01" 
        self._acquire_raw()

    def _update_progress(self, current, total, start_time):
        """Calculates speed and updates task progress"""
        elapsed = time.time() - start_time
        if elapsed > 0:
            speed_mb = (current / 1024 / 1024) / elapsed
            self.task.progress_percent = round((current / total) * 100, 2)
            return f"{speed_mb:.2f} MB/s"
        return "Calculating..."

    def _finalize_task(self):
        """Saves final hashes and completes task"""
        self.task.status = 'completed'
        self.task.completed_at = timezone.now()
        self.task.progress_percent = 100.0
        self.task.calculated_md5 = self.hashes['md5'].hexdigest()
        self.task.calculated_sha256 = self.hashes['sha256'].hexdigest()
        self.task.save()
        
        # Update related evidence object
        if self.task.evidence:
            self.task.evidence.md5_hash = self.task.calculated_md5
            self.task.evidence.sha256_hash = self.task.calculated_sha256
            self.task.evidence.size_bytes = os.path.getsize(self.destination_path)
            self.task.evidence.save()
