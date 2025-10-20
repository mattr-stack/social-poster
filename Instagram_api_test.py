#!/usr/bin/env python3
"""
Instagram API Debug Test
Test Instagram posting with detailed diagnostics
"""

import requests
import os
import json
import time

def test_instagram_credentials():
    """Test Instagram API credentials and permissions"""
    
    print("=== Instagram API Diagnostic Test ===\n")
    
    # Get credentials from environment
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN') or input("Instagram Access Token: ").strip()
    user_id = os.getenv('INSTAGRAM_USER_ID') or input("Instagram User ID: ").strip()
    app_id = os.getenv('INSTAGRAM_APP_ID') or input("Instagram App ID: ").strip()
    
    print(f"Access Token: {access_token[:20]}...{access_token[-10:]}")
    print(f"User ID: {user_id}")
    print(f"App ID: {app_id}\n")
    
    # Test 1: Verify account info
    print("--- Test 1: Verify Instagram Account ---")
    try:
        response = requests.get(
            f"https://graph.facebook.com/v23.0/{user_id}",
            params={
                'fields': 'id,username,name',  # Removed account_type - not available for IGUser
                'access_token': access_token
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}\n")
        
        if response.status_code == 200:
            account_data = response.json()
            print(f"✅ Account verified!")
            print(f"   Username: @{account_data.get('username', 'N/A')}")
            print(f"   Name: {account_data.get('name', 'N/A')}")
            print(f"   ID: {account_data.get('id')}\n")
        else:
            print("❌ Account verification failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False
    
    # Test 2: Check token permissions
    print("--- Test 2: Verify Token Permissions ---")
    try:
        response = requests.get(
            f"https://graph.facebook.com/v23.0/debug_token",
            params={
                'input_token': access_token,
                'access_token': access_token
            }
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json().get('data', {})
            print(f"App ID: {token_data.get('app_id')}")
            print(f"User ID: {token_data.get('user_id')}")
            print(f"Valid: {token_data.get('is_valid')}")
            print(f"Scopes: {token_data.get('scopes', [])}")
            
            required_scopes = ['instagram_basic', 'instagram_content_publish', 'pages_read_engagement']
            missing_scopes = [s for s in required_scopes if s not in token_data.get('scopes', [])]
            
            if missing_scopes:
                print(f"⚠️  Missing required scopes: {missing_scopes}\n")
            else:
                print("✅ All required permissions present!\n")
        else:
            print(f"Response: {response.text}\n")
    except Exception as e:
        print(f"⚠️  Could not verify permissions: {str(e)}\n")
    
    # Test 3: Test image container creation
    print("--- Test 3: Create Test Media Container ---")
    
    test_image_url = os.getenv('INSTAGRAM_IMAGE_URL') or input("Enter test image URL (or press Enter for default): ").strip()
    if not test_image_url:
        test_image_url = "https://picsum.photos/800/800"
    
    print(f"Using image: {test_image_url}")
    
    # Verify image is accessible
    try:
        img_check = requests.head(test_image_url, timeout=5)
        print(f"Image URL check: {img_check.status_code}")
        if img_check.status_code != 200:
            print(f"⚠️  Image might not be accessible!\n")
    except Exception as e:
        print(f"⚠️  Cannot verify image: {str(e)}\n")
    
    # Create container
    container_data = {
        'image_url': test_image_url,
        'caption': 'Test post from Instagram API diagnostic tool',
        'access_token': access_token,
        'app_id': app_id
    }
    
    print("\nRequest data:")
    print(f"  image_url: {test_image_url}")
    print(f"  app_id: {app_id}")
    print(f"  access_token: {access_token[:20]}...\n")
    
    try:
        response = requests.post(
            f"https://graph.facebook.com/v23.0/{user_id}/media",
            data=container_data
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}\n")
        
        if response.status_code == 200:
            container_id = response.json()['id']
            print(f"✅ Container created successfully!")
            print(f"   Container ID: {container_id}\n")
            
            # Ask if user wants to publish
            publish = (os.getenv('INSTAGRAM_PUBLISH') or input("Publish this test post to Instagram? (y/n): ")).strip().lower()
            
            if publish == 'y':
                print("\n--- Test 4: Publishing Media ---")
                time.sleep(5)  # Wait for Instagram to process
                
                publish_response = requests.post(
                    f"https://graph.facebook.com/v23.0/{user_id}/media_publish",
                    data={
                        'creation_id': container_id,
                        'access_token': access_token
                    }
                )
                
                print(f"Status: {publish_response.status_code}")
                print(f"Response: {publish_response.text}\n")
                
                if publish_response.status_code == 200:
                    print("✅ Published successfully to Instagram!")
                    print("\n🎉 All tests passed! Your Instagram integration is working.")
                else:
                    print("❌ Publish failed!")
                    try:
                        error_data = publish_response.json()
                        print(f"Error: {error_data.get('error', {}).get('message')}")
                    except:
                        pass
            else:
                print("Skipping publish. Container created but not published.")
                
        else:
            print("❌ Container creation failed!")
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {})
                print(f"\nError Details:")
                print(f"  Message: {error_msg.get('message')}")
                print(f"  Type: {error_msg.get('type')}")
                print(f"  Code: {error_msg.get('code')}")
                print(f"  Trace ID: {error_msg.get('fbtrace_id')}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_instagram_credentials()