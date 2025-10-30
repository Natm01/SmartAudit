#!/usr/bin/env python3
"""
Test script for the simplified database_upload endpoint

This script demonstrates how to use the database upload endpoint.
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8001/smau-proto/api/import"

def test_database_upload(execution_id: str, auth_user_id: int = 1):
    """
    Test the database upload endpoint with simplified parameters.

    Args:
        execution_id: The execution ID (GUID) - e.g., "12345678-1234-1234-1234-123456789012"
        auth_user_id: The authenticated user ID (default: 1)
    """

    print("=" * 80)
    print("TESTING DATABASE UPLOAD ENDPOINT")
    print("=" * 80)

    # Step 1: Start the upload
    print(f"\n1. Starting database upload...")
    print(f"   Execution ID: {execution_id}")
    print(f"   Auth User ID: {auth_user_id}")

    payload = {
        "execution_id": execution_id,
        "auth_user_id": auth_user_id
    }

    print(f"\n   POST {API_BASE_URL}/database-upload")
    print(f"   Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            f"{API_BASE_URL}/database-upload",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"\n   Response Status: {response.status_code}")
        print(f"   Response Body:")
        print(f"   {json.dumps(response.json(), indent=2)}")

        if response.status_code != 200:
            print("\n   ❌ Upload failed to start")
            return False

        print("\n   ✅ Upload started successfully")

    except Exception as e:
        print(f"\n   ❌ Error: {str(e)}")
        return False

    # Step 2: Check status
    print(f"\n2. Checking upload status...")

    for i in range(5):
        time.sleep(2)

        print(f"\n   Check #{i+1}:")
        print(f"   GET {API_BASE_URL}/database-upload/{execution_id}/status")

        try:
            status_response = requests.get(
                f"{API_BASE_URL}/database-upload/{execution_id}/status"
            )

            status_data = status_response.json()
            print(f"   Status: {status_data.get('status')}")
            print(f"   Step: {status_data.get('step')}")

            if status_data.get('error'):
                print(f"   Error: {status_data.get('error')}")

            if status_data.get('status') == 'completed':
                print("\n   ✅ Upload completed successfully!")
                return True

            if status_data.get('status') == 'failed':
                print("\n   ❌ Upload failed")
                return False

        except Exception as e:
            print(f"   ❌ Error checking status: {str(e)}")
            return False

    print("\n   ⏳ Upload still in progress...")
    return None


def main():
    """Main function"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_database_upload_endpoint.py <execution_id> [auth_user_id]")
        print("\nExample:")
        print("  python test_database_upload_endpoint.py '12345678-1234-1234-1234-123456789012'")
        print("  python test_database_upload_endpoint.py '12345678-1234-1234-1234-123456789012' 42")
        return 1

    execution_id = sys.argv[1]
    auth_user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    result = test_database_upload(execution_id, auth_user_id)

    print("\n" + "=" * 80)
    if result is True:
        print("✅ TEST PASSED")
        return 0
    elif result is False:
        print("❌ TEST FAILED")
        return 1
    else:
        print("⏳ TEST INCOMPLETE (still processing)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
