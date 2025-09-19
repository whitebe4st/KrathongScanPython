#!/usr/bin/env python3
"""
Test script to verify database connectivity for both executables
"""
import os
import sqlite3
import sys
from pathlib import Path

# Add the current directory to path to import path_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import path_utils


def test_database_connection():
    """Test database connection and basic operations"""
    try:
        # Get database path using our path utilities
        db_path = path_utils.get_database_path()
        print(f"Database path: {db_path}")

        # Check if database file exists
        if os.path.exists(db_path):
            print(f"✅ Database file exists at: {db_path}")
        else:
            print(f"❌ Database file not found at: {db_path}")
            return False

        # Try to connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if templates table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='templates';"
        )
        table_exists = cursor.fetchone()

        if table_exists:
            print("✅ Templates table exists")

            # Count templates
            cursor.execute("SELECT COUNT(*) FROM templates;")
            count = cursor.fetchone()[0]
            print(f"📊 Total templates in database: {count}")

            # Show some template info if any exist
            if count > 0:
                cursor.execute("SELECT id, name, created_at FROM templates LIMIT 3;")
                templates = cursor.fetchall()
                print("🔍 Sample templates:")
                for template in templates:
                    print(
                        f"   ID: {template[0]}, Name: {template[1]}, Created: {template[2]}"
                    )
        else:
            print("❌ Templates table not found")

        conn.close()
        print("✅ Database connection test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_path_detection():
    """Test path detection and directory creation"""
    try:
        print("\n🔍 Testing path detection...")

        # Test executable detection
        is_exe = hasattr(sys, "_MEIPASS")
        print(f"Running as executable: {is_exe}")

        # Test executable directory
        exe_dir = path_utils.get_executable_dir()
        print(f"Executable directory: {exe_dir}")

        # Test data directory
        data_dir = path_utils.get_data_dir()
        print(f"Data directory: {data_dir}")

        # Test directory creation
        path_utils.ensure_directories()
        print("✅ Directory creation test passed")

        return True

    except Exception as e:
        print(f"❌ Path detection test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing Executable Database Connectivity")
    print("=" * 50)

    # Test path detection
    path_test = test_path_detection()

    print("\n" + "=" * 50)

    # Test database connection
    db_test = test_database_connection()

    print("\n" + "=" * 50)

    if path_test and db_test:
        print("✅ All tests passed! Executables should work correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the output above.")
        sys.exit(1)
