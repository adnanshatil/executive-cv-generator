import re
import requests
from bs4 import BeautifulSoup
from .config import LINKEDIN_DIR
from .utils import save_text

# Regex pattern specifically checking for valid LinkedIn job URLs
LINKEDIN_JOB_URL_PATTERN = r'https?://(?:[a-z]{2,3}\.)?linkedin\.com/jobs/(?:view/\d+|search/?[^\s]+)'

def is_valid_linkedin_url(input_param: str) -> bool:
    """Validates if the user input contains a recognized LinkedIn job URL format."""
    return bool(re.search(LINKEDIN_JOB_URL_PATTERN, input_param.strip(), re.IGNORECASE))

def fetch_job_requirements(input_param: str) -> tuple[str, str, str]:
    input_str = input_param.strip()
    
    # Strictly enforce valid LinkedIn URL format
    if not is_valid_linkedin_url(input_str):
        raise ValueError(
            "Invalid input format! Please provide a valid LinkedIn Job URL.\n"
            "Example: `https://www.linkedin.com/jobs/view/1234567890/`"
        )

    url_match = re.search(r'https?://[^\s]+', input_str)
    url = url_match.group(0)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title_meta = soup.find("meta", property="og:title")
    title_str = title_meta["content"] if title_meta else ""
    clean_title = re.sub(r'\|\s*LinkedIn', '', title_str, flags=re.IGNORECASE).strip()
    
    company_name, role_name = "Target Company", "Target Role"
    hiring_match = re.search(r'^(.*?)\s+hiring\s+(.*?)\s+in\s+', clean_title, re.IGNORECASE)
    
    if hiring_match:
        company_name = hiring_match.group(1).strip()
        role_name = hiring_match.group(2).strip()
    elif " at " in clean_title:
        parts = clean_title.split(" at ", 1)
        role_name = parts[0].strip()
        company_name = re.sub(r'\s+in\s+.*$', '', parts[1], flags=re.IGNORECASE).strip()

    desc_div = soup.find("div", {"class": "show-more-less-html__markup"}) or soup.find("div", {"id": "job-details"})
    job_text = desc_div.get_text(separator="\n").strip() if desc_div else soup.get_text(separator="\n").strip()

    if not job_text or len(job_text) < 50:
        raise ValueError("Failed to extract job content from the provided LinkedIn URL. Please make sure the post is public.")

    clean_comp_fn = re.sub(r'[^a-zA-Z0-9]', '_', company_name).strip('_').lower()
    clean_role_fn = re.sub(r'[^a-zA-Z0-9]', '_', role_name).strip('_').lower()
    
    saved_filepath = LINKEDIN_DIR / f"{clean_comp_fn}_{clean_role_fn}.txt"
    save_text(saved_filepath, f"Company: {company_name}\nRole: {role_name}\n\n{job_text}")

    return company_name, role_name, job_text