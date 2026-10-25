import time
from .config import SCREENING_COOLDOWN_SECONDS, MIN_CONFIDENCE_THRESHOLD
from .google_services import (
    get_jobs_pending_screening,
    update_job_confidence_and_status,
    download_text_from_drive
)
from .agents import evaluate_role_confidence

def run_screening():
    """
    Screens newly scraped jobs (Status == 'Scraped') by calculating match confidence
    against candidate profile via Ollama.
    
    - Confidence >= MIN_CONFIDENCE_THRESHOLD: sets Status to 'Generate CV'
    - Confidence < MIN_CONFIDENCE_THRESHOLD: sets Status to 'Discarded'
    - Pauses SCREENING_COOLDOWN_SECONDS after each call to prevent CPU overheating.
    """
    print("🔍 Starting Role Relevance & Confidence Screening...")
    pending_jobs = get_jobs_pending_screening()
    
    if not pending_jobs:
        print("💤 No jobs with status 'Scraped' found. Screening complete.")
        return 0, 0

    total = len(pending_jobs)
    print(f"📊 Found {total} scraped job(s) pending confidence evaluation.")
    print(f"   Threshold: {MIN_CONFIDENCE_THRESHOLD}% | Cooldown: {SCREENING_COOLDOWN_SECONDS // 60}m per job\n")

    approved_count = 0
    discarded_count = 0

    for idx, job in enumerate(pending_jobs):
        row_num = job["_row_number"]
        company = str(job.get("Company", "Unknown Company")).strip()
        role = str(job.get("Role", "Unknown Role")).strip()
        linkedin_id = str(job.get("LinkedIn ID", "Unknown")).strip()
        info_link = str(job.get("Scraped Info Link", "")).strip()

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

        # 2. Evaluate Confidence via Ollama
        try:
            eval_result = evaluate_role_confidence(requirements_text, company, role)
            confidence = eval_result["confidence"]
            reason = eval_result.get("reason", "")
        except Exception as e:
            print(f"   ❌ Error evaluating confidence: {e}. Defaulting to 50% Discarded.")
            confidence = 50
            reason = f"Evaluation error: {e}"

        # 3. Apply Decision Threshold
        if confidence >= MIN_CONFIDENCE_THRESHOLD:
            new_status = "Generate CV"
            approved_count += 1
            icon = "✅"
        else:
            new_status = "Discarded"
            discarded_count += 1
            icon = "🗑️"

        confidence_str = f"{confidence}%"
        update_job_confidence_and_status(row_num, confidence_str, new_status)
        print(f"   {icon} Confidence: {confidence_str} ➔ Status: '{new_status}'")
        if reason:
            print(f"      Reason: {reason}")

        # 4. CPU Thermal Cooldown Break (if there are more jobs in queue)
        if idx < total - 1 and SCREENING_COOLDOWN_SECONDS > 0:
            mins = SCREENING_COOLDOWN_SECONDS / 60.0
            print(f"   ⏳ Cooldown: Pausing {mins:.1f} mins to protect CPU thermals before next evaluation...")
            time.sleep(SCREENING_COOLDOWN_SECONDS)

    print(f"\n🎉 Screening Complete! {approved_count} marked 'Generate CV', {discarded_count} marked 'Discarded'.")
    print("   ℹ️ Note: Discarded items are preserved for review and will be purged during the 3:00 AM cycle.")
    return approved_count, discarded_count

if __name__ == "__main__":
    run_screening()
