"""
API client for external partner integrations
"""


import os
from urllib.parse import quote
import requests


class PartnerAPIClient:
    """Client for partner API interactions"""
    
    def __init__(self, api_key=None, base_url=None, timeout=15):
        self.api_key = api_key
        self.base_url = (base_url or os.environ.get('SCANNER_API_URL', 'http://127.0.0.1:8000/api/v1')).rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
    
    def get_company_data(self, company_id):
        """Fetch company data from partner API"""
        if not company_id or not str(company_id).strip():
            raise ValueError('A company symbol is required')
        response = self.session.get(f'{self.base_url}/companies/{quote(str(company_id).strip().upper(), safe="")}/', timeout=self.timeout)
        response.raise_for_status()
        return response.json()
