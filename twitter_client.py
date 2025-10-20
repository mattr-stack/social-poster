import os
import requests
import json
import logging
from datetime import datetime, timedelta
import base64

logger = logging.getLogger(__name__)

class TwitterClient:
    """Handle Twitter OAuth2 authentication and API calls"""

    def __init__(self, client_id, client_secret, access_token=None, refresh_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = None
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

    def get_access_token(self) -> str:
        """Get or refresh access token using OAuth2"""
        try:
            if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
                return self.access_token

            if self.refresh_token:
                return self._refresh_access_token()

            logger.error("No valid access token or refresh token available for Twitter")
            return None

        except Exception as e:
            logger.error(f"Error getting Twitter access token: {str(e)}")
            return None

    def _refresh_access_token(self) -> str:
        """Refresh access token using refresh token"""
        try:
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            token_data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }

            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.post(
                'https://api.twitter.com/2/oauth2/token',
                data=token_data,
                headers=headers
            )

            if response.status_code == 200:
                token_info = response.json()
                self.access_token = token_info['access_token']
                self.refresh_token = token_info.get('refresh_token', self.refresh_token)
                
                # Store the new tokens as environment variables for persistence
                os.environ['TWITTER_ACCESS_TOKEN'] = self.access_token
                if self.refresh_token:
                    os.environ['TWITTER_REFRESH_TOKEN'] = self.refresh_token

                expires_in = token_info.get('expires_in', 7200)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

                logger.info("Successfully refreshed Twitter access token")
                return self.access_token
            else:
                logger.error(f"Failed to refresh Twitter token: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error refreshing Twitter token: {str(e)}")
            return None

    def create_tweet(self, text: str) -> bool:
        """Create a tweet using OAuth2"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                logger.error("Failed to get Twitter access token")
                return False

            if self.dry_run:
                logger.info(f"[DRY RUN] Would have tweeted: {text}")
                return True

            tweet_data = {
                'text': text
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                'https://api.twitter.com/2/tweets',
                headers=headers,
                data=json.dumps(tweet_data)
            )

            if response.status_code == 201:
                logger.info("Successfully posted to Twitter")
                return True
            else:
                logger.error(f"Twitter posting failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Twitter posting failed: {str(e)}")
            return False
