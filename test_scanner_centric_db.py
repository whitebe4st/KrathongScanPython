#!/usr/bin/env python3
"""
Test Database Path Resolution

Tests the new scanner-centric database path resolution system.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
import path_utils


def test_scanner_centric_paths():
    """Test scanner-centric database paths."""
    print("🧪 Testing Scanner-Centric Database Path Resolution")
    print("=" * 60)

    # Test scanner app detection
    print("\n1. Testing Application Type Detection:")
    is_scanner = path_utils.is_scanner_app()
    print(f"   Is Scanner App: {is_scanner}")

    # Test database path
    print("\n2. Testing Database Path Resolution:")
    db_path = path_utils.get_database_path()
    print(f"   Database Path: {db_path}")
    print(f"   Database Exists: {db_path.exists()}")

    # Test scanner database search
    print("\n3. Testing Scanner Database Search:")
    scanner_dbs = path_utils.find_scanner_database_locations()
    print(f"   Found {len(scanner_dbs)} scanner databases:")
    for i, db in enumerate(scanner_dbs, 1):
        print(f"     {i}. {db}")
        print(f"        Exists: {db.exists()}")

    # Test custom database validation
    print("\n4. Testing Custom Database Validation:")
    try:
        if scanner_dbs:
            custom_db = path_utils.get_custom_database_path(str(scanner_dbs[0]))
            print(f"   Valid custom database: {custom_db}")
        else:
            print("   No scanner databases found to test")
    except Exception as e:
        print(f"   Custom database validation error: {e}")

    print("\n" + "=" * 60)
    print("✅ Path resolution test completed!")


def test_from_scanner_directory():
    """Test path resolution from scanner directory."""
    print("\n🔍 Testing from Scanner Directory:")
    print("-" * 40)

    scanner_dir = Path.cwd() / "release" / "scanner"
    if scanner_dir.exists():
        original_cwd = Path.cwd()
        try:
            # Change to scanner directory
            import os

            os.chdir(scanner_dir)

            # Test database path resolution from scanner directory
            db_path = path_utils.get_database_path()
            print(f"   Database Path from Scanner Dir: {db_path}")
            print(f"   Database Exists: {db_path.exists()}")

            # Test if it detects as scanner app
            is_scanner = path_utils.is_scanner_app()
            print(f"   Detected as Scanner App: {is_scanner}")

        finally:
            # Restore original directory
            os.chdir(original_cwd)
    else:
        print("   Scanner directory not found - skipping test")


def test_from_backend_directory():
    """Test path resolution from backend directory."""
    print("\n🔍 Testing from Backend Directory:")
    print("-" * 40)

    backend_dir = Path.cwd() / "release" / "backend"
    if backend_dir.exists():
        original_cwd = Path.cwd()
        try:
            # Change to backend directory
            import os

            os.chdir(backend_dir)

            # Test database path resolution from backend directory
            db_path = path_utils.get_database_path()
            print(f"   Database Path from Backend Dir: {db_path}")
            print(f"   Database Exists: {db_path.exists()}")

            # Test scanner database search
            scanner_dbs = path_utils.find_scanner_database_locations()
            print(f"   Found Scanner Databases: {len(scanner_dbs)}")
            for db in scanner_dbs:
                print(f"     - {db}")

            # Test if it detects as scanner app
            is_scanner = path_utils.is_scanner_app()
            print(f"   Detected as Scanner App: {is_scanner}")

        finally:
            # Restore original directory
            os.chdir(original_cwd)
    else:
        print("   Backend directory not found - skipping test")


if __name__ == "__main__":
    test_scanner_centric_paths()
    test_from_scanner_directory()
    test_from_backend_directory()

    print("\n🎉 All tests completed!")
