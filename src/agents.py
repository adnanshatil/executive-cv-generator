import re
import requests
from .config import OLLAMA_URL, OLLAMA_MODEL
from .utils import clean_dashes

def call_native_ollama(prompt: str, system_prompt: str = "You are an executive CV writer.") -> str:
    """Handles direct HTTP communication with local Ollama engine."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "options": {
            "num_ctx": 8192,
            "num_predict": 4096,
            "temperature": 0.20,
            "top_p": 0.95,
            "thinking": False
        },
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    raw_text = response.json().get("message", {}).get("content", "").strip()
    
    # Strip <thought> tags just in case
    clean_text = re.sub(r'<\|channel\|>thought\s*[\s\S]*?(?=\n\n|\Z)', '', raw_text)
    clean_text = re.sub(r'<\|think\|>[\s\S]*?</\|think\|>', '', clean_text)
    return clean_dashes(clean_text)

# --- Agent Tasks ---

def extract_metadata(requirements: str, header_source: str) -> dict:
    prompt = f"""
    Target Job Requirements:\n{requirements}\n\nCandidate Header & Base Summary:\n{header_source}
    Instructions: Extract Company Name and Job Role. Write Title Line and Executive Summary (8-10 sentences).
    Do NOT use long em-dashes (—). Use standard hyphens (-) if needed.
    OUTPUT FORMAT:
    COMPANY_NAME: [Extracted Company]
    JOB_ROLE: [Extracted Title]
    TITLE_LINE: [Pipe-Delimited Title Line]
    SUMMARY: [Executive Summary Paragraph]
    """
    output = call_native_ollama(prompt, "You are a senior executive resume strategist.")
    
    return {
        "company": re.search(r"COMPANY_NAME:\s*(.*)", output, re.IGNORECASE).group(1).strip() if "COMPANY_NAME:" in output else "Target Company",
        "role": re.search(r"JOB_ROLE:\s*(.*)", output, re.IGNORECASE).group(1).strip() if "JOB_ROLE:" in output else "Target Position",
        "title_line": re.search(r"TITLE_LINE:\s*(.*)", output, re.IGNORECASE).group(1).strip() if "TITLE_LINE:" in output else "Executive Leader",
        "summary": re.search(r"SUMMARY:\s*(.*)", output, re.IGNORECASE | re.DOTALL).group(1).strip() if "SUMMARY:" in output else output
    }

def generate_core_competencies(requirements: str, anchor: str, core_source: str) -> str:
    prompt = f"""
    Requirements:\n{requirements}\n\nAnchor:\n{anchor}\n\nSource:\n{core_source}
    Instructions:\nSelect 12 capabilities across 3 unique sub-headers with 4 short phrases under each.
    Do NOT use long em-dashes (—).
    """
    return call_native_ollama(prompt, "Principal Enterprise Architect.")

def generate_tech_stack(requirements: str, anchor: str, tech_source: str) -> str:
    prompt = f"""
    Target Job Requirements:
    {requirements}

    Anchor Context:
    {anchor}

    Candidate Master Technical Competencies Source:
    {tech_source}

    INSTRUCTIONS:
    1. Filter and reorganize the candidate's Master Technical Competencies to match the target job's priorities.
    2. Output 7-8 skill categories formatted as `- Category: Values`. Elevate top job tech. Do NOT use long em-dashes (—).
    3. Include all relevant tools, languages, and frameworks from the source file.
    4. CRITICAL: Do NOT write paragraph explanations, meta-introductions, or recruiter summaries. Output ONLY markdown category headings and item lists.
    """
    return call_native_ollama(prompt, "Senior technical recruiter.")

def generate_experience(requirements: str, anchor: str, exp_source: str) -> str:
    prompt = f"""
    Target Job Requirements:
    {requirements}

    Anchor Context:
    {anchor}

    Candidate Master Professional Experience Source:
    {exp_source}

    INSTRUCTIONS:
    1. Select and tailor EXACTLY 10 bullet points from the Candidate's Master Source file that best match the target job requirements.
    2. RETAIN the specific metrics, project names (e.g., Reindeer), technology names (e.g., Anaplan, Semarchy xDM, SAP S/4HANA, Solace), and percentages from the original source bullets.
    3. Do NOT make the bullets generic or abstract. Keep them grounded in the exact operational detail provided in the source file.
    4. Format each line starting with a single `- `.
    """
    return call_native_ollama(prompt, "You are an executive ATS resume optimizer.")

def generate_cover_letter(requirements: str, anchor: str, company: str, role: str, letter_source: str) -> str:
    prompt = f"""
    Target Company: {company}
    Target Role: {role}
    Requirements:
    {requirements}
    Anchor Context:
    {anchor}
    Base Template:
    {letter_source}

    Instructions: Write a complete cover letter (~400 words across 4-5 paragraphs).
    Do NOT include candidate header lines at top. Do NOT use long em-dashes (—).

    Format:
    Subject: Application for {role} at {company}

    Dear Hiring Manager,

    [Letter Content]

    Best regards,
    Adnan Shatil
    """
    return call_native_ollama(prompt, "Executive copywriter.")