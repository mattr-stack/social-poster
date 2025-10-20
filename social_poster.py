import os
import requests
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from PIL import Image
import io
import time

from linkbio_client import LinkBioClient
from twitter_client import TwitterClient
from google.cloud import storage

logger = logging.getLogger(__name__)

class SocialMediaPoster:
    """Handle posting to various social media platforms"""

    def __init__(self, facebook_access_token, facebook_page_id, twitter_client_id, twitter_client_secret, twitter_access_token, twitter_refresh_token, threads_access_token, threads_user_id, instagram_access_token, instagram_user_id, instagram_app_id, linkbio_client):
        self.facebook_token = facebook_access_token
        self.facebook_page_id = facebook_page_id
        self.twitter_client_id = twitter_client_id
        self.twitter_client_secret = twitter_client_secret
        self.twitter_access_token = twitter_access_token
        self.twitter_refresh_token = twitter_refresh_token
        self.threads_token = threads_access_token
        self.threads_user_id = threads_user_id
        self.instagram_token = instagram_access_token
        self.instagram_user_id = instagram_user_id
        self.instagram_app_id = instagram_app_id
        self.linkbio_client = linkbio_client

        self.twitter_client = TwitterClient(
            client_id=self.twitter_client_id, 
            client_secret=self.twitter_client_secret, 
            access_token=self.twitter_access_token, 
            refresh_token=self.twitter_refresh_token
        )
        self.FACEBOOK_API_VERSION = "v23.0"
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        logger.info(f"INSTAGRAM_USER_ID: {self.instagram_user_id}")



    def create_post_content(self, metadata: Dict[str, str], platform: str) -> str:
        """Generate platform-specific post content"""
        title = metadata.get('title', '')
        description = metadata.get('description', '')
        url = metadata.get('url', '')

        if platform == 'twitter':
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            keywords = metadata.get('keywords', [])
            hashtags = ' '.join([f"#{tag}" for tag in keywords])
            content = f"{title}\n\n{description[:100]}{'...' if len(description) > 100 else ''}\n\n{url}\n\n{hashtags}\n\n{timestamp}"
            return content[:270] + "..." if len(content) > 273 else content
        elif platform == 'facebook':
            keywords = metadata.get('keywords', [])
            hashtags = ' '.join([f"#{tag}" for tag in keywords])
            return f"{title}\n\n{description}\n\nRead more: {url}\n\n{hashtags}"
        if platform == 'instagram':
            keywords = metadata.get('keywords', [])
            hashtags = ' '.join([f"#{tag}" for tag in keywords]) if keywords else "#article #news #update #link"
            content = f"{title}\n\n{description[:150]}{'...' if len(description) > 150 else ''}\n\n{hashtags}"
            return content
        elif platform == 'threads':
            keywords = metadata.get('keywords', [])
            hashtags = ' '.join([f"#{tag}" for tag in keywords])
            return f"{title}\n\n{description}\n\n{url}\n\n{hashtags}"

        return f"{title}\n\n{description}\n\n{url}"

    def post_to_facebook(self, metadata: Dict[str, str]) -> bool:
        """Post to Facebook Page"""
        try:
            content = self.create_post_content(metadata, 'facebook')
            if self.dry_run:
                logger.info(f"[DRY RUN] Would have posted to Facebook with content: {content}")
                return True

            data = {
                'message': content,
                'access_token': self.facebook_token,
                'link': metadata.get('url')
            }
            response = requests.post(
                f"https://graph.facebook.com/{self.FACEBOOK_API_VERSION}/{self.facebook_page_id}/feed",
                data=data
            )
            response.raise_for_status()
            logger.info("Posted to Facebook successfully")
            return True
        except Exception as e:
            logger.error(f"Facebook posting failed: {str(e)}")
            return False



    def _resize_and_upload_for_instagram(self, image_url: str, unique_id: str) -> Optional[tuple[str, str]]:
        """Downloads, crops to 1:1, and uploads an image to GCS, returning the public URL and blob name."""
        try:
            logger.info(f"Downloading image for Instagram from {image_url}")
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            
            image = Image.open(io.BytesIO(response.content))

            # Center crop to 1:1 (square)
            width, height = image.size
            if width == height:
                cropped_image = image
                logger.info("Image is already square.")
            else:
                short_side = min(width, height)
                left = (width - short_side) / 2
                top = (height - short_side) / 2
                right = (width + short_side) / 2
                bottom = (height + short_side) / 2
                cropped_image = image.crop((left, top, right, bottom))
                logger.info(f"Cropped image to {cropped_image.size} pixels.")

            # Save cropped image to an in-memory buffer
            buffer = io.BytesIO()
            cropped_image.save(buffer, format='JPEG', quality=90)
            buffer.seek(0)

            # Upload to GCS
            bucket_name = os.getenv("GCS_BUCKET_NAME", "rr-transcriptions-pr-watcher")
            destination_blob_name = f"instagram-images/{unique_id}.jpg"
            
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)

            logger.info(f"Uploading resized image to GCS: gs://{bucket_name}/{destination_blob_name}")
            blob.upload_from_file(buffer, content_type='image/jpeg')

            # Make the blob publicly viewable
            blob.make_public()
            
            logger.info(f"Image successfully uploaded and made public at {blob.public_url}")
            return blob.public_url, destination_blob_name

        except Exception as e:
            logger.error(f"Failed to resize and upload image for Instagram: {str(e)}")
            return None, None

    def _delete_image_from_gcs(self, blob_name: str):
        """Deletes an image from Google Cloud Storage."""
        try:
            bucket_name = os.getenv("GCS_BUCKET_NAME", "rr-transcriptions-pr-watcher")
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            if blob.exists():
                logger.info(f"Deleting image from GCS: gs://{bucket_name}/{blob_name}")
                blob.delete()
                logger.info("Image deleted successfully.")
            else:
                logger.warning(f"Image not found in GCS, skipping deletion: gs://{bucket_name}/{blob_name}")

        except Exception as e:
            logger.error(f"Failed to delete image from GCS: {str(e)}")

    def post_to_instagram(self, metadata: Dict[str, str]) -> bool:
        """Post to Instagram (requires image)"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would have posted to Instagram with content: {self.create_post_content(metadata, 'instagram')}")
            return True

        original_image_url = metadata.get('image')
        if not original_image_url:
            logger.warning("Instagram post skipped - no image available")
            return False
        
        unique_id = "".join(filter(str.isalnum, metadata.get('url', '')))[-50:] or datetime.now().isoformat()

        processed_image_url, destination_blob_name = self._resize_and_upload_for_instagram(original_image_url, unique_id)
        if not processed_image_url:
            logger.error("Instagram post skipped - image processing failed.")
            return False

        content = self.create_post_content(metadata, 'instagram')

        cleanup_blob_name = destination_blob_name

        try:
            data = {
                'image_url': processed_image_url,
                'caption': content,
                'access_token': self.instagram_token,
                'app_id': self.instagram_app_id
            }
            upload_response = requests.post(
                f"https://graph.facebook.com/{self.FACEBOOK_API_VERSION}/{self.instagram_user_id}/media",
                data=data
            )
            upload_response.raise_for_status()
            container_id = upload_response.json()['id']
            logger.info(f"Instagram media container created with ID: {container_id}")

            publish_response = requests.post(
                f"https://graph.facebook.com/{self.FACEBOOK_API_VERSION}/{self.instagram_user_id}/media_publish",
                data={
                    'creation_id': container_id,
                    'access_token': self.instagram_token
                }
            )
            publish_response.raise_for_status()
            logger.info("Instagram publish command sent. Now verifying status...")

            for _ in range(10):
                time.sleep(3)
                status_response = requests.get(
                    f"https://graph.facebook.com/{self.FACEBOOK_API_VERSION}/{container_id}",
                    params={
                        'fields': 'status_code,status',
                        'access_token': self.instagram_token
                    }
                )
                status_data = status_response.json()
                status_code = status_data.get('status_code')
                logger.info(f"Current container status: {status_code}")

                if status_code in ['FINISHED', 'PUBLISHED']:
                    logger.info("Posted to Instagram successfully")
                    # Delete the image from GCS after successful post
                    self._delete_image_from_gcs(destination_blob_name)
                    cleanup_blob_name = None
                    return True
                elif status_code == 'ERROR':
                    logger.error(f"Instagram post failed after publishing. Status: {status_data.get('status')}")
                    return False

            logger.warning("Instagram post status check timed out.")
            return False

        except requests.exceptions.HTTPError as e:
            logger.error(f"Instagram posting failed with HTTP error: {e.response.status_code} {e.response.reason}")
            logger.error(f"Response body: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during Instagram posting: {str(e)}")
            return False
        finally:
            if cleanup_blob_name:
                self._delete_image_from_gcs(cleanup_blob_name)

    def post_to_twitter(self, metadata: Dict[str, str]) -> bool:
        """Post to Twitter/X using OAuth2"""
        try:
            content = self.create_post_content(metadata, 'twitter')
            if self.dry_run:
                logger.info(f"[DRY RUN] Would have tweeted: {content}")
                return True
            return self.twitter_client.create_tweet(content)
        except Exception as e:
            logger.error(f"Twitter posting failed: {str(e)}")
            return False

    def post_to_threads(self, metadata: Dict[str, str]) -> bool:
        """Post to Threads (if API access approved)"""
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would have posted to Threads with content: {self.create_post_content(metadata, 'threads')}")
                return True

            if not self.threads_token or not self.threads_user_id:
                logger.info("Threads posting skipped - credentials not configured")
                return False

            content = self.create_post_content(metadata, 'threads')
            container_response = requests.post(
                f"https://graph.threads.net/v23.0/{self.threads_user_id}/threads",
                params={
                    'access_token': self.threads_token
                },
                data={
                    'media_type': 'TEXT',
                    'text': content
                }
            )
            container_response.raise_for_status()
            container_id = container_response.json()['id']

            publish_response = requests.post(
                f"https://graph.threads.net/v23.0/{self.threads_user_id}/threads_publish",
                data={
                    'creation_id': container_id,
                    'access_token': self.threads_token
                }
            )
            publish_response.raise_for_status()
            logger.info("Posted to Threads successfully")
            return True

        except Exception as e:
            logger.error(f"Threads posting failed: {str(e)}")
            return False
