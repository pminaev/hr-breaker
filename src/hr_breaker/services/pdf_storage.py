import re
from datetime import datetime
from pathlib import Path

from hr_breaker.config import get_settings
from hr_breaker.models import GeneratedPDF


def sanitize_filename(name: str) -> str:
    """Convert name to safe filename component."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


class PDFStorage:
    """Storage for generated PDFs - folder-based, no index file."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir if output_dir is not None else get_settings().output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_path(self, prefix: str, company: str) -> Path:
        """Generate PDF path: {prefix}_{company}.pdf"""
        filename = f"{prefix}_{sanitize_filename(company)}.pdf"
        return self.output_dir / filename

    def generate_debug_dir(self, company: str, role: str | None = None) -> Path:
        """Generate debug directory: output/debug_{company}_{role}/"""
        parts = ["debug", sanitize_filename(company)]
        if role:
            parts.append(sanitize_filename(role))
        debug_dir = self.output_dir / "_".join(parts)
        debug_dir.mkdir(parents=True, exist_ok=True)
        return debug_dir

    def list_all(self) -> list[GeneratedPDF]:
        """Scan output folder for PDFs."""
        records = []
        for pdf_path in self.output_dir.glob("*.pdf"):
            # Parse filename: CV_company.pdf or CL_company.pdf
            stem = pdf_path.stem
            prefix, _, rest = stem.partition("_")
            if prefix in ("CV", "CL") and rest:
                company = rest.replace("_", " ").title()
                job_title = prefix
            else:
                company = stem.title()
                job_title = "Unknown"
            first_name, last_name = None, None

            records.append(GeneratedPDF(
                path=pdf_path,
                source_checksum="",
                company=company,
                job_title=job_title,
                timestamp=datetime.fromtimestamp(pdf_path.stat().st_mtime),
                first_name=first_name,
                last_name=last_name,
            ))

        # Sort by timestamp (newest first for display)
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records

    def save_record(self, pdf: GeneratedPDF) -> None:
        """No-op - metadata derived from filename/mtime."""
        pass
