#!/usr/bin/env python3
"""
Utility to update job status for existing processed files
"""
import json
import os
from datetime import datetime


def update_existing_jobs():
    """Update job status for existing processed files"""
    uploads_dir = "G:/MotionSix/KrathongScanner/web/uploads"
    results_dir = "G:/MotionSix/KrathongScanner/web/results"

    if not os.path.exists(uploads_dir) or not os.path.exists(results_dir):
        print("Upload or results directory not found")
        return

    # Find uploaded files and their corresponding processed files
    upload_files = [f for f in os.listdir(uploads_dir) if f.endswith(".png")]

    completed_jobs = []

    for upload_file in upload_files:
        filename_base = os.path.splitext(upload_file)[0]
        processed_file = f"processed_{filename_base}.png"
        processed_path = os.path.join(results_dir, processed_file)

        if os.path.exists(processed_path):
            job_info = {
                "upload_file": upload_file,
                "processed_file": processed_file,
                "status": "completed",
                "processed_at": datetime.now().isoformat(),
            }
            completed_jobs.append(job_info)
            print(f"✅ Found completed: {upload_file} -> {processed_file}")
        else:
            print(f"❌ Missing result for: {upload_file}")

    print(f"\n📊 Summary:")
    print(f"   📁 Upload files: {len(upload_files)}")
    print(f"   ✅ Completed jobs: {len(completed_jobs)}")

    if completed_jobs:
        print(f"\n🎯 Completed files can be downloaded:")
        for job in completed_jobs:
            print(f"   📥 {job['processed_file']}")


if __name__ == "__main__":
    update_existing_jobs()
