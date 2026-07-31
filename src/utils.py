import re
import time
from pathlib import Path
from markdown_pdf import MarkdownPdf, Section
from .config import CSS_FILE, SOURCE_DIR

class Timer:
    """Context manager for tracking execution time."""
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, *args):
        self.duration = time.time() - self.start

def clean_dashes(text: str) -> str:
    """Removes em-dashes and en-dashes from output."""
    if not text:
        return ""
    text = text.replace("—", " - ").replace("–", "-")
    return re.sub(r' +', ' ', text).strip()

def load_source_file(filename: str) -> str:
    """Loads markdown template files from the source directory."""
    path = SOURCE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing required source file: {path}")
    return path.read_text(encoding="utf-8").strip()

def save_text(filepath: Path, content: str):
    """Saves raw text or markdown to a file."""
    filepath.write_text(content, encoding="utf-8")

def save_pdf(filepath: Path, markdown_content: str):
    """Compiles markdown text into a compact, executive-styled PDF document."""
    
    # 1. Read CSS stylesheet from source/styles.css
    css_content = ""
    if CSS_FILE.exists():
        css_content = CSS_FILE.read_text(encoding="utf-8")
    
    # 2. Embed CSS directly via standard HTML <style> block
    if css_content:
        styled_content = f"<style>\n{css_content}\n</style>\n\n{markdown_content}"
    else:
        styled_content = markdown_content

    # 3. Instantiate MarkdownPdf (zero keyword argument conflicts)
    pdf = MarkdownPdf(toc_level=0)
    pdf.add_section(Section(styled_content))
    
    # 4. Save PDF
    pdf.save(str(filepath))