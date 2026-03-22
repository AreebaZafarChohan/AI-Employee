#!/usr/bin/env python3
"""
Gold Tier - Real Social Media Auto-Posting Test

Tests real posting to Twitter, Facebook, and Instagram using:
1. Direct API calls
2. Browser automation (Playwright) as fallback

Usage:
    python test_auto_post.py
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add project root
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Test post content
TEST_POST = "🚀 Gold Tier Test - AI-Employee Project! Testing real social media automation. #Hackathon #AI #Automation"

print("="*70)
print("🚀 GOLD TIER - REAL AUTO-POSTING TEST")
print("="*70)
print(f"📅 Time: {datetime.now().isoformat()}")
print(f"📝 Test Post: {TEST_POST[:80]}...")
print("="*70)

# ============================================================================
# Load Environment
# ============================================================================
print("\n📂 Loading environment from .env.gold-tier.example...")

env_file = ROOT / ".env.gold-tier.example"
env_vars = {}

if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
                os.environ[key.strip()] = value.strip()

print("✅ Environment loaded!")

# ============================================================================
# Test Twitter via API
# ============================================================================
def test_twitter_api():
    print("\n" + "="*70)
    print("🐦 TWITTER API TEST")
    print("="*70)
    
    api_key = os.getenv("TWITTER_API_KEY", "")
    api_secret = os.getenv("TWITTER_API_SECRET", "")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    
    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("❌ Twitter credentials missing!")
        return False
    
    print(f"✓ API Key: {api_key[:15]}...")
    print(f"✓ Token: {access_token[:15]}...")
    
    try:
        import tweepy
        
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )
        
        # Verify credentials
        me = client.get_me()
        if me.data:
            print(f"✓ Logged in as: @{me.data.username}")
        
        # Post tweet
        print(f"📝 Posting tweet...")
        response = client.create_tweet(text=TEST_POST)
        
        if response.data:
            tweet_id = response.data['id']
            print(f"✅ Tweet posted!")
            print(f"🔗 https://twitter.com/user/status/{tweet_id}")
            return True
        else:
            print("❌ Failed to post")
            return False
            
    except ImportError:
        print("⚠️  Tweepy not installed. Install with: pip install tweepy")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# Test Facebook via API
# ============================================================================
def test_facebook_api():
    print("\n" + "="*70)
    print("📘 FACEBOOK API TEST")
    print("="*70)
    
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    
    if not access_token:
        print("❌ Facebook access token missing!")
        return False
    
    if not page_id:
        print("❌ Facebook page ID missing!")
        return False
    
    print(f"✓ Token: {access_token[:30]}...")
    print(f"✓ Page ID: {page_id}")
    
    try:
        import httpx
        
        # Post to Facebook Page
        url = f"https://graph.facebook.com/{page_id}/feed"
        params = {
            "message": TEST_POST,
            "access_token": access_token
        }
        
        print(f"📝 Posting to Facebook Page...")
        
        response = httpx.post(url, data=params, timeout=30)
        result = response.json()
        
        if response.status_code == 200 and 'id' in result:
            post_id = result['id']
            print(f"✅ Facebook post successful!")
            print(f"🔗 https://facebook.com/{post_id}")
            return True
        else:
            print(f"❌ Error: {result}")
            return False
            
    except ImportError:
        print("⚠️  httpx not installed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# Test Instagram via API
# ============================================================================
def test_instagram_api():
    print("\n" + "="*70)
    print("📸 INSTAGRAM API TEST")
    print("="*70)
    
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    business_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    
    if not access_token:
        print("❌ Instagram access token missing!")
        return False
    
    if not business_account_id:
        print("❌ Instagram business account ID missing!")
        return False
    
    print(f"✓ Token: {access_token[:30]}...")
    print(f"✓ Business ID: {business_account_id}")
    
    try:
        import httpx
        
        # Use a test image
        image_url = "https://picsum.photos/seed/goldtier/1080/1080.jpg"
        caption = TEST_POST
        
        # Step 1: Create media container
        url = f"https://graph.facebook.com/v18.0/{business_account_id}/media"
        params = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token
        }
        
        print(f"📝 Creating media container...")
        
        response = httpx.post(url, data=params, timeout=30)
        result = response.json()
        
        if response.status_code == 200 and 'id' in result:
            creation_id = result['id']
            print(f"✓ Media container created: {creation_id}")
            
            # Step 2: Publish
            publish_url = f"https://graph.facebook.com/v18.0/{business_account_id}/media_publish"
            publish_params = {
                "creation_id": creation_id,
                "access_token": access_token
            }
            
            print(f"📝 Publishing...")
            
            publish_response = httpx.post(publish_url, data=publish_params, timeout=30)
            publish_result = publish_response.json()
            
            if publish_response.status_code == 200 and 'id' in publish_result:
                media_id = publish_result['id']
                print(f"✅ Instagram post successful!")
                print(f"🔗 Media ID: {media_id}")
                return True
            else:
                print(f"❌ Publish error: {publish_result}")
                return False
        else:
            print(f"❌ Media creation error: {result}")
            return False
            
    except ImportError:
        print("⚠️  httpx not installed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# Test via Browser Automation (Playwright)
# ============================================================================
def test_twitter_browser():
    print("\n" + "="*70)
    print("🐦 TWITTER BROWSER AUTOMATION TEST")
    print("="*70)
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("🌐 Launching browser...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Go to Twitter login
            print("📝 Navigate to Twitter...")
            page.goto("https://twitter.com/login", timeout=60000)
            
            # Wait for login page
            page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
            
            print("⏳ Waiting for manual login (60 seconds)...")
            print("   Please login to Twitter in the browser window")
            
            # Wait for user to login
            try:
                page.wait_for_url("https://twitter.com/home", timeout=60000)
                print("✓ Login detected!")
            except:
                print("⚠️  Login timeout - continuing anyway")
            
            # Try to compose tweet
            try:
                print("📝 Finding compose box...")
                
                # Look for compose textarea
                compose_box = page.query_selector('[data-testid="tweetTextarea_0"]')
                
                if compose_box:
                    compose_box.click()
                    compose_box.fill(TEST_POST)
                    print("✓ Tweet content entered")
                    
                    # Find and click tweet button
                    tweet_button = page.query_selector('[data-testid="tweetButton"]')
                    if tweet_button:
                        print("📝 Clicking tweet button...")
                        tweet_button.click()
                        print("✅ Tweet posted via browser!")
                        time.sleep(3)
                        browser.close()
                        return True
                
                print("⚠️  Could not find compose box")
                
            except Exception as e:
                print(f"⚠️  Error posting: {e}")
            
            browser.close()
            return False
            
    except ImportError:
        print("⚠️  Playwright not installed. Install with: playwright install")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# Main
# ============================================================================
def main():
    print("\n📌 PHASE 1: Direct API Tests")
    print("-"*70)
    
    results = {
        "Twitter API": False,
        "Facebook API": False,
        "Instagram API": False,
    }
    
    results["Twitter API"] = test_twitter_api()
    results["Facebook API"] = test_facebook_api()
    results["Instagram API"] = test_instagram_api()
    
    # Summary
    print("\n" + "="*70)
    print("📊 API TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} passed ({(passed/total*100):.1f}%)")
    
    # Save results
    results_file = ROOT / "test_results_api.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_post": TEST_POST,
            "results": results,
            "passed": passed,
            "total": total
        }, f, indent=2)
    
    print(f"💾 Results saved to: {results_file}")
    print("="*70)
    
    return passed > 0

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ SOME TESTS PASSED - Check your social media accounts!")
    else:
        print("\n⚠️  ALL TESTS FAILED - Check credentials and try again")
    
    sys.exit(0 if success else 1)
