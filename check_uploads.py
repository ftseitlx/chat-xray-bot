#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Define the expected directory structure based on the bot's configuration
base_dir = Path(__file__).parent
upload_dir = base_dir / "uploads"
report_dir = base_dir / "reports"

print("Checking local directory structure for the Chat X-Ray Bot...")

# Check if the upload directory exists
if not upload_dir.exists():
    print(f"❌ Upload directory does not exist: {upload_dir}")
    print("Creating upload directory...")
    try:
        os.makedirs(upload_dir, exist_ok=True)
        print(f"✅ Created upload directory: {upload_dir}")
    except Exception as e:
        print(f"❌ Failed to create upload directory: {e}")
else:
    print(f"✅ Upload directory exists: {upload_dir}")
    
    # Check if the upload directory is writable
    try:
        test_file = upload_dir / "test_write.tmp"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Upload directory is writable")
    except Exception as e:
        print(f"❌ Upload directory is not writable: {e}")

# Check if the report directory exists
if not report_dir.exists():
    print(f"❌ Report directory does not exist: {report_dir}")
    print("Creating report directory...")
    try:
        os.makedirs(report_dir, exist_ok=True)
        print(f"✅ Created report directory: {report_dir}")
    except Exception as e:
        print(f"❌ Failed to create report directory: {e}")
else:
    print(f"✅ Report directory exists: {report_dir}")
    
    # Check if the report directory is writable
    try:
        test_file = report_dir / "test_write.tmp"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Report directory is writable")
    except Exception as e:
        print(f"❌ Report directory is not writable: {e}")

print("\nNote: This only checks the local directory structure.")
print("On the Render.com server, the directories should be created automatically when the bot starts.")
print("If you're still having issues with file uploads, the problem might be elsewhere in the code.") 