"""
Generate an API key for the developer API.
Usage: python scripts/generate_api_key.py --name "My App"
"""

import argparse
import json
import os
import uuid
from datetime import datetime

KEYS_FILE = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "api_keys.json")


def main():
    parser = argparse.ArgumentParser(description="Generate an API key")
    parser.add_argument("--name", required=True, help="Name/description for this key")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)

    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE) as f:
            keys = json.load(f)
    else:
        keys = []

    new_key = {
        "key": str(uuid.uuid4()),
        "name": args.name,
        "created": datetime.utcnow().isoformat() + "Z",
        "requests_today": 0,
        "last_reset": datetime.utcnow().strftime("%Y-%m-%d"),
    }

    keys.append(new_key)

    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

    print(f"API key generated successfully:")
    print(f"  Name: {args.name}")
    print(f"  Key:  {new_key['key']}")
    print(f"  File: {KEYS_FILE}")
    print(f"\nUsage: curl -H 'X-API-Key: {new_key['key']}' -F 'file=@image.jpg' /api/v1/detect")


if __name__ == "__main__":
    main()
