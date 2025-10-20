import os
import requests
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AirtableClient:
    """Handle Airtable API operations"""

    def __init__(self, base_id: str, table_name: str, api_key: str):
        self.base_id = base_id
        self.table_name = table_name
        self.api_key = api_key
        self.base_url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def get_record(self, record_id: str) -> Optional[Dict]:
        """Get a specific record from Airtable"""
        try:
            response = requests.get(
                f"{self.base_url}/{record_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Airtable record {record_id}: {str(e)}")
            return None

    def update_record(self, record_id: str, fields: Dict) -> bool:
        """Update a record in Airtable"""
        try:
            data = {'fields': fields}
            response = requests.patch(
                f"{self.base_url}/{record_id}",
                headers=self.headers,
                data=json.dumps(data)
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to update Airtable record {record_id}: {str(e)}")
            return False
