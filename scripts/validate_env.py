#!/usr/bin/env python3
"""
Validates that required environment variables are set.
"""
import os
import sys

from dotenv import load_dotenv


def main():
    load_dotenv()
    required_keys = ['FRED_API_KEY']
    missing = []

    for key in required_keys:
        if not os.environ.get(key):
            missing.append(key)

    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Please copy .env.example to .env and fill in the values.")
        sys.exit(1)

    print("Environment validation passed. Core API keys are present.")

if __name__ == '__main__':
    main()
