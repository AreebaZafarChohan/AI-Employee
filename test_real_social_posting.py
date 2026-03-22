#!/usr/bin/env python3
"""
Real Social Media Posting Test

Tests real posting to Twitter, Facebook, and Instagram using:
1. Direct API calls from watchers
2. MCP server tools

Uses credentials from .env.gold-tier.example
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Load .env.gold-tier.example
env_file = ROOT / ".env.gold-tier.example"
print(f"[INFO] Loading environment from: {env_file}")

# Parse .env file manually
env_vars = {}
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
                os.environ[key.strip()] = value.strip()

print("[OK] Environment loaded!\n")

# Test post content
TEST_POST = "[GO] Gold Tier Test Post from AI-Employee! Testing real API integration. #Hackathon #AI #Automation"

# ============================================================================
# Twitter Test
# ============================================================================
def test_twitter_post():
    """Test posting to Twitter using Tweepy"""
    print("\n" + "="*70)
    print("[TW] TWITTER POST TEST")
    print("="*70)
    
    api_key = os.getenv("TWITTER_API_KEY", "")
    api_secret = os.getenv("TWITTER_API_SECRET", "")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")
    
    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("[ERR] Twitter credentials not found!")
        return False
    
    print(f"[Y] API Key: {api_key[:10]}...")
    print(f"[Y] Access Token: {access_token[:10]}...")
    
    try:
        import tweepy
        
        # Authenticate
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        
        print("[Y] Authenticated with Twitter API v2")
        
        # Post tweet
        print(f"[MSG] Posting: {TEST_POST[:50]}...")
        response = client.create_tweet(text=TEST_POST)
        
        if response.data:
            tweet_id = response.data['id']
            print(f"[OK] Tweet posted successfully!")
            print(f"🔗 Tweet ID: {tweet_id}")
            print(f"🔗 URL: https://twitter.com/user/status/{tweet_id}")
            return True
        else:
            print("[ERR] Failed to post tweet")
            return False
            
    except ImportError:
        print("[ERR] Tweepy not installed. Run: pip install tweepy")
        return False
    except Exception as e:
        print(f"[ERR] Error: {e}")
        return False

# ============================================================================
# Facebook Test
# ============================================================================
def test_facebook_post():
    """Test posting to Facebook using Graph API"""
    print("\n" + "="*70)
    print("[FB] FACEBOOK POST TEST")
    print("="*70)
    
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    
    if not access_token:
        print("[ERR] Facebook access token not found!")
        return False
    
    if not page_id:
        print("[ERR] Facebook page ID not found!")
        return False
    
    print(f"[Y] Access Token: {access_token[:20]}...")
    print(f"[Y] Page ID: {page_id}")
    
    try:
        import httpx
        
        # Post to Facebook Page
        url = f"https://graph.facebook.com/{page_id}/feed"
        params = {
            "message": TEST_POST,
            "access_token": access_token
        }
        
        print(f"[MSG] Posting to Page: {page_id}")
        print(f"[MSG] Content: {TEST_POST[:50]}...")
        
        response = httpx.post(url, data=params, timeout=30)
        result = response.json()
        
        if response.status_code == 200 and 'id' in result:
            post_id = result['id']
            print(f"[OK] Facebook post successful!")
            print(f"🔗 Post ID: {post_id}")
            print(f"🔗 URL: https://facebook.com/{post_id}")
            return True
        else:
            print(f"[ERR] Facebook API Error: {result}")
            return False
            
    except ImportError:
        print("[ERR] httpx not installed. Run: pip install httpx")
        return False
    except Exception as e:
        print(f"[ERR] Error: {e}")
        return False

# ============================================================================
# Instagram Test
# ============================================================================
def test_instagram_post():
    """Test posting to Instagram using Graph API"""
    print("\n" + "="*70)
    print("[IG] INSTAGRAM POST TEST")
    print("="*70)
    
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    business_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    
    if not access_token:
        print("[ERR] Instagram access token not found!")
        return False
    
    if not business_account_id:
        print("[ERR] Instagram business account ID not found!")
        return False
    
    print(f"[Y] Access Token: {access_token[:20]}...")
    print(f"[Y] Business Account ID: {business_account_id}")
    
    try:
        import httpx
        
        # Instagram requires image URL for posts
        # For testing, we'll use a placeholder image
        image_url = "https://picsum.photos/seed/testpost/1080/1080.jpg"
        caption = TEST_POST
        
        # Step 1: Create media container
        url = f"https://graph.facebook.com/v18.0/{business_account_id}/media"
        params = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token
        }
        
        print(f"[MSG] Creating media container...")
        print(f"[MSG] Image: {image_url}")
        print(f"[MSG] Caption: {caption[:50]}...")
        
        response = httpx.post(url, data=params, timeout=30)
        result = response.json()
        
        if response.status_code == 200 and 'id' in result:
            creation_id = result['id']
            print(f"[Y] Media container created: {creation_id}")
            
            # Step 2: Publish the media
            publish_url = f"https://graph.facebook.com/v18.0/{business_account_id}/media_publish"
            publish_params = {
                "creation_id": creation_id,
                "access_token": access_token
            }
            
            print(f"[MSG] Publishing media...")
            publish_response = httpx.post(publish_url, data=publish_params, timeout=30)
            publish_result = publish_response.json()
            
            if publish_response.status_code == 200 and 'id' in publish_result:
                media_id = publish_result['id']
                print(f"[OK] Instagram post successful!")
                print(f"🔗 Media ID: {media_id}")
                return True
            else:
                print(f"[ERR] Publish Error: {publish_result}")
                return False
        else:
            print(f"[ERR] Media Creation Error: {result}")
            return False
            
    except ImportError:
        print("[ERR] httpx not installed. Run: pip install httpx")
        return False
    except Exception as e:
        print(f"[ERR] Error: {e}")
        return False

# ============================================================================
# MCP Server Tests
# ============================================================================
def test_mcp_twitter_post():
    """Test posting via MCP Twitter Server"""
    print("\n" + "="*70)
    print("[MCP] MCP TWITTER SERVER TEST")
    print("="*70)
    
    mcp_port = os.getenv("MCP_TWITTER_PORT", "8087")
    mcp_url = f"{os.getenv('MCP_SERVER_URL', 'http://localhost')}:{mcp_port}"
    
    print(f"[URL] MCP Server URL: {mcp_url}")
    
    try:
        import httpx
        
        # Call MCP tool
        tool_url = f"{mcp_url}/tools/publish_tweet"
        payload = {
            "text": TEST_POST,
            "auto_approve": True
        }
        
        print(f"[MSG] Calling MCP tool: publish_tweet")
        print(f"[MSG] Content: {TEST_POST[:50]}...")
        
        response = httpx.post(tool_url, json=payload, timeout=30)
        result = response.json()
        
        if response.status_code == 200:
            print(f"[OK] MCP Twitter post successful!")
            print(f"[RES] Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"[ERR] MCP Error: {result}")
            return False
            
    except ImportError:
        print("[ERR] httpx not installed")
        return False
    except Exception as e:
        print(f"[ERR] Error: {e}")
        return False

def test_mcp_facebook_post():
    """Test posting via MCP Facebook Server"""
    print("\n" + "="*70)
    print("[MCP] MCP FACEBOOK SERVER TEST")
    print("="*70)
    
    mcp_port = os.getenv("MCP_FACEBOOK_PORT", "8085")
    mcp_url = f"{os.getenv('MCP_SERVER_URL', 'http://localhost')}:{mcp_port}"
    
    print(f"[URL] MCP Server URL: {mcp_url}")
    
    try:
        import httpx
        
        tool_url = f"{mcp_url}/tools/publish_facebook_post"
        payload = {
            "message": TEST_POST,
            "page_id": os.getenv("FACEBOOK_PAGE_ID", ""),
            "auto_approve": True
        }
        
        print(f"[MSG] Calling MCP tool: publish_facebook_post")
        print(f"[MSG] Content: {TEST_POST[:50]}...")
        
        response = httpx.post(tool_url, json=payload, timeout=30)
        result = response.json()
        
        if response.status_code == 200:
            print(f"[OK] MCP Facebook post successful!")
            print(f"[RES] Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"[ERR] MCP Error: {result}")
            return False
            
    except ImportError:
        print("[ERR] httpx not installed")
        return False
    except Exception as e:
        print(f"[ERR] Error: {e}")
        return False

def test_mcp_instagram_post():
    """Test posting via MCP Instagram Server"""
    print("\n" + "="*70)
    print("[MCP] MCP INSTAGRAM SERVER TEST")
    print("="*70)
    
    mcp_port = os.getenv("MCP_INSTAGRAM_PORT", "8086")
    mcp_url = f"{os.getenv('MCP_SERVER_URL', 'http://localhost')}:{mcp_port}"
    
    print(f"[URL] MCP Server URL: {mcp_url}")
    
    try:
        import httpx
        
        tool_url = f"{mcp_url}/tools/publish_instagram_post"
        payload = {
            "caption": TEST_POST,
            "image_url": "https://picsum.photos/seed/testpost/1080/1080.jpg",
            "auto_approve": True
        }
        
        print(f"[MSG] Calling MCP tool: publish_instagram_post")
        print(f"[MSG] Content: {TEST_POST[:50]}...")
        
        response = httpx.post(tool_url, json=payload, timeout=30)
        result = response.json()
        
        if response.status_code == 200:
            print(f"[OK] MCP Instagram post successful!")
            print(f"[RES] Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"[ERR] MCP Error: {result}")
            return False
            
    except ImportError:
        print("[ERR] httpx not installed")
        return False
    except Exception as e:
        print(f"[ERR] Error: {e}")
        return False

# ============================================================================
# Main Test Runner
# ============================================================================
def main():
    print("\n" + "="*70)
    print("[GO] GOLD TIER - REAL SOCIAL MEDIA POSTING TEST")
    print("="*70)
    print(f"📅 Time: {datetime.now().isoformat()}")
    print(f"[MSG] Test Post: {TEST_POST}")
    print("="*70)
    
    results = {
        "Twitter Direct API": False,
        "Facebook Direct API": False,
        "Instagram Direct API": False,
        "MCP Twitter Server": False,
        "MCP Facebook Server": False,
        "MCP Instagram Server": False,
    }
    
    # Test Direct API calls
    print("\n📌 PHASE 1: Direct API Calls")
    print("-"*70)
    
    results["Twitter Direct API"] = test_twitter_post()
    results["Facebook Direct API"] = test_facebook_post()
    results["Instagram Direct API"] = test_instagram_post()
    
    # Test MCP Servers
    print("\n📌 PHASE 2: MCP Server Calls")
    print("-"*70)
    
    results["MCP Twitter Server"] = test_mcp_twitter_post()
    results["MCP Facebook Server"] = test_mcp_facebook_post()
    results["MCP Instagram Server"] = test_mcp_instagram_post()
    
    # Summary
    print("\n" + "="*70)
    print("[SUM] TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[OK] PASS" if result else "[ERR] FAIL"
        print(f"{status} | {test_name}")
    
    print("-"*70)
    print(f"[STAT] Results: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    print("="*70)
    
    # Save results
    results_file = ROOT / "test_results_social_posting.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_post": TEST_POST,
            "results": results,
            "passed": passed,
            "total": total
        }, f, indent=2)
    
    print(f"[SAVE] Results saved to: {results_file}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
