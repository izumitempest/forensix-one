import os
import zipfile
import tarfile
import sqlite3
import tempfile
import shutil
import re
import binascii
import hashlib
import logging
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from hachoir.core import config as hachoir_config

# Optional Forensic Libraries
try:
    import magic
except ImportError:
    magic = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

try:
    import pefile
except ImportError:
    pefile = None

from .models import Analysis, Artifact
from .ai_service import AICopilotService

logger = logging.getLogger(__name__)

# Silent hachoir
hachoir_config.quiet = True


class MetadataExtractor:
    """
    Pillar 3: Deep Extraction Engine - Layer 1 & 2
    Identifies file types and extracts internal metadata headers.
    """

    def __init__(self, analysis_id):
        self.analysis = Analysis.objects.get(id=analysis_id)
        self.evidence = self.analysis.evidence
        self.file_path = self.evidence.file_path

    def process(self):
        """Main entry point for deep metadata extraction"""
        try:
            self.analysis.status = "processing"
            self.analysis.started_at = timezone.now()
            self.analysis.save()

            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"Evidence file not found at {self.file_path}")

            # 1. Identify File Type
            mime = (
                magic.from_file(self.file_path, mime=True)
                if magic
                else "application/octet-stream"
            )
            desc = (
                magic.from_file(self.file_path)
                if magic
                else "Bit-stream data (magic library not installed)"
            )

            # Fallback for large raw images that might appear 'empty' to magic (e.g. zeroed MBR)
            if (desc == "empty" or not desc) and stats.st_size > 0:
                desc = "Raw Bit-stream Data"
                mime = "application/octet-stream"

            # 2. Extract File System Stats
            stats = os.stat(self.file_path)
            fs_metadata = {
                "size": stats.st_size,
                "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stats.st_atime).isoformat(),
                "mode": oct(stats.st_mode),
                "uid": stats.st_uid,
                "gid": stats.st_gid,
                "mime_type": mime,
                "magic_description": desc,
            }

            # 3. Extract Internal Metadata (Hachoir)
            internal_metadata = self._extract_hachoir_metadata()

            # 4. Generate Hex Preview (First 256 bytes)
            hex_preview = self._get_hex_preview()

            # Master Artifact for the evidence file itself
            artifact = Artifact.objects.create(
                evidence=self.evidence,
                analysis=self.analysis,
                type="file",
                name=os.path.basename(self.file_path),
                original_path=self.file_path,
                content=desc,
                metadata={**fs_metadata, **internal_metadata},
                file_system_metadata=fs_metadata,
                raw_hex_preview=hex_preview,
                timestamp=timezone.now(),
            )

            # Heuristic Partition Discovery for Disk Images
            if (
                "disk image" in desc.lower()
                or "bit-stream" in desc.lower()
                or fs_metadata["size"] > 100 * 1024 * 1024
            ):
                carver = DiskImageCarver(self.analysis.id)
                carver.process()

            self.analysis.progress_percent = 25.0
            self.analysis.save()

            logger.info(
                f"Layer 1 & 2 Metadata Extraction completed for {self.evidence.name}"
            )
            return True

        except Exception as e:
            logger.error(f"Deep Analysis Layer 1/2 failed: {e}")
            self.analysis.status = "failed"
            self.analysis.error_message = str(e)
            self.analysis.save()
            return False

    def _extract_hachoir_metadata(self):
        """Uses Hachoir to dive into file headers"""
        metadata_dict = {}
        try:
            parser = createParser(self.file_path)
            if not parser:
                return {}

            with parser:
                metadata = extractMetadata(parser)
                if metadata:
                    for line in metadata.exportPlaintext():
                        if ":" in line:
                            key, val = line.split(":", 1)
                            metadata_dict[key.strip().lower().replace("-", "_")] = (
                                val.strip()
                            )
        except Exception as e:
            logger.warning(f"Hachoir extraction failed for {self.file_path}: {e}")

        return metadata_dict

    def _get_hex_preview(self, bytes_count=256):
        """Generates a formatted hex dump preview"""
        try:
            with open(self.file_path, "rb") as f:
                chunk = f.read(bytes_count)
                hex_str = binascii.hexlify(chunk).decode("ascii")
                # Format into 16-byte lines
                lines = []
                for i in range(0, len(hex_str), 32):
                    line = hex_str[i : i + 32]
                    formatted_line = " ".join(
                        [line[j : j + 2] for j in range(0, len(line), 2)]
                    )
                    lines.append(formatted_line)
                return "\n".join(lines)
        except Exception:
            return "Hex preview unavailable."


class DiskImageCarver:
    """
    Forensic Partition Carver: Identifies filesystem structures in raw disk images.
    Used when a bit-stream image (USB/HDD) is processed.
    """

    def __init__(self, analysis_id):
        self.analysis = Analysis.objects.get(id=analysis_id)
        self.evidence = self.analysis.evidence
        self.file_path = self.evidence.file_path

    def process(self):
        """Scans the start of the image and common partition offsets for signatures"""
        try:
            with open(self.file_path, "rb") as f:
                # 1. Check for MBR/GPT
                sector_0 = f.read(512)
                if len(sector_0) == 512 and sector_0[510:512] == b"\x55\xaa":
                    self._create_artifact(
                        "Master Boot Record (MBR)",
                        "Standard MBR Partition Table detected at offset 0.",
                    )

                # 2. Check for GPT at offset 512
                f.seek(512)
                sector_1 = f.read(512)
                if b"EFI PART" in sector_1:
                    self._create_artifact(
                        "GUID Partition Table (GPT)",
                        "GPT Header detected at offset 512.",
                    )

                # 3. Signature Carving at common sector offsets
                # (Simple heuristic: checking first 1MB for filesystem headers)
                f.seek(0)
                buffer = f.read(1024 * 1024)

                # NTFS
                for match in re.finditer(
                    b"EB 52 90 4E 54 46 53", binascii.hexlify(buffer)
                ):
                    offset = match.start() // 2
                    self._create_artifact(
                        f"NTFS Partition (Offset: {offset})",
                        "NTFS Volume Boot Record found.",
                    )

                # FAT32
                if b"FAT32" in buffer:
                    for match in re.finditer(b"FAT32   ", buffer):
                        offset = match.start() - 0x52  # FAT32 OEM ID is at 0x52 in VBR
                        self._create_artifact(
                            f"FAT32 Partition (Offset: {offset})",
                            "FAT32 Volume Boot Record found.",
                        )

                # EXT4
                if b"\x53\xef" in buffer:  # Superblock magic
                    self._create_artifact(
                        "Ext4/Linux Partition",
                        "Linux Filesystem Superblock signature detected.",
                    )

            return True
        except Exception as e:
            logger.warning(f"Disk Carver failed: {e}")
            return False

    def _create_artifact(self, name, description):
        Artifact.objects.create(
            evidence=self.evidence,
            analysis=self.analysis,
            type="file",
            name=name,
            content=description,
            metadata={"source": "disk_carver", "carved": True},
        )


class ContentScanner:
    """
    Pillar 3: Deep Extraction Engine - Layer 3 (Universal)
    Carves intelligence from ANY file using specialized parsers and heuristics.
    """

    def __init__(self, analysis_id):
        self.analysis = Analysis.objects.get(id=analysis_id)
        self.evidence = self.analysis.evidence
        self.main_file_path = self.evidence.file_path
        self._temp_dir = None

    def process(self):
        """Orchestrates universal content scanning"""
        try:
            # 1. Recursive Unpacking if archive
            files_to_scan = [
                (self.main_file_path, os.path.basename(self.main_file_path))
            ]

            if self._is_archive(self.main_file_path):
                unpacked = self._unpack_to_temp(self.main_file_path)
                files_to_scan.extend(unpacked)

            # 2. Sequential Scanning of all identified files
            for file_path, display_name in files_to_scan:
                self._scan_single_file(file_path, display_name)

            # 3. Cleanup
            if self._temp_dir and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)

            self.analysis.progress_percent = 75.0
            self.analysis.save()
            return True

        except Exception as e:
            logger.error(f"Universal Scan failed: {e}")
            return False

    def _scan_single_file(self, path, name):
        """Universal dispatcher for a single file/blob"""
        mime = self._get_mime(path)
        logger.info(f"Scanning {name} (MIME: {mime})")

        # A. Universal Strings & Regex Carving (IPs, Emails, URLs)
        self._carve_intelligence(path, name)

        # B. Specialized Content Parsers
        if "sqlite" in mime or path.endswith((".db", ".sqlite")):
            self._carve_sqlite(path, name)

        elif "image" in mime and pytesseract:
            self._extract_ocr(path, name)

        elif "pdf" in mime and PyPDF2:
            self._extract_pdf(path, name)

        elif ("wordprocessingml" in mime or path.endswith(".docx")) and docx:
            self._extract_docx(path, name)

        elif "text" in mime or path.endswith((".txt", ".log", ".ini", ".conf")):
            self._extract_text(path, name)

        elif (
            "executable" in mime
            or "sharedlib" in mime
            or path.endswith((".exe", ".dll", ".bin"))
        ):
            self._analyze_executable(path, name)

        # Universal: Strings extraction for ANY file that isn't plain text
        if "text" not in mime:
            self._extract_strings(path, name)

    def _analyze_executable(self, path, name):
        """Deep PE/ELF Analysis (if pefile is available)"""
        try:
            if pefile:
                pe = pefile.PE(path)
                imports = []
                if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
                    for entry in pe.DIRECTORY_ENTRY_IMPORT:
                        for imp in entry.imports:
                            if imp.name:
                                imports.append(
                                    imp.name.decode("ascii", errors="ignore")
                                )

                sections = []
                for section in pe.sections:
                    sections.append(
                        {
                            "name": section.Name.decode("ascii", errors="ignore").strip(
                                "\x00"
                            ),
                            "virt_size": section.Misc_VirtualSize,
                            "raw_size": section.SizeOfRawData,
                        }
                    )

                Artifact.objects.create(
                    evidence=self.evidence,
                    analysis=self.analysis,
                    type="file",
                    name=f"PE Headers: {name}",
                    content=f"Executable Analysis for {name}",
                    metadata={
                        "machine": hex(pe.FILE_HEADER.Machine),
                        "sections": sections[:5],
                        "imports_count": len(imports),
                        "suspicious_imports": [
                            i
                            for i in imports
                            if i
                            in [
                                "CreateRemoteThread",
                                "WriteProcessMemory",
                                "VirtualAllocEx",
                            ]
                        ],
                    },
                )
        except Exception as e:
            logger.debug(f"PE analysis failed: {e}")

    def _extract_strings(self, path, name):
        """Universal Forensic Strings: Extracts ASCII sequences > 6 chars"""
        try:
            with open(path, "rb") as f:
                # Read up to 2MB for strings
                chunk = f.read(1024 * 1024 * 2)
                # Regex for printable ASCII
                found = re.findall(b"[\x20-\x7e]{7,}", chunk)
                if found:
                    cleaned = [s.decode("ascii", errors="ignore") for s in found[:200]]
                    Artifact.objects.create(
                        evidence=self.evidence,
                        analysis=self.analysis,
                        type="file",
                        name=f"Strings: {name}",
                        content="\n".join(cleaned),
                        metadata={"source": "strings_carver", "count": len(found)},
                    )
        except Exception:
            pass

    def _extract_text(self, path, name):
        """Standard text file extraction"""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)  # Cap at 10KB
                if content.strip():
                    Artifact.objects.create(
                        evidence=self.evidence,
                        analysis=self.analysis,
                        type="file",
                        name=f"Text: {name}",
                        content=content,
                        metadata={"source": "text_parser"},
                    )
        except Exception:
            pass

    def _carve_intelligence(self, path, name):
        """Forensic String Carving: Finds IPs, Emails, and URLs in binary or text"""
        try:
            with open(path, "rb") as f:
                content = f.read(1024 * 512)  # Scan first 512KB for speed
                text = content.decode("ascii", errors="ignore")

                # Regex patterns
                ips = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", text)
                emails = re.findall(
                    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text
                )
                urls = re.findall(r"https?://[^\s<>\"']+", text)

                if ips or emails or urls:
                    Artifact.objects.create(
                        evidence=self.evidence,
                        analysis=self.analysis,
                        type="network_log",
                        name=f"Intelligence: {name}",
                        content=f"Extracted Indicators from {name}",
                        metadata={
                            "ips": list(set(ips))[:10],
                            "emails": list(set(emails))[:10],
                            "urls": list(set(urls))[:10],
                        },
                    )
        except Exception as e:
            logger.warning(f"Intelligence carving failed for {name}: {e}")

    def _extract_ocr(self, path, name):
        """Text extraction from images"""
        try:
            text = pytesseract.image_to_string(Image.open(path))
            if text.strip():
                Artifact.objects.create(
                    evidence=self.evidence,
                    analysis=self.analysis,
                    type="document",
                    name=f"OCR: {name}",
                    content=text,
                    metadata={"source": "tesseract_ocr"},
                )
        except Exception as e:
            logger.debug(f"OCR failed for {name}: {e}")

    def _extract_pdf(self, path, name):
        """Text extraction from PDF"""
        try:
            text = ""
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages[:10]:  # First 10 pages
                    text += page.extract_text() + "\n"

            if text.strip():
                Artifact.objects.create(
                    evidence=self.evidence,
                    analysis=self.analysis,
                    type="document",
                    name=f"PDF Text: {name}",
                    content=text[:5000],  # Cap size
                    metadata={"pages": len(reader.pages)},
                )
        except Exception as e:
            logger.debug(f"PDF extract failed: {e}")

    def _extract_docx(self, path, name):
        """Text extraction from Word"""
        try:
            doc = docx.Document(path)
            text = "\n".join([p.text for p in doc.paragraphs])
            if text.strip():
                Artifact.objects.create(
                    evidence=self.evidence,
                    analysis=self.analysis,
                    type="document",
                    name=f"Word Text: {name}",
                    content=text[:5000],
                    metadata={"paragraphs": len(doc.paragraphs)},
                )
        except Exception as e:
            logger.debug(f"Docx extract failed: {e}")

    def _carve_sqlite(self, path, name):
        """SQLite artifacts (Chrome/WhatsApp/Generic)"""
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall()]

            # Simple heuristic: If it has 'urls', it might be browser history
            if "urls" in tables:
                cursor.execute("SELECT url, title FROM urls LIMIT 20")
                for url, title in cursor.fetchall():
                    Artifact.objects.create(
                        evidence=self.evidence,
                        analysis=self.analysis,
                        type="browser_history",
                        name=f"History: {title or 'Visit'}",
                        content=url,
                    )
            conn.close()
        except Exception:
            pass

    def _is_archive(self, path):
        return path.endswith((".zip", ".tar", ".gz"))

    def _unpack_to_temp(self, path):
        """Unpacks archive to a temporary directory for scanning"""
        self._temp_dir = tempfile.mkdtemp(prefix="forensix_")
        results = []
        try:
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path, "r") as z:
                    z.extractall(self._temp_dir)
            elif tarfile.is_tarfile(path):
                with tarfile.open(path, "r:*") as t:
                    t.extractall(self._temp_dir)

            for root, _, files in os.walk(self._temp_dir):
                for f in files:
                    results.append((os.path.join(root, f), f))
        except Exception as e:
            logger.warning(f"Unpack failed: {e}")
        return results

    def _get_mime(self, path):
        if magic:
            return magic.from_file(path, mime=True)
        return "application/octet-stream"


class AISummarizer:
    """
    Pillar 3: Deep Extraction Engine - Layer 4
    Performs AI-driven summarization and anomaly detection on extracted artifacts.
    """

    def __init__(self, analysis_id):
        self.analysis = Analysis.objects.get(id=analysis_id)
        self.ai_service = AICopilotService()

    def process(self):
        """Processes all artifacts for this analysis through the AI Copilot"""
        logger.info(f"Starting AI Enrichment for Analysis {self.analysis.id}")
        try:
            artifacts = self.analysis.artifacts.all()
            total = artifacts.count()

            for i, artifact in enumerate(artifacts):
                # Anomaly Detection (Passing name and content for better heuristics)
                anomaly_data = self.ai_service.identify_anomalies(
                    {
                        **artifact.metadata,
                        "name": artifact.name,
                        "content_preview": str(artifact.content)[:1000],
                    }
                )
                artifact.is_suspicious = anomaly_data["is_suspicious"]
                artifact.ai_labels = anomaly_data["reasons"]
                artifact.risk_score = anomaly_data["risk_score"]

                # Dynamic Summarization (only for text-heavy or important artifacts)
                if artifact.type in ["chat", "browser_history", "file"]:
                    artifact.ai_summary = self.ai_service.answer_question(
                        f"Summarize this forensic artifact: {artifact.name}", [artifact]
                    )

                artifact.save()

                # Update progress within Layer 4 (80% to 100%)
                progress = 80.0 + (float(i) / total * 20.0) if total > 0 else 100.0
                self.analysis.progress_percent = progress
                self.analysis.save()

            return True

        except Exception as e:
            logger.error(f"AI Enrichment failed: {e}")
            return False

