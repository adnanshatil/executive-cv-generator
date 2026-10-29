import re
import requests
from .config import OLLAMA_URL, OLLAMA_MODEL
from .utils import clean_dashes, load_source_file

def call_native_ollama(
    prompt: str,
    system_prompt: str = "You are an executive CV writer.",
    num_predict: int = 500,
    num_ctx: int = 4096,
    num_thread: int = 8,
    temperature: float = 0.20,
    stop: list[str] = None
) -> str:
    """Handles direct HTTP communication with Ollama engine on 192.168.2.2."""
    options = {
        "num_ctx": num_ctx,
        "num_predict": num_predict,
        "num_thread": num_thread,     # Matches 8 physical cores on AMD Ryzen 7 5700G
        "temperature": temperature,
        "top_p": 0.95,
        "thinking": False
    }
    if stop:
        options["stop"] = stop

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "think": False,                 # Explicitly disables thinking mode in Ollama
        "options": options,
        "keep_alive": "1h",             # Keeps model loaded in RAM for 1 hour
        "stream": False
    }

    # Timeout: 15s connect, 300s read
    response = requests.post(OLLAMA_URL, json=payload, timeout=(15, 300))
    response.raise_for_status()
    raw_text = response.json().get("message", {}).get("content", "").strip()
    
    # Strip thinking and internal reasoning tags
    clean_text = re.sub(r'<\|channel\|>thought\s*[\s\S]*?(?=\n\n|\Z)', '', raw_text)
    clean_text = re.sub(r'<\|think\|>[\s\S]*?</\|think\|>', '', clean_text)
    clean_text = re.sub(r'<think>[\s\S]*?</think>', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'<thought>[\s\S]*?</thought>', '', clean_text, flags=re.IGNORECASE)

    # Strip wrapping markdown code fences if the entire output was enclosed in ```
    fence_match = re.match(r'^```(?:markdown)?\s*\n([\s\S]*?)\n```\s*$', clean_text.strip(), flags=re.IGNORECASE)
    if fence_match:
        clean_text = fence_match.group(1).strip()

    return clean_dashes(clean_text)

# --- Agent Tasks ---

def extract_metadata(requirements: str, header_source: str) -> dict:
    prompt = f"""Target Job Requirements:
{requirements}

Candidate Header & Base Summary:
{header_source}

INSTRUCTIONS:
1. Extract Company Name and Job Role.
2. Write a Title Line (pipe-delimited) and Executive Summary (4-5 punchy sentences).
3. Do NOT use long em-dashes (—). Use standard hyphens (-) if needed.
4. Output ONLY the 4 fields in the EXACT format below. Do NOT write any introduction, commentary, or markdown fences.

OUTPUT FORMAT:
COMPANY_NAME: [Extracted Company]
JOB_ROLE: [Extracted Title]
TITLE_LINE: [Pipe-Delimited Title Line]
SUMMARY: [Executive Summary Paragraph]"""

    output = call_native_ollama(
        prompt=prompt,
        system_prompt="You are a senior executive resume strategist. Output strictly the requested fields without commentary.",
        num_predict=350,
        num_ctx=4096
    )
    
    return {
        "company": re.search(r"COMPANY_NAME:\s*(.*)", output, re.IGNORECASE).group(1).strip() if "COMPANY_NAME:" in output else "Target Company",
        "role": re.search(r"JOB_ROLE:\s*(.*)", output, re.IGNORECASE).group(1).strip() if "JOB_ROLE:" in output else "Target Position",
        "title_line": re.search(r"TITLE_LINE:\s*(.*)", output, re.IGNORECASE).group(1).strip() if "TITLE_LINE:" in output else "Executive Leader",
        "summary": re.search(r"SUMMARY:\s*(.*)", output, re.IGNORECASE | re.DOTALL).group(1).strip() if "SUMMARY:" in output else output
    }

def generate_tech_stack(requirements: str, anchor: str, tech_source: str) -> str:
    prompt = f"""Target Job Requirements:
{requirements}

Anchor Context:
{anchor}

Candidate Master Technical Competencies Source:
{tech_source}

INSTRUCTIONS:
1. Filter, prioritize, and reorganize the candidate's skills to match the target job's key tech stack.
2. Output exactly 8 to 10 categories.
3. Every category MUST be formatted on a SINGLE line as: `- Category: value1, value2, value3`.
4. Values within each category MUST be comma-separated on that same line.
5. Do NOT create multi-line bullet points or line breaks for items under a category.
6. Do NOT use markdown section headers (`###`), em-dashes (`—`), introductions, or notes.
7. Output ONLY the formatted category lines.

EXACT OUTPUT FORMAT TEMPLATE:
- Cloud & Infrastructure: AWS, Azure, GCP, Kubernetes, Docker, Terraform
- Architecture & Design: Microservices, Event-Driven Architecture, Domain-Driven Design (DDD), TOGAF
- Programming & Scripting: Python, TypeScript, Go, Java, Bash, SQL
- CI/CD & Automation: GitHub Actions, GitLab CI, ArgoCD, Helm, Ansible"""

    return call_native_ollama(
        prompt=prompt,
        system_prompt="You are a senior technical recruiter. Output strictly the single-line category bullets without commentary.",
        num_predict=400,
        num_ctx=4096
    )

def generate_experience(requirements: str, anchor: str, exp_source: str) -> str:
    prompt = f"""Target Job Requirements:
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
5. Output ONLY the 10 bullet points. Do NOT include greetings, section headers, or concluding remarks."""

    return call_native_ollama(
        prompt=prompt,
        system_prompt="You are an executive ATS resume optimizer. Output strictly 10 impact-focused bullet points without commentary.",
        num_predict=650,
        num_ctx=4096
    )

def generate_cover_letter(requirements: str, anchor: str, company: str, role: str, letter_source: str) -> str:
    prompt = f"""Target Company: {company}
Target Role: {role}
Requirements:
{requirements}
Anchor Context:
{anchor}
Base Template:
{letter_source}

INSTRUCTIONS:
1. Write a complete, compelling cover letter (~400 words across 4-5 paragraphs).
2. Do NOT include candidate header lines at top. Do NOT use long em-dashes (—).
3. Output ONLY the letter text starting with 'Subject:' and ending with 'Adnan Shatil'. Do NOT add preamble or commentary.

Format:
Subject: Application for {role} at {company}

Dear Hiring Manager,

[Letter Content]

Best regards,
Adnan Shatil"""

    return call_native_ollama(
        prompt=prompt,
        system_prompt="You are an executive copywriter. Output strictly the cover letter text without introduction or notes.",
        num_predict=700,
        num_ctx=4096
    )

def evaluate_role_confidence(
    requirements: str,
    company: str,
    role: str,
    tech_source: str = None,
    exp_source: str = None,
    check_language: bool = True
) -> dict:
    """
    Evaluates how closely a scraped job matches Adnan Shatil's actual master profile,
    specifically comparing requirements against technicalcompetencies.md and professionalexperiences.md.
    Returns a dict with 'confidence' (int 0-100), optional 'mandatory_finnish' (bool), and 'reason' (str).
    """
    clean_req = requirements[:3500].strip() if requirements else ""

    if not tech_source:
        tech_source = load_source_file("technicalcompetencies.md")
    if not exp_source:
        exp_source = load_source_file("professionalexperiences.md")

    lang_instruction = """3. Language Requirement Check:
   - Check if this job posting strictly requires mandatory Finnish language skills (e.g. ad is written in Finnish, or states fluent/native Finnish is required/mandatory/edellytys/kielitaitovaatimus).
   - If English is accepted or Finnish is merely optional/preferred, answer NO.
   - If Finnish is strictly required or mandatory, answer YES.
4. Assign a match confidence score from 0 to 100%.
5. Output strictly in the exact format below without any conversational preamble or notes.

OUTPUT FORMAT:
CONFIDENCE: [0-100]
MANDATORY_FINNISH: [YES/NO]
REASON: [1-2 sentence concise explanation highlighting specific technical/experience match points or critical gaps]""" if check_language else """3. Assign a match confidence score from 0 to 100%.
4. Output strictly in the exact format below without any conversational preamble or notes.

OUTPUT FORMAT:
CONFIDENCE: [0-100]
REASON: [1-2 sentence concise explanation highlighting specific technical/experience match points or critical gaps]"""

    prompt = f"""Target Company: {company}
Target Role: {role}

Target Job Requirements:
{clean_req}

Candidate Master Technical Competencies Source:
{tech_source}

Candidate Master Professional Experience Source:
{exp_source}

INSTRUCTIONS:
You are an executive technology recruiter evaluating this candidate for the target job.
1. Compare the target job requirements directly against the candidate's verified master technical competencies and career experience.
2. Evaluate:
   - Seniority & Architecture Level: Enterprise Architect, Principal, Lead Solution Architect, IT Director/Head of Technology vs junior developer roles.
   - Domain & Stack Fit: Cloud (AWS/Azure), ERP (SAP S/4HANA), Integration fabrics (Kafka, RabbitMQ, Solace, APIs, EDA), Data Platforms (Databricks, Snowflake), EA Governance (TOGAF, LeanIX), and Agentic AI.
   - Disqualifiers (Score < 50%): Unrelated fields (pure Frontend UI, Game development, Embedded/Hardware, Sales/Marketing, Non-technical HR, or pure junior hands-on coding without architecture).
{lang_instruction}"""

    output = call_native_ollama(
        prompt=prompt,
        system_prompt="You are an executive technology recruiter. Output strictly the requested fields without commentary.",
        num_predict=220 if check_language else 180,
        num_ctx=4096,
        temperature=0.10
    )

    conf_match = re.search(r"CONFIDENCE:\s*(\d+)", output, re.IGNORECASE)
    confidence = int(conf_match.group(1)) if conf_match else 50
    confidence = max(0, min(100, confidence))

    mandatory_finnish = False
    if check_language:
        finnish_match = re.search(r"MANDATORY_FINNISH:\s*(YES|NO)", output, re.IGNORECASE)
        is_finnish_llm = bool(finnish_match and finnish_match.group(1).upper() == "YES")

        # Secondary heuristic check on raw requirements text
        is_finnish_heuristic = bool(re.search(
            r'\b(?:suomen\s+kiel|sujuva[a-z]*\s+suomi|kielitaitovaatimuksena\s+suomi|edellytämme\s+suomen|vaadimme\s+suomen|fluent\s+(?:in\s+)?finnish|mandatory\s+finnish|finnish\s+(?:is\s+)?(?:mandatory|required))\b',
            clean_req,
            re.IGNORECASE
        ))
        mandatory_finnish = is_finnish_llm or is_finnish_heuristic

    reason_match = re.search(r"REASON:\s*(.*)", output, re.IGNORECASE)
    reason = reason_match.group(1).strip() if reason_match else output.strip()

    return {
        "confidence": confidence,
        "mandatory_finnish": mandatory_finnish,
        "reason": reason
    }
