"""
Test script for AI Router.
Demonstrates single generation and streaming with Gemini and Grok.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from src.core.ai_router import generate, generate_stream, router

def test_single():
    print("--- Testing Single Generation ---")
    try:
        response = generate("Write a 1-sentence LinkedIn hook about AI Employees.")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

def test_streaming():
    print("\n--- Testing Streaming Generation ---")
    try:
        print("Response: ", end="", flush=True)
        for chunk in generate_stream("List 3 benefits of AI automation."):
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Check if keys are set
    from src.core.config import get_settings
    settings = get_settings()
    
    if not settings.GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY is not set.")
    if not settings.GROK_API_KEY:
        print("WARNING: GROK_API_KEY is not set.")
        
    test_single()
    test_streaming()
