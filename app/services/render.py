import logging
import os
import subprocess
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

async def render_to_pdf(html_path: Path, pdf_path: Path) -> str:
    """
    Render HTML file to PDF using WeasyPrint or wkhtmltopdf as fallback.
    
    Args:
        html_path: Path to the HTML file
        pdf_path: Path to save the PDF file
        
    Returns:
        URL of the generated PDF file
    """
    try:
        # Try using WeasyPrint first
        try:
            import weasyprint
            logger.info(f"Rendering PDF with WeasyPrint: {pdf_path}")
            
            # Read HTML content
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Render to PDF
            weasyprint.HTML(string=html_content).write_pdf(pdf_path)
            logger.info(f"PDF generated successfully with WeasyPrint: {pdf_path}")
            
        except (ImportError, Exception) as e:
            logger.warning(f"WeasyPrint failed: {e}. Falling back to wkhtmltopdf...")
            
            # Fall back to wkhtmltopdf
            result = subprocess.run(
                ["wkhtmltopdf", str(html_path), str(pdf_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"wkhtmltopdf error: {result.stderr}")
                raise Exception(f"wkhtmltopdf failed: {result.stderr}")
            
            logger.info(f"PDF generated successfully with wkhtmltopdf: {pdf_path}")
        
        # Generate a URL for the PDF
        file_name = os.path.basename(pdf_path)
        
        if settings.WEBHOOK_HOST:
            # In production with a webhook, return a public URL
            pdf_url = f"{settings.WEBHOOK_HOST}/reports/{file_name}"
        else:
            # In local mode, return a file path
            pdf_url = f"file://{pdf_path}"
        
        return pdf_url
        
    except Exception as e:
        logger.exception(f"Failed to render PDF: {e}")
        
        # If PDF rendering fails, return the HTML path as fallback
        file_name = os.path.basename(html_path)
        
        if settings.WEBHOOK_HOST:
            return f"{settings.WEBHOOK_HOST}/reports/{file_name}"
        else:
            return f"file://{html_path}" 