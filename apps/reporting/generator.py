import logging
import json
from django.template.loader import render_to_string
try:
    from weasyprint import HTML
except ImportError:
    HTML = None
    logger = logging.getLogger(__name__)
    logger.warning("WeasyPrint not found. PDF generation will be mocked.")
from .models import Report
from django.conf import settings
import os

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Pillar 4: Smart Reporting & Export - Generation Logic"""
    
    def __init__(self, report):
        self.report = report
        self.case = report.case

    def generate_pdf(self):
        """
        Generates a PDF report using a template and current case data.
        """
        context = {
            'case': self.case,
            'report': self.report,
            'evidence_list': self.case.evidence.all(),
            'summary': self.report.generated_content or "No summary provided.",
        }
        
        # Use simple fallback template if none specified
        template_name = 'reports/default_report.html'
        if self.report.template:
            # Logic to use dynamic template string or path
            pass
            
        try:
            html_string = render_to_string(template_name, context)
            
            # Save PDF
            filename = f"report_{self.report.id}.pdf"
            file_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if HTML:
                HTML(string=html_string).write_pdf(file_path)
            else:
                with open(file_path, 'w') as f:
                    f.write("MOCK PDF CONTENT: " + html_string)
            
            self.report.file_path = file_path
            self.report.save()
            return file_path
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            return None

    def export_as_case(self):
        """
        Exports the investigation as a CASE (Cyber-investigation Analysis Standard Expression) JSON file.
        """
        case_data = {
            "@context": "https://casework.org/context/case-v1.0.0.jsonld",
            "@type": "Investigation",
            "name": self.case.name,
            "description": self.case.description,
            "evidence": []
        }
        
        for ev in self.case.evidence.all():
            case_data["evidence"].append({
                "@type": "Trace",
                "name": ev.name,
                "hashes": {
                    "md5": ev.md5_hash,
                    "sha256": ev.sha256_hash
                }
            })
            
        return json.dumps(case_data, indent=2)
