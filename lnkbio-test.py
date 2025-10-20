#!/usr/bin/env python3
"""
lnk.bio OAuth2 Test Script
Run this to test your client credentials and generate access tokens
"""

import requests
import json
import os
from datetime import datetime

def test_client_credentials_flow(client_id: str, client_secret: str):
    """Test the client credentials OAuth2 flow using Basic Auth."""
    print(f"Testing OAuth2 flow with Client ID: {client_id}")
    
    # Data for token request
    token_data = {
        'grant_type': 'client_credentials'
    }
    
    # Headers with better user agent
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'lnk-bio-api-client/1.0'
    }
    
    print("\n1. Requesting access token using Basic Auth...")
    try:
        # Use Basic Auth with client_id:client_secret
        response = requests.post(
            'https://lnk.bio/oauth/token',
            data=token_data,
            auth=(client_id, client_secret),
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Response: {response.text[:500]}")
            print(f"❌ Failed to get access token! Status: {response.status_code}")
            return None
        
        token_info = response.json()
        access_token = token_info.get('access_token')
        expires_in = token_info.get('expires_in')
        token_type = token_info.get('token_type')
        scope = token_info.get('scope')
        
        print(f"✅ Success! Got access token!")
        print(f"   Token Type: {token_type}")
        print(f"   Expires In: {expires_in} seconds ({expires_in/60:.1f} minutes)")
        print(f"   Scope: {scope}")
        print(f"   Access Token: {access_token[:20]}...{access_token[-10:]}")
        
        return access_token
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed! Error: {e}")
        return None
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON from response.")
        return None


def make_api_request(method: str, endpoint: str, access_token: str, data: dict = None, description: str = "", use_form_data: bool = False):
    """Generic function to make API requests with proper error handling"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'User-Agent': 'lnk-bio-api-client/1.0'
    }
    
    if data and not use_form_data:
        headers['Content-Type'] = 'application/json'
    
    full_url = f"https://lnk.bio{endpoint}"
    
    if description:
        print(f"\n{description}")
    print(f"Requesting: {method} {full_url}")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(full_url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            if use_form_data:
                # Use form data (application/x-www-form-urlencoded)
                response = requests.post(full_url, headers=headers, data=data, timeout=10)
            else:
                # Use JSON
                response = requests.post(full_url, headers=headers, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return None
        
        print(f"Status Code: {response.status_code}")
        
        # Check if it's a Cloudflare block
        if response.status_code == 403 and 'cloudflare' in response.text.lower():
            print("⚠️  Cloudflare protection detected - this endpoint may require browser verification")
            return None
        
        if response.status_code in [200, 201]:
            try:
                return response.json()
            except:
                print(f"Response (text): {response.text[:200]}")
                return response.text
        else:
            print(f"Response: {response.text[:500]}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def test_endpoints(access_token: str):
    """Test various API endpoints to find what works"""
    print("\n" + "="*60)
    print("TESTING API ENDPOINTS")
    print("="*60)
    
    # Try different endpoint variations
    endpoints_to_test = [
        ('GET', '/oauth/v1/me', '2a. Testing /oauth/v1/me (User Info)'),
        ('GET', '/api/v1/user', '2b. Testing /api/v1/user'),
        ('GET', '/api/lnk/list', '2c. Testing /api/lnk/list (List Links)'),
        ('GET', '/api/v1/lnks', '2d. Testing /api/v1/lnks'),
    ]
    
    working_endpoints = []
    
    for method, endpoint, description in endpoints_to_test:
        result = make_api_request(method, endpoint, access_token, description=description)
        if result:
            print(f"✅ SUCCESS! This endpoint works!")
            print(f"   Response preview: {str(result)[:150]}...")
            working_endpoints.append((method, endpoint))
        print()
    
    return working_endpoints


def test_add_link(access_token: str, test_url: str = "https://example.com", test_title: str = "API Test Link"):
    """Test adding a link using the correct OpenAPI spec format"""
    print("\n" + "="*60)
    print("TESTING LINK CREATION")
    print("="*60)
    
    # Use 'link' not 'url' as per OpenAPI spec
    # Use form data (application/x-www-form-urlencoded) as per spec
    data = {
        'link': test_url,
        'title': test_title
    }
    
    print(f"\nData to send: {data}")
    
    # The correct endpoint from OpenAPI spec
    endpoint = '/oauth/v1/lnk/add'
    
    print(f"\nUsing official endpoint from OpenAPI spec: {endpoint}")
    print("Using Content-Type: application/x-www-form-urlencoded")
    
    result = make_api_request('POST', endpoint, access_token, data=data, use_form_data=True)
    
    if result:
        print(f"✅ SUCCESS! Link created!")
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        # Extract link ID and URL from response
        if isinstance(result, dict) and result.get('status') and result.get('data'):
            link_id = result['data'].get('id')
            link_url = result['data'].get('url')
            print(f"\n   Link ID: {link_id}")
            print(f"   Link URL: {link_url}")
        
        return True
    else:
        print(f"❌ Failed to create link")
        return False


def main():
    print("=== lnk.bio OAuth2 Test Script ===\n")
    
    # Get credentials from environment or input
    client_id = os.getenv('LINKBIO_CLIENT_ID')
    client_secret = os.getenv('LINKBIO_CLIENT_SECRET')
    
    if not client_id:
        client_id = input("Enter your lnk.bio Client ID: ").strip()
    
    if not client_secret:
        client_secret = input("Enter your lnk.bio Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Client ID and Secret are required!")
        return
    
    # Test the OAuth2 flow
    access_token = test_client_credentials_flow(client_id, client_secret)
    
    if not access_token:
        print("\n❌ Could not obtain access token. Check your credentials and the API status.")
        return
    
    # Test various endpoints to see what works
    working_endpoints = test_endpoints(access_token)
    
    if working_endpoints:
        print("\n" + "="*60)
        print("SUMMARY: Working Endpoints")
        print("="*60)
        for method, endpoint in working_endpoints:
            print(f"✅ {method} {endpoint}")
    else:
        print("\n⚠️  No endpoints returned successful responses.")
        print("This might be due to:")
        print("  - Cloudflare protection requiring browser verification")
        print("  - API permissions on your app")
        print("  - Rate limiting")
    
    # Ask if user wants to test link creation
    print("\n" + "="*60)
    test_link = input("Do you want to test creating a link? (y/n): ").strip().lower()
    if test_link == 'y':
        test_url = input("Enter test URL (or press Enter for example.com): ").strip()
        if not test_url:
            test_url = "https://example.com"
        
        test_title = input("Enter test title (or press Enter for 'API Test Link'): ").strip()
        if not test_title:
            test_title = "API Test Link"
        
        success = test_add_link(access_token, test_url, test_title)
        
        if success:
            print(f"\n✅ Integration test successful!")
        else:
            print(f"\n⚠️  Link creation failed on all tested endpoints.")
    
    print(f"\n" + "="*60)
    print("CREDENTIALS FOR .env FILE")
    print("="*60)
    print(f"LINKBIO_CLIENT_ID={client_id}")
    print(f"LINKBIO_CLIENT_SECRET={client_secret}")
    print(f"LINKBIO_ACCESS_TOKEN={access_token}")

if __name__ == "__main__":
    main()