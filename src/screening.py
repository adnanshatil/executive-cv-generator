import time
from .config import SCREENING_COOLDOWN_SECONDS, MIN_CONFIDENCE_THRESHOLD
from .utils import load_source_file
from .google_services import (
    get_sheet,
    get_jobs_pending_screening,
    update_job_confidence_and_status,
    download_text_from_drive
)
from .agents import evaluate_role_confidence

def run_screening():
    """
    Screens newly scraped jobs (Status == 'Scraped' with empty Confidence):
    
    1. Duplicate Filter: If multiple roles are found with identical Company and Role names,
       marks subsequent ones 'Discarded' immediately without calculating confidence.
    2. Confidence Evaluation: Compares requirements against candidate master technical
       competencies and professional experiences.
    3. Mandatory Finnish Check: If mandatory Finnish language is required, calculates
       confidence and keeps status as 'Scraped' (does not promote to 'Generate CV').
    4. Threshold Promotion:
       - Confidence >= MIN_CONFIDENCE_THRESHOLD (and no mandatory Finnish): 'Generate CV'
       - Confidence < MIN_CONFIDENCE_THRESHOLD: 'Discarded'
    5. Pauses SCREENING_COOLDOWN_SECONDS between LLM evaluations to protect CPU thermals.
    """
    print("🔍 Starting Role Relevance & Confidence Screening...")
    pending_jobs = get_jobs_pending_screening()
    
    if not pending_jobs:
        print("💤 No jobs with status 'Scraped' found. Screening complete.")
        return 0, 0

    total = len(pending_jobs)
    print(f"📊 Found {total} scraped job(s) pending confidence evaluation.")
    print(f"   Threshold: {MIN_CONFIDENCE_THRESHOLD}% | Cooldown: {SCREENING_COOLDOWN_SECONDS // 60}m per job\n")

    # Fetch all records to build a set of already existing (Company, Role) pairs
    sheet = get_sheet()
    all_records = sheet.get_all_records()
    seen_company_roles = set()
    for record in all_records:
        st = str(record.get("Status", "")).strip()
        conf = str(record.get("Confidence", "")).strip()
        # Include all rows that are already processed or screened
        if st != "Scraped" or conf:
            c = str(record.get("Company", "")).strip().lower()
            r = str(record.get("Role", "")).strip().lower()
            if c and r:
                seen_company_roles.add((c, r))

    # Load master sources once for all evaluations
    tech_src = load_source_file("technicalcompetencies.md")
    exp_src = load_source_file("professionalexperiences.md")

    approved_count = 0
    discarded_count = 0
    finnish_flag_count = 0

    for idx, job in enumerate(pending_jobs):
        row_num = job["_row_number"]
        company = str(job.get("Company", "Unknown Company")).strip()
        role = str(job.get("Role", "Unknown Role")).strip()
        linkedin_id = str(job.get("LinkedIn ID", "Unknown")).strip()
        info_link = str(job.get("Scraped Info Link", "")).strip()

        # Step 0: Check for duplicate Company and Role names
        norm_key = (company.lower(), role.lower())
        if norm_key in seen_company_roles:
            print(f"[{idx + 1}/{total}] 🗑️ Duplicate Company & Role detected: '{company}' - '{role}' ({linkedin_id}) already exists. Marked Discarded (Skipping LLM).")
            update_job_confidence_and_status(row_num, "", "Discarded")
            discarded_count += 1
            continue

        # Register this company & role combination so subsequent duplicates in this batch are discarded
        seen_company_roles.add(norm_key)

        print(f"[{idx + 1}/{total}] Evaluating: {company} - {role} ({linkedin_id})")

        # 1. Fetch Job Description text from Drive
        requirements_text = ""
        if info_link:
            try:
                requirements_text = download_text_from_drive(info_link)
            except Exception as e:
                print(f"   ⚠️ Could not download description from Drive: {e}. Using title/role fallback.")
                requirements_text = f"Company: {company}\nRole: {role}"
        else:
            requirements_text = f"Company: {company}\nRole: {role}"

        # 2. Evaluate Confidence and Language Requirement via Ollama
        try:
            eval_result = evaluate_role_confidence(
                requirements=requirements_text,
                company=company,
                role=role,
                tech_source=tech_src,
                exp_source=exp_src
            )
            confidence = eval_result["confidence"]
            mandatory_finnish = eval_result.get("mandatory_finnish", False)
            reason = eval_result.get("reason", "")
        except Exception as e:
            print(f"   ❌ Error evaluating confidence: {e}. Defaulting to 50% Discarded.")
            confidence = 50
            mandatory_finnish = False
            reason = f"Evaluation error: {e}"

        # 3. Apply Decision Threshold & Finnish Language Rule
        confidence_str = f"{confidence}%"
        if mandatory_finnish:
            new_status = "Scraped"
            finnish_flag_count += 1
            icon = "🇫🇮"
            print(f"   {icon} Confidence: {confidence_str} | Mandatory Finnish language required ➔ Keeping Status: 'Scraped'")
        elif confidence >= MIN_CONFIDENCE_THRESHOLD:
            new_status = "Generate CV"
            approved_count += 1
            icon = "✅"
            print(f"   {icon} Confidence: {confidence_str} ➔ Status: '{new_status}'")
        else:
            new_status = "Discarded"
            discarded_count += 1
            icon = "🗑️"
            print(f"   {icon} Confidence: {confidence_str} ➔ Status: '{new_status}'")

        update_job_confidence_and_status(row_num, confidence_str, new_status)
        if reason:
            print(f"      Reason: {reason}")

        # 4. CPU Thermal Cooldown Break (if there are more jobs in queue)
        if idx < total - 1 and SCREENING_COOLDOWN_SECONDS > 0:
            mins = SCREENING_COOLDOWN_SECONDS / 60.0
            print(f"   ⏳ Cooldown: Pausing {mins:.1f} mins to protect CPU thermals before next evaluation...")
            time.sleep(SCREENING_COOLDOWN_SECONDS)

    print(f"\n🎉 Screening Complete! {approved_count} marked 'Generate CV', {finnish_flag_count} kept 'Scraped' (Mandatory Finnish), {discarded_count} marked 'Discarded'.")
    print("   ℹ️ Note: Discarded items are preserved for review and will be purged during the 3:00 AM cycle.")
    return approved_count, discarded_count

if __name__ == "__main__":
    run_screening()
