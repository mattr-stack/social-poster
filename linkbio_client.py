import os
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import base64

logger = logging.getLogger(__name__)

class LinkBioClient:
    """Handle lnk.bio OAuth2 authentication and API calls with automatic token management"""

    def __init__(self, client_id, client_secret, group_id=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.group_id = group_id
        self.access_token = None
        self.token_expires_at = datetime.fromtimestamp(0)  # Force initial token fetch

    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or about to expire (60s buffer)"""
        buffer_time = timedelta(seconds=60)
        return datetime.now() >= (self.token_expires_at - buffer_time)

    def _get_new_token(self) -> bool:
        """Fetch a new access token using HTTP Basic Auth with client credentials"""
        try:
            token_data = {
                'grant_type': 'client_credentials',
            }

            headers = {
                'Accept': 'application/json',
                'User-Agent': 'lnk-bio-api-client/1.0'
            }

            response = requests.post(
                "https://lnk.bio/oauth/token",
                data=token_data,
                auth=(self.client_id, self.client_secret),
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                token_info = response.json()
                self.access_token = token_info['access_token']
                expires_in = token_info.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                logger.info("Successfully obtained new lnk.bio access token")
                return True
            else:
                logger.error(f"Failed to get lnk.bio access token: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error getting lnk.bio access token: {str(e)}")
            return False

    def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token, refreshing if necessary"""
        if self._is_token_expired():
            return self._get_new_token()
        return True

    def get_user_info(self) -> Optional[Dict]:
        """Get lnk.bio user profile information"""
        try:
            if not self._ensure_valid_token():
                logger.error("Failed to get valid lnk.bio token")
                return None

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json',
                'User-Agent': 'lnk-bio-api-client/1.0'
            }

            response = requests.get(
                "https://lnk.bio/oauth/v1/me",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get lnk.bio user info: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error getting lnk.bio user info: {str(e)}")
            return None

    def add_link(self, url: str, title: str = None, group_id: str = None, image_url: str = None) -> bool:
        """Add new link to lnk.bio profile
        
        Args:
            url: The URL to add to your lnk.bio profile
            title: The display title for the link (defaults to 'Latest Article')
            group_id: Optional group ID to organize the link
            image_url: Optional URL of an image to associate with the link
            
        Returns:
            bool: True if link was added successfully, False otherwise
        """
        try:
            if not self._ensure_valid_token():
                logger.error("Failed to get valid lnk.bio token")
                return False

            # Build form data (application/x-www-form-urlencoded)
            data = {
                'link': url,
                'title': title or 'Latest Article',
            }

            if group_id or self.group_id:
                data['group_id'] = group_id or self.group_id

            if image_url:
                data['image_url'] = image_url

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json',
                'User-Agent': 'lnk-bio-api-client/1.0'
                # Note: requests will automatically set Content-Type to 
                # application/x-www-form-urlencoded when using data parameter
            }

            response = requests.post(
                "https://lnk.bio/oauth/v1/lnk/add",
                headers=headers,
                data=data,  # This sends as form data (x-www-form-urlencoded)
                timeout=10
            )

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Added link to lnk.bio successfully: {url}")
                
                # Log the response data for debugging
                if result.get('data'):
                    link_id = result['data'].get('id')
                    link_url = result['data'].get('url')
                    logger.info(f"Created link ID: {link_id}, URL: {link_url}")
                
                return True
            else:
                logger.error(f"lnk.bio link creation failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"lnk.bio link creation failed: {str(e)}")
            return False