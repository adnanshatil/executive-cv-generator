import re
import time
from pathlib import Path
from markdown_pdf import MarkdownPdf, Section
from .config import SOURCE_DIR

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
    """Compiles markdown text into an executive-styled PDF document using clean default spacing."""
    pdf = MarkdownPdf(toc_level=0)
    pdf.add_section(Section(markdown_content))
    pdf.save(str(filepath))