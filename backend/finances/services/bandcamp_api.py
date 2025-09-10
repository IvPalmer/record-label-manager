import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
from django.conf import settings
from django.core.cache import cache
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BandcampTokens:
    access_token: str
    refresh_token: str
    expires_at: int


class BandcampAPIError(Exception):
    """Custom exception for Bandcamp API errors"""
    pass


class BandcampAPI:
    """
    Python implementation of Bandcamp API client
    Based on the Node.js implementation from label-manager-server
    """
    
    BASE_URL = "https://bandcamp.com"
    TOKEN_URL = "https://bandcamp.com/oauth_token"
    SALES_API_URL = "https://bandcamp.com/api/sales/1/sales_report"
    TOKEN_CACHE_KEY = "bandcamp_tokens"
    
    def __init__(self):
        self.client_id = getattr(settings, 'BANDCAMP_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'BANDCAMP_CLIENT_SECRET', None)
        
        if not self.client_id or not self.client_secret:
            raise ValueError("BANDCAMP_CLIENT_ID and BANDCAMP_CLIENT_SECRET must be set in Django settings")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'curl/8.7.1',
            'Accept': '*/*'
        })
    
    def get_client_credentials(self) -> Optional[BandcampTokens]:
        """
        Get client credentials (OAuth2 client credentials flow)
        """
        logger.info(f"Attempting to fetch client credentials at {datetime.now().isoformat()}")
        
        try:
            # Use form data for OAuth request with proper URL encoding
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            # URL encode the data manually to ensure proper encoding of special characters
            encoded_data = urlencode(data)
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            logger.info(f"Requesting token from {self.TOKEN_URL} with client_id: {self.client_id}")
            response = self.session.post(self.TOKEN_URL, data=encoded_data, headers=headers)
            
            logger.info(f"Token response status: {response.status_code}")
            logger.info(f"Token response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.error(f"Token request failed with status {response.status_code}: {response.text}")
            
            response.raise_for_status()
            
            token_data = response.json()
            
            if not token_data.get('access_token'):
                logger.error('No access token in response')
                return None
            
            # Calculate expiration time (30 minutes as in Node.js version)
            expires_in = token_data.get('expires_in', 1800)  # 30 minutes default
            expires_at = int(time.time()) + expires_in
            
            tokens = BandcampTokens(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', ''),
                expires_at=expires_at
            )
            
            # Cache the tokens
            cache.set(self.TOKEN_CACHE_KEY, tokens, timeout=expires_in - 60)  # Cache for slightly less time
            
            logger.info("Client credentials fetched successfully")
            return tokens
            
        except requests.RequestException as e:
            logger.error(f"Error fetching client credentials: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching client credentials: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[BandcampTokens]:
        """
        Refresh access token using refresh token
        """
        logger.info(f"Attempting to refresh access token at {datetime.now().isoformat()}")
        
        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            # URL encode the data
            encoded_data = urlencode(data)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            response = self.session.post(self.TOKEN_URL, data=encoded_data, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            
            expires_in = token_data.get('expires_in', 1800)
            expires_at = int(time.time()) + expires_in
            
            tokens = BandcampTokens(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', refresh_token),  # Keep old refresh token if not provided
                expires_at=expires_at
            )
            
            # Update cache
            cache.set(self.TOKEN_CACHE_KEY, tokens, timeout=expires_in - 60)
            
            logger.info("Access token refreshed successfully")
            return tokens
            
        except requests.RequestException as e:
            logger.error(f"Error refreshing access token: {e}")
            raise BandcampAPIError(f"Failed to refresh access token: {e}")
    
    def is_token_expired(self, tokens: BandcampTokens) -> bool:
        """Check if access token is expired"""
        return time.time() >= tokens.expires_at
    
    def ensure_valid_access_token(self) -> Optional[str]:
        """
        Ensure we have a valid access token, refreshing if necessary
        """
        # Try to get cached tokens
        tokens = cache.get(self.TOKEN_CACHE_KEY)
        
        # If no cached tokens or expired, get new credentials
        if not tokens or self.is_token_expired(tokens):
            if tokens and tokens.refresh_token:
                # Try to refresh
                try:
                    tokens = self.refresh_access_token(tokens.refresh_token)
                except BandcampAPIError:
                    tokens = None
            
            # If refresh failed or no refresh token, get new credentials
            if not tokens:
                tokens = self.get_client_credentials()
        
        return tokens.access_token if tokens else None
    
    def get_my_bands(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of bands associated with the authenticated account
        For this implementation, we'll return the band ID provided in settings
        """
        # Since we have the band ID directly, return it as a band list
        # In a full implementation, this would call the Bandcamp API to get all bands
        band_id = getattr(settings, 'BAND_ID', None)
        if band_id:
            return [{'id': int(band_id), 'name': f'Band {band_id}'}]
        
        logger.error("No BAND_ID configured")
        return None
    
    def get_sales_report(self, band_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get sales report for a specific band and date range
        Fetches data in yearly chunks to avoid API limits
        """
        access_token = self.ensure_valid_access_token()
        if not access_token:
            raise BandcampAPIError("No valid access token available")
        
        return self._fetch_sales_reports_in_chunks(band_id, start_date, end_date, access_token)
    
    def _fetch_sales_reports_in_chunks(self, band_id: int, start_date: str, end_date: str, 
                                     access_token: str) -> List[Dict[str, Any]]:
        """
        Fetch sales reports in yearly chunks to avoid API limitations
        """
        one_year_ms = 365 * 24 * 60 * 60 * 1000  # One year in milliseconds
        start_time = int(datetime.fromisoformat(start_date).timestamp() * 1000)
        end_time = int(datetime.fromisoformat(end_date).timestamp() * 1000)
        current_time = start_time
        sales_reports = []
        
        while current_time < end_time:
            next_time = min(current_time + one_year_ms, end_time)
            current_start = datetime.fromtimestamp(current_time / 1000).strftime('%Y-%m-%d')
            current_end = datetime.fromtimestamp(next_time / 1000).strftime('%Y-%m-%d')
            
            try:
                chunk_data = self._fetch_sales_report_chunk(
                    band_id, current_start, current_end, access_token
                )
                if chunk_data:
                    sales_reports.extend(chunk_data)
                    
            except Exception as e:
                logger.error(f"Error fetching sales report chunk from {current_start} to {current_end}: {e}")
            
            current_time = next_time
        
        return sales_reports
    
    def _fetch_sales_report_chunk(self, band_id: int, start_date: str, end_date: str, 
                                access_token: str) -> List[Dict[str, Any]]:
        """
        Fetch a single chunk of sales report data
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            payload = {
                'band_id': band_id,
                'start_time': f"{start_date} 00:00:00",
                'end_time': f"{end_date} 23:59:59",
                'format': 'json'
            }
            
            response = self.session.post(self.SALES_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            report_data = response.json()
            
            # Convert the response format to match the expected structure
            if isinstance(report_data, dict):
                sales_report_array = []
                for unique_id, details in report_data.items():
                    sale_record = {
                        'unique_bc_id': unique_id,
                        'date': details.get('date'),
                        'paid_to': details.get('paid_to', ''),
                        'item_type': details.get('item_type', ''),
                        'item_name': details.get('item_name', ''),
                        'artist': details.get('artist', ''),
                        'currency': details.get('currency', 'USD'),
                        'item_price': float(details.get('item_price', 0)),
                        'quantity': int(details.get('quantity', 1)),
                        'discount_code': details.get('discount_code'),
                        'sub_total': float(details.get('sub_total', 0)),
                        'shipping': float(details.get('shipping', 0)) if details.get('shipping') else None,
                        'ship_from_country_name': details.get('ship_from_country_name'),
                        'transaction_fee': float(details.get('transaction_fee', 0)),
                        'fee_type': details.get('fee_type', ''),
                        'item_total': float(details.get('item_total', 0)),
                        'amount_you_received': float(details.get('amount_you_received', 0)),
                        'bandcamp_transaction_id': details.get('bandcamp_transaction_id', ''),
                        'paypal_transaction_id': details.get('paypal_transaction_id'),
                        'net_amount': float(details.get('net_amount', 0)),
                        'package': details.get('package'),
                        'option': details.get('option'),
                        'item_url': details.get('item_url'),
                        'catalog_number': details.get('catalog_number'),
                        'upc': details.get('upc'),
                        'isrc': details.get('isrc'),
                        'buyer_name': details.get('buyer_name'),
                        'buyer_email': details.get('buyer_email'),
                        'buyer_phone': details.get('buyer_phone'),
                        'buyer_note': details.get('buyer_note'),
                        'ship_to_name': details.get('ship_to_name'),
                        'ship_to_street': details.get('ship_to_street'),
                        'ship_to_street_2': details.get('ship_to_street_2'),
                        'ship_to_city': details.get('ship_to_city'),
                        'ship_to_state': details.get('ship_to_state'),
                        'ship_to_zip': details.get('ship_to_zip'),
                        'ship_to_country': details.get('ship_to_country'),
                        'ship_to_country_code': details.get('ship_to_country_code'),
                        'ship_date': details.get('ship_date'),
                        'ship_notes': details.get('ship_notes'),
                        'country': details.get('country'),
                        'country_code': details.get('country_code'),
                        'region_or_state': details.get('region_or_state'),
                        'city': details.get('city'),
                        'referer': details.get('referer'),
                        'referer_url': details.get('referer_url'),
                        'sku': details.get('sku'),
                        'seller_tax': float(details.get('seller_tax', 0)) if details.get('seller_tax') else None,
                        'marketplace_tax': float(details.get('marketplace_tax', 0)) if details.get('marketplace_tax') else None,
                    }
                    sales_report_array.append(sale_record)
                
                return sales_report_array
            
            return []
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise BandcampAPIError(f"Failed to fetch sales report: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise BandcampAPIError(f"Unexpected error fetching sales report: {e}")
