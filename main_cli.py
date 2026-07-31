import sys
from src.pipeline import run_pipeline

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Error: Please provide a job URL or description text.")
        sys.exit(1)
    
    input_param = sys.argv[1]
    print(f"🚀 Starting pipeline for: {input_param[:50]}...")
    
    metrics = run_pipeline(input_param)
    
    print("\n✅ Task Completed!")
    print(f"🏢 Company: {metrics['company']} | 🎯 Role: {metrics['role']}")
    print(f"⏱️ Total CV Time: {metrics['cv_total_time']:.2f}s")
    print(f"⏱️ Total Cover Letter Time: {metrics['cover_total_time']:.2f}s")