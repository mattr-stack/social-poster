#!/usr/bin/env python3
"""
Threads OAuth2 Test Script
Test your Threads app credentials and generate access tokens
"""

import requests
import json
import os
from datetime import datetime
import webbrowser
from urllib.parse import urlencode

class ThreadsTokenManager:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://graph.threads.net/v23.0"
        self.oauth_url = "https://threads.net/oauth"
    
    def generate_login_url(self, redirect_uri: str = "https://localhost:8080") -> str:
        """Generate Threads login URL for getting user access token"""
        params = {
            'client_id': self.app_id,
            'redirect_uri': redirect_uri,
            'scope': 'threads_basic,threads_content_publish',
            'response_type': 'code',
            'state': 'threads_oauth_state'
        }
        
        login_url = f"{self.oauth_url}/authorize?{urlencode(params)}"
        return login_url
    
    def exchange_code_for_token(self, code: str, redirect_uri: str = "https://graph.threads.net/oauth/access_token") -> dict:
        """Exchange authorization code for access token"""
        try:
            data = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'redirect_uri': redirect_uri,
                'code': code,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(f"{self.oauth_url}/access_token", data=data)
            
            print(f"Token exchange status: {response.status_code}")
            print(f"Token exchange response: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error exchanging code: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def get_long_lived_token(self, short_token: str) -> dict:
        """Convert short-lived token to long-lived (60 days)"""
        try:
            params = {
                'grant_type': 'th_exchange_token',
                'client_secret': self.app_secret,
                'access_token': short_token
            }
            
            response = requests.get(f"{self.base_url}/access_token", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting long-lived token: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def get_user_profile(self, access_token: str) -> dict:
        """Get Threads user profile information"""
        try:
            params = {
                'fields': 'id,username,name,threads_profile_picture_url,threads_biography',
                'access_token': access_token
            }
            
            response = requests.get(f"{self.base_url}/me", params=params)
            
            print(f"Profile lookup status: {response.status_code}")
            print(f"Profile lookup response: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting profile: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def create_threads_post(self, user_id: str, access_token: str, text: str = None) -> bool:
        """Create a test Threads post"""
        try:
            if not text:
                text = f"Test post from automation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} #automation #test"
            
            # Step 1: Create media container
            container_data = {
                'media_type': 'TEXT',
                'text': text,
                'access_token': access_token
            }
            
            print(f"Creating Threads media container...")
            container_response = requests.post(
                f"{self.base_url}/{user_id}/threads",
                data=container_data
            )
            
            print(f"Container creation status: {container_response.status_code}")
            print(f"Container creation response: {container_response.text}")
            
            if container_response.status_code != 200:
                print(f"❌ Container creation failed")
                return False
            
            container_id = container_response.json()['id']
            print(f"✅ Created container: {container_id}")
            
            # Step 2: Publish the thread
            publish_data = {
                'creation_id': container_id,
                'access_token': access_token
            }
            
            print(f"Publishing Threads post...")
            publish_response = requests.post(
                f"{self.base_url}/{user_id}/threads_publish",
                data=publish_data
            )
            
            print(f"Publish status: {publish_response.status_code}")
            print(f"Publish response: {publish_response.text}")
            
            if publish_response.status_code == 200:
                post_data = publish_response.json()
                post_id = post_data.get('id')
                print(f"✅ Successfully created Threads post! ID: {post_id}")
                return True
            else:
                print(f"❌ Failed to publish Threads post")
                return False
                
        except Exception as e:
            print(f"Error posting to Threads: {str(e)}")
            return False

def test_app_credentials(app_id: str, app_secret: str):
    """Basic test to see if app credentials are valid"""
    print(f"Testing Threads app credentials...")
    print(f"App ID: {app_id}")
    print(f"App Secret: {app_secret[:10]}...")
    
    # Try to make a basic request to see if credentials work
    try:
        # This might fail, but we can see the error response
        response = requests.get(f"https://graph.threads.net/v23.0/me?access_token=test")
        print(f"Basic test response: {response.status_code}")
        if response.status_code == 400:
            error_data = response.json()
            if error_data.get('error', {}).get('code') == 190:
                print("✅ App seems configured (got expected invalid token error)")
                return True
    except:
        pass
    
    return False

def main():
    print("=== Threads OAuth2 Test Script ===\n")
    
    # Get app credentials
    app_id = os.getenv('THREADS_APP_ID')
    app_secret = os.getenv('THREADS_APP_SECRET')
    
    if not app_id:
        app_id = input("Enter your Threads App ID: ").strip()
    
    if not app_secret:
        app_secret = input("Enter your Threads App Secret: ").strip()
    
    if not app_id or not app_secret:
        print("❌ App ID and Secret are required!")
        return
    
    # Test basic app setup
    test_app_credentials(app_id, app_secret)
    
    token_manager = ThreadsTokenManager(app_id, app_secret)
    
    print("\n=== Threads Token Generation ===")
    print("Threads uses OAuth2 flow similar to Facebook/Instagram")
    print("You'll need to:")
    print("1. Authorize your app through browser login")
    print("2. Get authorization code from redirect")
    print("3. Exchange code for access token")
    print("4. Convert to long-lived token")
    
    # Choose redirect URI
    print("\n--- Redirect URI Options ---")
    print("1. https://localhost:8080 (requires adding to app settings)")
    print("2. https://example.com (simple fallback)")
    
    choice = input("Choose redirect URI option (1 or 2): ").strip()
    
    if choice == "2":
        redirect_uri = "https://example.com"
        print(f"Using: {redirect_uri}")
        print("⚠️ Make sure to add this to your app's OAuth Redirect URIs")
    else:
        redirect_uri = "https://localhost:8080"
        print(f"Using: {redirect_uri}")
        print("⚠️ Make sure to add this to your app's OAuth Redirect URIs")
    
    # Generate OAuth URL
    login_url = token_manager.generate_login_url(redirect_uri)
    
    print(f"\n--- Step 1: User Authorization ---")
    print(f"1. Opening Threads authorization URL...")
    print(f"Login URL: {login_url}")
    
    try:
        webbrowser.open(login_url)
        print("✅ Browser opened")
    except:
        print("⚠️ Could not open browser automatically")
        print("Please copy and paste the URL above into your browser")
    
    print(f"\n2. After authorization, you'll be redirected to:")
    print(f"   {redirect_uri}/?code=ABC123&state=threads_oauth_state")
    if redirect_uri == "https://localhost:8080":
        print(f"   (The page will show an error - that's normal)")
    else:
        print(f"   (Look in the URL bar for the code parameter)")
    
    auth_code = input("\n3. Enter the 'code' parameter from the redirect URL: ").strip()
    
    if not auth_code:
        print("❌ Authorization code required")
        return
    
    # Exchange code for token
    print(f"\n--- Step 2: Token Exchange ---")
    token_data = token_manager.exchange_code_for_token(auth_code, redirect_uri)
    
    if not token_data:
        print("❌ Failed to exchange code for token")
        print("\nPossible issues:")
        print("- Code expired (try again quickly)")
        print("- Redirect URI mismatch")
        print("- App not properly configured for Threads")
        print("- Missing threads_basic permission")
        print(f"\n🔧 Quick Fix: Add '{redirect_uri}' to your app's OAuth Redirect URIs")
        return
    
    access_token = token_data.get('access_token')
    user_id = token_data.get('user_id')
    
    if not access_token:
        print("❌ No access token received")
        return
    
    print(f"✅ Got access token!")
    print(f"User ID: {user_id}")
    
    # Get long-lived token
    print(f"\n--- Step 3: Long-lived Token ---")
    long_token_data = token_manager.get_long_lived_token(access_token)
    
    if long_token_data:
        final_token = long_token_data.get('access_token', access_token)
        expires_in = long_token_data.get('expires_in', 'unknown')
        print(f"✅ Got long-lived token (expires in {expires_in} seconds)")
    else:
        final_token = access_token
        print("⚠️ Using short-lived token")
    
    # Get user profile
    print(f"\n--- Step 4: Profile Test ---")
    profile = token_manager.get_user_profile(final_token)
    
    if profile:
        username = profile.get('username', 'Unknown')
        name = profile.get('name', 'Unknown')
        print(f"✅ Successfully authenticated!")
        print(f"Username: @{username}")
        print(f"Name: {name}")
        
        # Test posting
        test_post = input(f"\nDo you want to test creating a Threads post? (y/n): ").strip().lower()
        if test_post == 'y':
            custom_text = input("Enter custom post text (or press Enter for default): ").strip()
            if not custom_text:
                custom_text = None
            
            success = token_manager.create_threads_post(profile['id'], final_token, custom_text)
            
            if success:
                print(f"\n✅ Threads integration test successful!")
            else:
                print(f"\n❌ Threads posting failed")
        
        print(f"\n=== Environment Variables ===")
        print(f"THREADS_ACCESS_TOKEN={final_token}")
        print(f"THREADS_USER_ID={profile['id']}")
        print(f"THREADS_APP_ID={app_id}")
        print(f"THREADS_APP_SECRET={app_secret}")
    
    else:
        print("❌ Failed to get profile - check token and permissions")

if __name__ == "__main__":
    main()