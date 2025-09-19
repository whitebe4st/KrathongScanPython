"""
Utility to sync existing processed files with job tracking
"""
import json
import os
import uuid
from datetime import datetime


def sync_processed_files():
    """Sync existing processed files with job tracking"""

    uploads_dir = "uploads"
    results_dir = "results"

    if not os.path.exists(uploads_dir) or not os.path.exists(results_dir):
        print("Upload or results directory not found")
        return

    # Get all processed files
    processed_files = [f for f in os.listdir(results_dir) if f.startswith("processed_")]
    uploaded_files = [f for f in os.listdir(uploads_dir)]

    print(f"Found {len(processed_files)} processed files")
    print(f"Found {len(uploaded_files)} uploaded files")

    # Create job data
    jobs_data = {}

    for processed_file in processed_files:
        # Extract original filename
        if processed_file.startswith("processed_"):
            original_name = processed_file[10:]  # Remove 'processed_' prefix

            # Find matching upload file
            upload_file = None
            for upload in uploaded_files:
                if upload == original_name:
                    upload_file = upload
                    break

            if upload_file:
                job_id = str(uuid.uuid4())
                jobs_data[job_id] = {
                    "job_id": job_id,
                    "filename": upload_file,
                    "status": "completed",
                    "result_file": processed_file,
                    "created_at": datetime.now().isoformat(),
                    "error_message": None,
                }
                print(f"✅ Synced: {upload_file} -> {processed_file}")

    # Save to JSON file for reference
    with open("jobs_sync.json", "w") as f:
        json.dump(jobs_data, f, indent=2)

    print(f"\n📊 Synced {len(jobs_data)} jobs")
    print("💾 Job data saved to jobs_sync.json")

    return jobs_data


if __name__ == "__main__":
    sync_processed_files()
