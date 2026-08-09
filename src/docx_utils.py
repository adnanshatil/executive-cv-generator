import re
import subprocess
from pathlib import Path
from docxtpl import DocxTemplate
from .config import SOURCE_DIR, SOFFICE_PATH

TEMPLATE_FILE = SOURCE_DIR / "AdnanShatilCV.docx"

def parse_competencies_to_dict(raw_text: str) -> dict:
    """
    Strips headers/bullets and maps up to 12 competencies into 
    individual keys matching the static 4x3 Word table: r1c1 ... r4c3.
    """
    lines = raw_text.splitlines()
    bullet_items = []
    
    for line in lines:
        cleaned = line.strip()
        # Skip section titles/subheaders (e.g., '### Business Realization') or empty lines
        if cleaned.startswith('#') or not cleaned:
            continue
            
        # Clean bullets (*, -, •), numbers, and markdown bolding
        clean_item = re.sub(r'[*•\d\.\-]+\s*', '', cleaned).replace('**', '').strip()
        if clean_item:
            bullet_items.append(clean_item)

    # Split into 3 columns of 4 items each
    col1 = bullet_items[0:4]
    col2 = bullet_items[4:8]
    col3 = bullet_items[8:12]

    # Ensure each column has 4 items (pad with empty string if Ollama returned fewer)
    while len(col1) < 4: col1.append("")
    while len(col2) < 4: col2.append("")
    while len(col3) < 4: col3.append("")

    # Return flat key-value pairs matching the Word template tags
    return {
        "r1c1": col1[0], "r1c2": col2[0], "r1c3": col3[0],
        "r2c1": col1[1], "r2c2": col2[1], "r2c3": col3[1],
        "r3c1": col1[2], "r3c2": col2[2], "r3c3": col3[2],
        "r4c1": col1[3], "r4c2": col2[3], "r4c3": col3[3],
    }

def convert_docx_to_pdf_libreoffice(docx_path: Path) -> Path:
    """Converts a .docx file to .pdf using LibreOffice CLI."""
    pdf_path = docx_path.with_suffix(".pdf")
    
    cmd = [
        SOFFICE_PATH,
        "--headless",
        "--convert-to",
        "pdf",
        str(docx_path),
        "--outdir",
        str(docx_path.parent)
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice PDF conversion failed: {result.stderr}")
        
    return pdf_path

def render_docx_template(output_docx_path: Path, context: dict) -> tuple[Path, Path]:
    """Renders the docx template and converts it to PDF."""
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"Missing master Word template at {TEMPLATE_FILE}")

    # 1. Fill template
    doc = DocxTemplate(TEMPLATE_FILE)
    doc.render(context)
    doc.save(output_docx_path)

    # 2. Convert to PDF
    output_pdf_path = convert_docx_to_pdf_libreoffice(output_docx_path)

    return output_docx_path, output_pdf_path