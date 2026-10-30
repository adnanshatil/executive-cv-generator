import time
from .config import (
    SCREENING_COOLDOWN_SECONDS,
    MIN_CONFIDENCE_THRESHOLD,
    CHECK_MANDATORY_FINNISH
)
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
    
    1. In-Batch Duplicate Filter:
       - Only checks within the current batch of newly scraped jobs (not historical rows).
       - If multiple jobs share identical (Company, Role), keeps the first one for evaluation
         and immediately marks subsequent duplicates as 'Discarded' (skipping LLM call).
    2. Confidence Evaluation:
       - Compares requirements against candidate master technical competencies and experiences.
    3. Mandatory Finnish Language Check:
       - If mandatory Finnish is required, calculates actual confidence and keeps status as 'Scraped'
         (does not promote to 'Generate CV', leaving it for manual review).
    4. Threshold Promotion (if no mandatory Finnish):
       - Confidence >= MIN_CONFIDENCE_THRESHOLD: 'Generate CV'
       - Confidence < MIN_CONFIDENCE_THRESHOLD: 'Discarded'
    5. Cooldown: Pauses SCREENING_COOLDOWN_SECONDS between LLM evaluations to protect CPU thermals.
    """
    print("🔍 Starting Role Relevance & Confidence Screening...")
    pending_jobs = get_jobs_pending_screening()
    
    if not pending_jobs:
        print("💤 No jobs with status 'Scraped' found. Screening complete.")
        return 0, 0

    total = len(pending_jobs)
    print(f"📊 Found {total} scraped job(s) pending confidence evaluation.")
    print(f"   Threshold: {MIN_CONFIDENCE_THRESHOLD}% | Cooldown: {SCREENING_COOLDOWN_SECONDS // 60}m per job\n")

    # In-batch duplicate tracking: only tracks (Company, Role) within this newly scraped batch
    seen_in_batch_company_roles = set()

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

        # Step 0: Check for duplicates within this batch ONLY
        norm_key = (company.lower(), role.lower())
        if norm_key in seen_in_batch_company_roles:
            print(f"[{idx + 1}/{total}] 🗑️ In-batch duplicate detected: '{company}' - '{role}' ({linkedin_id}) already seen in this scraped batch. Marked Discarded (Skipping LLM).")
            update_job_confidence_and_status(row_num, "", "Discarded")
            discarded_count += 1
            continue

        # Register this company & role combination for subsequent items in this batch
        seen_in_batch_company_roles.add(norm_key)

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
                exp_source=exp_src,
                check_language=CHECK_MANDATORY_FINNISH
            )
            confidence = eval_result["confidence"]
            mandatory_finnish = eval_result.get("mandatory_finnish", False)
            reason = eval_result.get("reason", "")
        except Exception as e:
            print(f"   ❌ Error evaluating confidence: {e}. Defaulting to 50% Discarded.")
            confidence = 50
            mandatory_finnish = False
            reason = f"Evaluation error: {e}"

        # 3. Apply Decision Threshold & Finnish Language Feature Flag
        confidence_str = f"{confidence}%"
        if CHECK_MANDATORY_FINNISH and mandatory_finnish:
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
