#!/usr/bin/env python3
"""
Twitter AI Poster Demo
Uses Gemini to generate a post and saves it to Pending_Approval.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Load .env
load_dotenv()

from src.services.social_service import generate_social_post

def main():
    print("=" * 60)
    print("AI Employee - Twitter AI Poster")
    print("=" * 60)
    
    topic = input("Enter the topic for the Twitter post: ")
    if not topic:
        topic = "AI Employee Gold Tier launch - transforming business with automated social media and Odoo integration."
        print(f"Using default topic: {topic}")
    
    print(f"\n🚀 Generating Twitter post using Gemini-2.0-flash...")
    result = generate_social_post(topic, "twitter")
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n✅ Post generated successfully!")
    print(f"📄 Filename: {result['filename']}")
    print(f"📍 Location: AI-Employee-Vault/Pending_Approval/{result['filename']}")
    print("\n--- CONTENT ---")
    print(result['content'])
    print("----------------")
    
    print("\nNext Steps:")
    print(f"1. Go to AI-Employee-Vault/Pending_Approval/")
    print(f"2. Review the post in {result['filename']}")
    print(f"3. Move it to AI-Employee-Vault/Approved/ to post it to Twitter!")
    print(f"4. Make sure 'run_all_watchers.py' is running.")

if __name__ == "__main__":
    main()
