#!/usr/bin/env python3
"""
Meta (Facebook/Instagram) Token Generator and Tester
This script helps you generate and test Facebook/Instagram API tokens
"""

import requests
import json
import os
from datetime import datetime
import webbrowser
from urllib.parse import urlencode

class MetaTokenManager:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://graph.facebook.com/v23.0"
    
    def generate_login_url(self, redirect_uri: str = "https://localhost:8080") -> str:
        """Generate Facebook login URL for getting user access token"""
        params = {
            'client_id': self.app_id,
            'redirect_uri': redirect_uri,
            'scope': 'pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish,business_management',
            'response_type': 'code',
            'state': 'your_app_state'
        }
        
        login_url = f"https://www.facebook.com/v23.0/dialog/oauth?{urlencode(params)}"
        return login_url
    
    def exchange_code_for_token(self, code: str, redirect_uri: str = "https://localhost:8080") -> dict:
        """Exchange authorization code for user access token"""
        try:
            params = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'redirect_uri': redirect_uri,
                'code': code
            }
            
            response = requests.get(f"{self.base_url}/oauth/access_token", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error exchanging code: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def get_long_lived_user_token(self, short_token: str) -> dict:
        """Convert short-lived user token to long-lived (60 days)"""
        try:
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'fb_exchange_token': short_token
            }
            
            response = requests.get(f"{self.base_url}/oauth/access_token", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting long-lived token: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def get_user_pages(self, user_token: str) -> list:
        """Get user's Facebook pages"""
        try:
            params = {
                'access_token': user_token,
                'fields': 'id,name,access_token,instagram_business_account'
            }
            
            response = requests.get(f"{self.base_url}/me/accounts", params=params)
            
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                print(f"Error getting pages: {response.text}")
                return []
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return []
    
    def get_page_long_lived_token(self, page_token: str) -> dict:
        """Convert page token to long-lived (never expires)"""
        try:
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'fb_exchange_token': page_token
            }
            
            response = requests.get(f"{self.base_url}/oauth/access_token", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting long-lived page token: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def test_facebook_post(self, page_id: str, page_token: str, message: str = None) -> bool:
        """Test posting to Facebook page"""
        try:
            if not message:
                message = f"Test post from automation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            data = {
                'message': message,
                'access_token': page_token
            }
            
            response = requests.post(f"{self.base_url}/{page_id}/feed", data=data)
            
            if response.status_code == 200:
                post_data = response.json()
                post_id = post_data.get('id')
                print(f"✅ Facebook post successful! Post ID: {post_id}")
                return True
            else:
                print(f"❌ Facebook post failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error posting to Facebook: {str(e)}")
            return False
    
    def test_instagram_post(self, instagram_user_id: str, page_token: str, image_url: str = None, caption: str = None) -> bool:
        """Test posting to Instagram"""
        try:
            if not image_url:
                image_url = "https://picsum.photos/400/400"  # Random test image
            
            if not caption:
                caption = f"Test post from automation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} #automation #test"
            
            # Step 1: Create media container
            container_data = {
                'image_url': image_url,
                'caption': caption,
                'access_token': page_token
            }
            
            container_response = requests.post(
                f"{self.base_url}/{instagram_user_id}/media",
                data=container_data
            )
            
            if container_response.status_code != 200:
                print(f"❌ Instagram container creation failed: {container_response.text}")
                return False
            
            container_id = container_response.json()['id']
            print(f"📷 Created Instagram media container: {container_id}")
            
            # Step 2: Publish the media
            publish_data = {
                'creation_id': container_id,
                'access_token': page_token
            }
            
            publish_response = requests.post(
                f"{self.base_url}/{instagram_user_id}/media_publish",
                data=publish_data
            )
            
            if publish_response.status_code == 200:
                post_data = publish_response.json()
                post_id = post_data.get('id')
                print(f"✅ Instagram post successful! Post ID: {post_id}")
                return True
            else:
                print(f"❌ Instagram post failed: {publish_response.text}")
                return False
                
        except Exception as e:
            print(f"Error posting to Instagram: {str(e)}")
            return False

def main():
    print("=== Meta (Facebook/Instagram) Token Generator ===\n")
    
    # Get app credentials
    app_id = os.getenv('FACEBOOK_APP_ID')
    app_secret = os.getenv('FACEBOOK_APP_SECRET')
    
    if not app_id:
        app_id = input("Enter your Facebook App ID: ").strip()
    
    if not app_secret:
        app_secret = input("Enter your Facebook App Secret: ").strip()
    
    if not app_id or not app_secret:
        print("❌ App ID and Secret are required!")
        return
    
    token_manager = MetaTokenManager(app_id, app_secret)
    
    print("=== Token Generation Process ===\n")
    print("Facebook/Instagram tokens require a multi-step OAuth2 flow:")
    print("1. User authorization (browser login)")
    print("2. Exchange code for short-lived user token")
    print("3. Convert to long-lived user token")
    print("4. Get page access tokens")
    print("5. Convert page tokens to long-lived (never expire)")
    
    # Method 1: Manual token generation
    print("\n--- Method 1: Manual Token Generation ---")
    print("1. Go to Facebook Graph API Explorer:")
    print("   https://developers.facebook.com/tools/explorer/")
    print("2. Select your app")
    print("3. Get User Token with permissions:")
    print("   - pages_manage_posts")
    print("   - pages_read_engagement") 
    print("   - instagram_basic")
    print("   - instagram_content_publish")
    print("4. Copy the token here")
    
    manual_token = input("\nEnter your token from Graph API Explorer (or press Enter to skip): ").strip()
    
    if manual_token:
        print("\n--- Processing Manual Token ---")
        
        # Convert to long-lived user token
        long_user_token_data = token_manager.get_long_lived_user_token(manual_token)
        
        if long_user_token_data:
            long_user_token = long_user_token_data['access_token']
            print(f"✅ Got long-lived user token (expires in {long_user_token_data.get('expires_in', 'unknown')} seconds)")
            
            # Get user's pages
            pages = token_manager.get_user_pages(long_user_token)
            
            if pages:
                print(f"\n--- Found {len(pages)} Facebook Pages ---")
                
                for i, page in enumerate(pages):
                    page_id = page['id']
                    page_name = page['name']
                    page_token = page['access_token']
                    instagram_account = page.get('instagram_business_account')
                    
                    print(f"\n{i+1}. {page_name} (ID: {page_id})")
                    
                    # Get long-lived page token
                    long_page_token_data = token_manager.get_page_long_lived_token(page_token)
                    
                    if long_page_token_data:
                        final_page_token = long_page_token_data['access_token']
                        print(f"   ✅ Long-lived page token: {final_page_token[:50]}...")
                        
                        if instagram_account:
                            instagram_id = instagram_account['id']
                            print(f"   📷 Connected Instagram Account ID: {instagram_id}")
                            
                            # Test posts
                            test_posts = input(f"   Test posts for {page_name}? (y/n): ").strip().lower()
                            if test_posts == 'y':
                                print(f"   Testing Facebook post...")
                                token_manager.test_facebook_post(page_id, final_page_token)
                                
                                print(f"   Testing Instagram post...")
                                token_manager.test_instagram_post(instagram_id, final_page_token)
                            
                            print(f"\n   === Environment Variables for {page_name} ===")
                            print(f"   FACEBOOK_ACCESS_TOKEN={final_page_token}")
                            print(f"   FACEBOOK_PAGE_ID={page_id}")
                            print(f"   INSTAGRAM_ACCESS_TOKEN={final_page_token}")  # Same token!
                            print(f"   INSTAGRAM_USER_ID={instagram_id}")
                        
                        else:
                            print(f"   ⚠️ No Instagram Business account connected")
                    else:
                        print(f"   ❌ Failed to get long-lived page token")
            else:
                print("❌ No pages found or insufficient permissions")
        else:
            print("❌ Failed to get long-lived user token")
    
    # Method 2: Automated OAuth flow (requires running server)
    print("\n--- Method 2: Automated OAuth Flow ---")
    automated = input("Want to try automated OAuth flow? (requires local server) (y/n): ").strip().lower()
    
    if automated == 'y':
        redirect_uri = "https://localhost:8080"
        login_url = token_manager.generate_login_url(redirect_uri)
        
        print(f"\n1. Opening browser to Facebook login...")
        print(f"Login URL: {login_url}")
        
        try:
            webbrowser.open(login_url)
        except:
            print("Could not open browser automatically. Please copy the URL above.")
        
        print(f"\n2. After login, you'll be redirected to localhost with a 'code' parameter")
        print(f"   Example: https://localhost:8080/?code=ABC123&state=your_app_state")
        
        auth_code = input("3. Enter the 'code' parameter from the redirect URL: ").strip()
        
        if auth_code:
            # Exchange code for token
            token_data = token_manager.exchange_code_for_token(auth_code, redirect_uri)
            
            if token_data:
                user_token = token_data['access_token']
                print("✅ Got user access token!")
                
                # Continue with the same process as manual method
                # (Get long-lived token, pages, etc.)
                print("Continuing with token processing...")
            else:
                print("❌ Failed to exchange code for token")
    
    print("\n=== Setup Summary ===")
    print("Key Points:")
    print("- Facebook and Instagram use THE SAME page access token")
    print("- Page tokens can be made to never expire (long-lived)")
    print("- You need a Facebook Page connected to an Instagram Business account")
    print("- The Instagram User ID is different from the Facebook Page ID")
    print("- Both platforms use the same Meta Graph API")
    
    print("\nRequired Facebook App Setup:")
    print("1. Create app at https://developers.facebook.com/")
    print("2. Add Facebook Login product")
    print("3. Add Instagram Basic Display product") 
    print("4. Set valid OAuth redirect URIs")
    print("5. Add necessary permissions in App Review (for production)")

if __name__ == "__main__":
    main()