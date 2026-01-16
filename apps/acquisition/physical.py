import os
import hashlib
import logging
import time
from django.utils import timezone
from django.conf import settings

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
        # 0. Set Initial Paths
        self.logical_source = task.source_path or ""
        self.internal_source = task.source_path or ""
        self.destination_path = task.destination_path or ""

        # 1. Handle File Uploads (Special Logic)
        if task.type == "file_upload" and task.source_upload:
            self.internal_source = task.source_upload.path
            if not self.logical_source:
                self.logical_source = os.path.basename(task.source_upload.name)
                task.source_path = self.logical_source
                task.save()

        # 2. Auto-generate Destination if missing
        if not self.destination_path:
            ext = ".dd"  # Default
            if task.type == "disk_expert":
                ext = ".E01"
            elif task.type == "memory_dump":
                ext = ".mem"
            elif task.type == "remote_agent":
                ext = ".remote"

            clean_name = (
                task.evidence.name.replace(" ", "_") if task.evidence else "acquisition"
            )
            self.destination_path = os.path.join(
                settings.MEDIA_ROOT, "evidence", f"{task.id}_{clean_name}{ext}"
            )
            task.destination_path = self.destination_path
            task.save()

        # 3. Robustness for UI placeholders
        if "Auto-managed" in self.destination_path:
            self.destination_path = ""  # Force re-validation or generation if needed

        logger.info(
            f"Initialized Imager: forensic_source='{self.logical_source}', internal='{self.internal_source}', dest='{self.destination_path}'"
        )

        self.hashes = {"md5": hashlib.md5(), "sha256": hashlib.sha256()}

    def _validate_paths(self):
        """Final validation before acquisition starts"""
        # Memory and Remote do not necessarily have a local source path at init
        if not self.internal_source and self.task.type not in [
            "memory_dump",
            "remote_agent",
        ]:
            raise ValueError(
                "Internal source path is empty. Acquisition cannot proceed."
            )
        if not self.destination_path:
            raise ValueError("Destination path is empty. Acquisition cannot proceed.")

    def acquire(self):
        """Main entry point for acquisition"""
        try:
            self.task.status = "running"
            self.task.started_at = timezone.now()
            self.task.save()

            self._validate_paths()

            if (
                not os.path.exists(self.internal_source)
                and self.task.type != "memory_dump"
            ):
                raise FileNotFoundError(
                    f"Source device not found: {self.internal_source}"
                )

            if self.task.type == "disk_expert":
                self._acquire_e01()
            elif self.task.type == "file_upload":
                # ensure evidence dir exists
                dest_dir = os.path.dirname(self.destination_path)
                logger.debug(f"Ensuring directory exists: '{dest_dir}'")
                if dest_dir:
                    os.makedirs(dest_dir, exist_ok=True)
                else:
                    # If somehow still empty, fallback to MEDIA_ROOT/evidence
                    fallback = os.path.join(settings.MEDIA_ROOT, "evidence")
                    os.makedirs(fallback, exist_ok=True)
                    self.destination_path = os.path.join(
                        fallback,
                        os.path.basename(self.destination_path) or "output.bin",
                    )

                self._acquire_raw()
            else:
                self._acquire_raw()

            self._finalize_task()
            return True

        except PermissionError:
            error_msg = (
                "Permission Denied accessing device. "
                "Forensic Tip: Ensure the user running the worker is in the 'disk' group. "
                "Run: sudo usermod -aG disk $USER && logout"
            )
            logger.error(error_msg)
            self.task.status = "failed"
            self.task.error_message = error_msg
            self.task.save()
        except Exception as e:
            logger.error(f"Acquisition failed: {e}")
            self.task.status = "failed"
            self.task.error_message = str(e)
            self.task.save()
            return False

    def _acquire_raw(self):
        """Performs a raw DD-style acquisition with hashing"""
        # Improved size detection for block devices (/dev/sdX)
        try:
            total_size = os.path.getsize(self.internal_source)
            if total_size == 0:
                # Fallback for block devices
                with open(self.internal_source, "rb") as f:
                    f.seek(0, 2)
                    total_size = f.tell()
        except Exception as e:
            logger.warning(
                f"Standard size detection failed, attempting direct probe: {e}"
            )
            total_size = 0

        logger.info(f"Target size detected: {total_size} bytes")
        bytes_copied = 0
        start_time = time.time()

        last_update = time.time()
        with open(self.internal_source, "rb") as src, open(
            self.destination_path, "wb"
        ) as dst:
            while True:
                chunk = src.read(self.CHUNK_SIZE)
                if not chunk:
                    break

                # Write to destination
                dst.write(chunk)

                # Update Hashes
                self.hashes["md5"].update(chunk)
                self.hashes["sha256"].update(chunk)

                # Update Progress
                bytes_copied += len(chunk)

                now = time.time()
                if now - last_update > 0.5:
                    msg = self._update_progress(bytes_copied, total_size, start_time)
                    self.task.current_speed = msg
                    self.task.save()
                    last_update = now

    def _acquire_e01(self):
        """
        Implementation of E01-style segmented acquisition.
        Splits data into segments (default 2GB) and generates a forensic info file.
        """
        logger.info("Starting Segmented Forensic Acquisition (E01-Style)")

        # 1. Generate Forensic Metadata Sidecar
        info_path = self.destination_path + ".info"
        try:
            with open(info_path, "w") as info:
                info.write(f"ForensixOne Acquisition Log\n")
                info.write(f"===========================\n")
                info.write(
                    f"Case ID: {self.task.evidence.case.case_number if self.task.evidence else 'N/A'}\n"
                )
                info.write(f"Evidence: {self.logical_source}\n")
                info.write(f"Examiner: {self.task.created_by.username}\n")
                info.write(f"Acquisition Date: {timezone.now().isoformat()}\n")
                info.write(f"Source Path: {self.internal_source}\n")
                info.write(f"Format: Expert Witness (E01 Segmented)\n")
        except Exception as e:
            logger.warning(f"Failed to create forensic info file: {e}")

        # 2. Perform Segmented Acquisition
        self._acquire_segmented(segment_size=2 * 1024 * 1024 * 1024)  # 2GB Segments

    def _acquire_segmented(self, segment_size):
        """Internal helper for segmented data streaming"""
        try:
            total_size = os.path.getsize(self.internal_source)
            if total_size == 0:
                with open(self.internal_source, "rb") as f:
                    f.seek(0, 2)
                    total_size = f.tell()
        except:
            total_size = 0

        bytes_copied = 0
        start_time = time.time()
        last_update = time.time()
        segment_index = 1

        with open(self.internal_source, "rb") as src:
            while True:
                # Determine current segment path (e.g. image.E01, image.E02)
                ext = f".E{segment_index:02d}"
                seg_path = self.destination_path + ext

                seg_bytes = 0
                with open(seg_path, "wb") as dst:
                    while seg_bytes < segment_size:
                        chunk = src.read(min(self.CHUNK_SIZE, segment_size - seg_bytes))
                        if not chunk:
                            break

                        dst.write(chunk)
                        self.hashes["md5"].update(chunk)
                        self.hashes["sha256"].update(chunk)

                        seg_bytes += len(chunk)
                        bytes_copied += len(chunk)

                        now = time.time()
                        if now - last_update > 0.5:
                            msg = self._update_progress(
                                bytes_copied, total_size, start_time
                            )
                            self.task.current_speed = f"{msg} (Segment {segment_index})"
                            self.task.save()
                            last_update = now

                if seg_bytes == 0:  # End of source
                    if os.path.exists(seg_path) and os.path.getsize(seg_path) == 0:
                        os.remove(seg_path)
                    break

                segment_index += 1
                if seg_bytes < segment_size:  # Partial last segment
                    break

        # Override destination_path to the first segment for record keeping
        self.destination_path = self.destination_path + ".E01"

    def _update_progress(self, current, total, start_time):
        """Calculates speed and updates task progress"""
        elapsed = time.time() - start_time
        if elapsed > 0:
            speed_mb = (current / 1024 / 1024) / elapsed
            if total > 0:
                self.task.progress_percent = round((current / total) * 100, 2)
            else:
                self.task.progress_percent = 0.0  # Streaming mode
            return f"{speed_mb:.2f} MB/s"
        return "Calculating..."

    def _finalize_task(self):
        """Saves final hashes and completes task"""
        self.task.status = "completed"
        self.task.completed_at = timezone.now()
        self.task.progress_percent = 100.0
        self.task.calculated_md5 = self.hashes["md5"].hexdigest()
        self.task.calculated_sha256 = self.hashes["sha256"].hexdigest()
        self.task.save()

        # Update related evidence object
        if self.task.evidence:
            self.task.evidence.md5_hash = self.task.calculated_md5
            self.task.evidence.sha256_hash = self.task.calculated_sha256
            self.task.evidence.size_bytes = os.path.getsize(self.destination_path)
            self.task.evidence.file_path = self.destination_path
            self.task.evidence.save()

            # --- AUTOMATION: Trigger AI Analysis immediately after success ---
            try:
                from apps.analysis.models import Analysis
                from apps.analysis.tasks import start_evidence_analysis

                # Check if analysis already exists for this evidence (avoid duplicates if re-running)
                if not Analysis.objects.filter(evidence=self.task.evidence).exists():
                    logger.info(
                        f"Triggering automated AI Analysis for evidence: {self.task.evidence.name}"
                    )
                    analysis = Analysis.objects.create(
                        evidence=self.task.evidence, type="deep_file"
                    )
                    start_evidence_analysis.delay(analysis.id)
            except Exception as e:
                logger.error(f"Failed to auto-trigger analysis: {e}")
