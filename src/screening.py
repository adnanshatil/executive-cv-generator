import time
from .config import (
    SCREENING_COOLDOWN_SECONDS,
    MIN_CONFIDENCE_THRESHOLD,
    FINNISH_LANGUAGE_ALLOWED
)
from .utils import load_source_file
from .google_services import (
    get_sheet,
    get_jobs_pending_screening,
    update_job_confidence_and_status,
    download_text_from_drive
)
from .agents import (
    evaluate_role_confidence,
    is_mandatory_finnish_required,
    is_finnish_role_title
)

def run_screening():
    """
    Screens newly scraped jobs (Status == 'Scraped' or Status == 'Cal. Confidence'):
    
    1. In-Batch Duplicate Filter:
       - Only checks within the current batch of newly scraped jobs.
       - If multiple jobs share identical (Company, Role), keeps the first one for evaluation
         and immediately marks subsequent duplicates as 'Discarded' (skipping LLM call).
    2. Finnish Language Filter (when FINNISH_LANGUAGE_ALLOWED is False):
       - If job title contains Finnish words (e.g. 'arkkitehti') or description requires
         mandatory Finnish: immediately marks as 'Discarded' and skips confidence calculation.
       - If user manually set status to 'Cal. Confidence': forces full confidence evaluation
         regardless of language.
    3. Confidence Evaluation via Ollama:
       - Compares requirements against candidate master technical competencies and experiences.
    4. Threshold Promotion:
       - Confidence >= MIN_CONFIDENCE_THRESHOLD: 'Generate CV'
       - Confidence < MIN_CONFIDENCE_THRESHOLD: 'Discarded'
    5. Cooldown: Pauses SCREENING_COOLDOWN_SECONDS between LLM evaluations to protect CPU thermals.
    """
    print("🔍 Starting Role Relevance & Confidence Screening...")
    pending_jobs = get_jobs_pending_screening()
    
    if not pending_jobs:
        print("💤 No jobs pending screening ('Scraped' or 'Cal. Confidence'). Screening complete.")
        return 0, 0

    total = len(pending_jobs)
    print(f"📊 Found {total} job(s) pending confidence evaluation.")
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
        is_manual = job.get("_manual_trigger", False)
        company = str(job.get("Company", "Unknown Company")).strip()
        role = str(job.get("Role", "Unknown Role")).strip()
        linkedin_id = str(job.get("LinkedIn ID", "Unknown")).strip()
        info_link = str(job.get("Scraped Info Link", "")).strip()

        # Step 0: Check for duplicates within this batch ONLY (only applies to automatic scraping, not manual triggers)
        norm_key = (company.lower(), role.lower())
        if not is_manual:
            if norm_key in seen_in_batch_company_roles:
                print(f"[{idx + 1}/{total}] 🗑️ In-batch duplicate detected: '{company}' - '{role}' ({linkedin_id}) already seen in this scraped batch. Marked Discarded (Skipping LLM).")
                update_job_confidence_and_status(row_num, "", "Discarded")
                discarded_count += 1
                continue
            seen_in_batch_company_roles.add(norm_key)

        trigger_type = "Manual 'Cal. Confidence'" if is_manual else "Automatic 'Scraped'"
        print(f"[{idx + 1}/{total}] Evaluating ({trigger_type}): {company} - {role} ({linkedin_id})")

        # 1. Fast Finnish Title Check (skips Drive download & LLM entirely)
        if not FINNISH_LANGUAGE_ALLOWED and not is_manual:
            if is_finnish_role_title(role):
                print(f"[{idx + 1}/{total}] 🇫🇮 Finnish role title detected ('{role}'). FINNISH_LANGUAGE_ALLOWED=False ➔ Status: 'Discarded' (Skipping LLM)")
                update_job_confidence_and_status(row_num, "", "Discarded")
                discarded_count += 1
                finnish_flag_count += 1
                continue

        # 2. Fetch Job Description text from Drive
        requirements_text = ""
        if info_link:
            try:
                requirements_text = download_text_from_drive(info_link)
            except Exception as e:
                print(f"   ⚠️ Could not download description from Drive: {e}. Using title/role fallback.")
                requirements_text = f"Company: {company}\nRole: {role}"
        else:
            requirements_text = f"Company: {company}\nRole: {role}"

        # 3. Finnish Language Check on Requirements Text:
        # If job description contains Finnish language requirements or is written in Finnish:
        if not FINNISH_LANGUAGE_ALLOWED and not is_manual:
            if is_mandatory_finnish_required(requirements_text, role_title=role):
                print(f"   🇫🇮 Finnish requirement detected in description ('{role}'). FINNISH_LANGUAGE_ALLOWED=False ➔ Status: 'Discarded' (Skipping LLM)")
                update_job_confidence_and_status(row_num, "", "Discarded")
                discarded_count += 1
                finnish_flag_count += 1
                continue

        # 4. Evaluate Confidence via Ollama using master source files
        try:
            eval_result = evaluate_role_confidence(
                requirements=requirements_text,
                company=company,
                role=role,
                tech_source=tech_src,
                exp_source=exp_src,
                check_language=not FINNISH_LANGUAGE_ALLOWED if not is_manual else False
            )
            confidence = eval_result["confidence"]
            reason = eval_result.get("reason", "")
            mandatory_finnish = eval_result.get("mandatory_finnish", False)
        except Exception as e:
            print(f"   ❌ Error evaluating confidence: {e}. Defaulting to 50% Discarded.")
            confidence = 50
            reason = f"Evaluation error: {e}"
            mandatory_finnish = False

        # 5. Apply Decision Threshold (and check if LLM flagged mandatory Finnish)
        confidence_str = f"{confidence}%"
        if mandatory_finnish and not FINNISH_LANGUAGE_ALLOWED and not is_manual:
            new_status = "Discarded"
            discarded_count += 1
            finnish_flag_count += 1
            print(f"   🇫🇮 LLM flagged mandatory Finnish requirement ➔ Status: 'Discarded' (Skipping CV generation)")
            update_job_confidence_and_status(row_num, "", new_status)
        elif confidence >= MIN_CONFIDENCE_THRESHOLD:
            new_status = "Generate CV"
            approved_count += 1
            icon = "✅"
            print(f"   {icon} Confidence: {confidence_str} ➔ Status: '{new_status}'")
            update_job_confidence_and_status(row_num, confidence_str, new_status)
        else:
            new_status = "Discarded"
            discarded_count += 1
            icon = "🗑️"
            print(f"   {icon} Confidence: {confidence_str} ➔ Status: '{new_status}'")
            update_job_confidence_and_status(row_num, confidence_str, new_status)
        if reason:
            print(f"      Reason: {reason}")

        # 5. CPU Thermal Cooldown Break (if there are more jobs in queue)
        if idx < total - 1 and SCREENING_COOLDOWN_SECONDS > 0:
            mins = SCREENING_COOLDOWN_SECONDS / 60.0
            print(f"   ⏳ Cooldown: Pausing {mins:.1f} mins to protect CPU thermals before next evaluation...")
            time.sleep(SCREENING_COOLDOWN_SECONDS)

    print(f"\n🎉 Screening Complete! {approved_count} marked 'Generate CV', {finnish_flag_count} discarded for Finnish requirement, {discarded_count} total marked 'Discarded'.")
    print("   ℹ️ Note: Discarded items are preserved for review and will be purged during the 2:00 AM cycle.")
    return approved_count, discarded_count

if __name__ == "__main__":
    run_screening()
