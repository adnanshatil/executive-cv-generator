import re
import textwrap

from .db import log_generation
from .config import OUTPUT_DIR
from .utils import Timer, load_source_file, save_text, save_pdf, clean_dashes
from .scraper import fetch_job_requirements
from . import agents

def run_pipeline(input_param: str) -> dict:
    """
    Master orchestrator. Runs the entire pipeline and returns timing & output metrics.
    """
    metrics = {}
    
    with Timer() as t_total:
        # Step 0: Ingestion
        with Timer() as t_ingest:
            req_company, req_role, requirements = fetch_job_requirements(input_param)
        metrics["dur_ingest"] = t_ingest.duration

        # Static CV data
        static_cv_header_name = (
            "Adnan Md. Shoeb Shatil\n"
        )

        static_cv_header_info = (
            "Email       shoeb.shatil@gmail.com\n"
            "Phone       +358(0)406850868\n"
            "LinkedIn    linkedin.com/in/adnanshatil\n"
            "Github      github.com/adnanshatil\n\n"
        )

        posti_experience_header = (
            "Enterprise Architect\n"
            "Posti Group Oyj\n"
            "11/2024 - Present           Helsinki, Finland"
        )


        # Load Source Data
        header_src = load_source_file("titlesummary.md")
        core_src = load_source_file("corecompetencies.md")
        tech_src = load_source_file("technicalcompetencies.md")
        exp_src = load_source_file("professionalexperiences.md")
        cover_src = load_source_file("coverletter.md")
        static_footer = load_source_file("staticcontent.md")

        exp_lines = [line.strip() for line in exp_src.split("\n") if line.strip().startswith("-")]
        formatted_exp = "\n".join(exp_lines)

        # Step 1: Metadata & Summary
        with Timer() as t_1:
            meta = agents.extract_metadata(requirements, header_src)
            company = req_company if meta['company'] == "Target Company" else clean_dashes(meta['company'])
            role = req_role if meta['role'] == "Target Position" else clean_dashes(meta['role'])
            anchor = f"TARGET COMPANY: {company}\nTARGET ROLE: {role}\nTITLE LINE: {meta['title_line']}\nSUMMARY: {meta['summary'][:350]}..."
        metrics["dur_1"] = t_1.duration

        # Step 2: Core Competencies
        with Timer() as t_2:
            out_2 = agents.generate_core_competencies(requirements, anchor, core_src)
        metrics["dur_2"] = t_2.duration

        # Step 3: Tech Stack
        with Timer() as t_3:
            out_3 = agents.generate_tech_stack(requirements, anchor, tech_src)
        metrics["dur_3"] = t_3.duration

        # Step 4: Professional Experience
        with Timer() as t_4:
            out_4 = agents.generate_experience(requirements, anchor, formatted_exp)
        metrics["dur_4"] = t_4.duration

        # Step 5: Cover Letter
        with Timer() as t_5:
            out_5 = agents.generate_cover_letter(requirements, anchor, company, role, cover_src)
        metrics["dur_5"] = t_5.duration

        # Document Assembly & Saving
        clean_comp_fn = re.sub(r'[^a-zA-Z0-9]', '_', company).strip('_').lower()
        clean_role_fn = re.sub(r'[^a-zA-Z0-9]', '_', role).strip('_').lower()
        clean_comp_fn = re.sub(r'_+', '_', clean_comp_fn)
        clean_role_fn = re.sub(r'_+', '_', clean_role_fn)

        cv_md_path = OUTPUT_DIR / f"cv_{clean_comp_fn}_{clean_role_fn}.md"
        cv_pdf_path = OUTPUT_DIR / f"cv_{clean_comp_fn}_{clean_role_fn}.pdf"
        cover_md_path = OUTPUT_DIR / f"cover_letter_{clean_comp_fn}_{clean_role_fn}.md"
        cover_pdf_path = OUTPUT_DIR / f"cover_letter_{clean_comp_fn}_{clean_role_fn}.pdf"

        # Save CV (Markdown Only)
        with Timer() as t_cv_compile:
            final_cv = textwrap.dedent(f"""\
# Adnan Md. Shoeb Shatil
**{meta['title_line']}**

**Email:** shoeb.shatil@gmail.com | **Phone:** +358(0)406850868\n
**LinkedIn:** linkedin.com/in/adnanshatil | **Github:** github.com/adnanshatil



### EXECUTIVE SUMMARY
{meta['summary']}

### CORE COMPETENCIES
{out_2}

### TECHNICAL COMPETENCIES
{out_3}

### PROFESSIONAL EXPERIENCE
#### - Enterprise Architect
**Posti Group Oyj**         *11/2024 – Present | Helsinki, Finland*
{out_4}

{static_footer}
""").strip()

            save_text(cv_md_path, final_cv)
            save_pdf(cv_pdf_path, final_cv)
        metrics["cv_total_time"] = t_1.duration + t_2.duration + t_3.duration + t_4.duration + t_cv_compile.duration

        # Save Cover Letter (PDF Only)
        with Timer() as t_cover_compile:
            # Force line break on sign-off if Ollama collapses it
            final_cover = clean_dashes(out_5)
            final_cover = re.sub(r'Best regards,?\s*Adnan Shatil', 'Best regards,\n\nAdnan Shatil', final_cover, flags=re.IGNORECASE)
            save_text(cover_md_path, final_cover)
            save_pdf(cover_pdf_path, final_cover)
        metrics["cover_total_time"] = t_1.duration + t_5.duration + t_cover_compile.duration

        # Convert total pipeline time from seconds to minutes
        total_minutes = (metrics["cv_total_time"] + metrics["cover_total_time"]) / 60.0

        # 📌 Log completion to history.json via src/db.py
        log_generation(
            company=company,
            role=role,
            linkedin_url=input_param.strip(),
            cv_md=cv_md_path.name,
            cv_pdf=cv_pdf_path.name,
            cover_md=cover_md_path.name,
            cover_pdf=cover_pdf_path.name,
            exec_time=f"{total_minutes:.2f}"
        )

        metrics["company"] = company
        metrics["role"] = role
        metrics["total_time_min"] = f"{total_minutes:.2f}"
    
    return metrics