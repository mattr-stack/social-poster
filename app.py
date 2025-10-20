import os
import logging
from flask import Flask, request, jsonify
from datetime import datetime
import threading
from google.cloud import secretmanager
from metadata_extractor import MetadataExtractor
from airtable_client import AirtableClient
from social_poster import SocialMediaPoster
from linkbio_client import LinkBioClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

project_id = os.getenv("GCP_PROJECT")

def get_secret(secret_id):
    """Get a secret from Google Secret Manager"""
    if not project_id:
        logger.error("GCP_PROJECT environment variable not set.")
        return None
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"Failed to get secret {secret_id}: {str(e)}")
        return None

class SocialMediaAutomation:
    """Main automation class"""

    def __init__(self):
        self.metadata_extractor = MetadataExtractor()
        
        airtable_api_key = get_secret('AIRTABLE_PAT')
        airtable_base_id = get_secret('AIRTABLE_BASE_ID')
        airtable_table_name = get_secret('AIRTABLE_TABLE_NAME')

        self.airtable = AirtableClient(
            base_id=airtable_base_id,
            table_name=airtable_table_name,
            api_key=airtable_api_key
        )
        
        self.linkbio_client = LinkBioClient(
            client_id=get_secret('LINKBIO_CLIENT_ID'),
            client_secret=get_secret('LINKBIO_CLIENT_SECRET'),
            group_id=get_secret('LINKBIO_GROUP_ID')
        )

        self.social_poster = SocialMediaPoster(
            facebook_access_token=get_secret('FACEBOOK_ACCESS_TOKEN'),
            facebook_page_id=get_secret('FACEBOOK_PAGE_ID'),
            twitter_client_id=get_secret('TWITTER_CLIENT_ID'),
            twitter_client_secret=get_secret('TWITTER_CLIENT_SECRET'),
            twitter_access_token=get_secret('TWITTER_ACCESS_TOKEN'),
            twitter_refresh_token=get_secret('TWITTER_REFRESH_TOKEN'),
            threads_access_token=get_secret('THREADS_ACCESS_TOKEN'),
            threads_user_id=get_secret('THREADS_USER_ID'),
            instagram_access_token=get_secret('INSTAGRAM_ACCESS_TOKEN'),
            instagram_user_id=get_secret('INSTAGRAM_USER_ID'),
            instagram_app_id=get_secret('INSTAGRAM_APP_ID'),
            linkbio_client=self.linkbio_client
        )

    def process_record(self, record_id: str) -> dict[str, bool]:
        """Process a single Airtable record and post to social media"""
        logger.info(f"Starting to process record {record_id}")
        results = {
            'facebook': False,
            'instagram': False,
            'twitter': False,
            'threads': False,
            'linkbio': False
        }

        try:
            record = self.airtable.get_record(record_id)
            if not record:
                logger.error(f"Could not retrieve record {record_id}")
                return results

            fields = record.get('fields', {})
            article_url = fields.get('Article URL')
            status = fields.get('Status')

            if not status or status.upper() != 'LIVE' or not article_url:
                logger.info(f"Record {record_id} does not meet posting criteria - Status: {status}, Article URL: {article_url}")
                return results

            metadata = self.metadata_extractor.extract_metadata(article_url)
            logger.info(f"Extracted metadata: {metadata}")

            results['facebook'] = self.social_poster.post_to_facebook(metadata)
            results['instagram'] = self.social_poster.post_to_instagram(metadata)
            results['twitter'] = self.social_poster.post_to_twitter(metadata)
            results['threads'] = self.social_poster.post_to_threads(metadata)
            results['linkbio'] = self.linkbio_client.add_link(article_url, metadata.get('title'), image_url=metadata.get('image'))



            logger.info(f"Processed record {record_id}: {results}")
            return results

        except Exception as e:
            logger.error(f"Failed to process record {record_id}: {str(e)}")
            return results

import threading

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Airtable webhook or automation trigger"""
    try:
        data = request.get_json()
        logger.info(f"Received webhook data: {data}")

        record_id = data.get('recordId') or (data.get('records') and data['records'][0].get('id')) or data.get('id') or (data.get('record') and data['record'].get('id'))

        if not record_id:
            logger.error(f"No record ID found in webhook payload: {data}")
            return jsonify({'error': 'No record ID found in payload'}), 400

        logger.info(f"Processing record ID: {record_id} in background")

        automation = SocialMediaAutomation()
        thread = threading.Thread(target=automation.process_record, args=(record_id,))
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Request accepted for processing',
            'record_id': record_id
        }), 202

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

def main():
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
