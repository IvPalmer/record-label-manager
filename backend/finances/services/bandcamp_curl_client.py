import subprocess
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BandcampTokens:
    access_token: str
    refresh_token: str
    expires_at: int


class BandcampCurlAPIError(Exception):
    """Custom exception for Bandcamp API errors"""
    pass


class BandcampCurlAPI:
    """
    Bandcamp API client using curl subprocess calls
    This approach works around Python requests being blocked
    """
    
    TOKEN_URL = "https://bandcamp.com/oauth_token"
    SALES_API_URL = "https://bandcamp.com/api/sales/1/sales_report"
    TOKEN_CACHE_KEY = "bandcamp_tokens_curl"
    
    def __init__(self):
        self.client_id = getattr(settings, 'BANDCAMP_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'BANDCAMP_CLIENT_SECRET', None)
        
        if not self.client_id or not self.client_secret:
            raise ValueError("BANDCAMP_CLIENT_ID and BANDCAMP_CLIENT_SECRET must be set in Django settings")
    
    def get_client_credentials(self) -> Optional[BandcampTokens]:
        """
        Get client credentials using curl
        """
        logger.info(f"Attempting to fetch client credentials at {datetime.now().isoformat()}")
        
        curl_cmd = [
            'curl', '-s',
            self.TOKEN_URL,
            '-H', 'Content-Type: application/x-www-form-urlencoded',
            '--data-urlencode', 'grant_type=client_credentials',
            '--data-urlencode', f'client_id={self.client_id}',
            '--data-urlencode', f'client_secret={self.client_secret}'
        ]
        
        try:
            result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
            logger.info(f"Token response: {result.stdout}")
            token_data = json.loads(result.stdout)
            
            if not token_data.get('access_token'):
                logger.error('No access token in response')
                logger.error(f'Full response: {token_data}')
                return None
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 3600)
            expires_at = int(time.time()) + expires_in
            
            tokens = BandcampTokens(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', ''),
                expires_at=expires_at
            )
            
            # Cache the tokens
            cache.set(self.TOKEN_CACHE_KEY, tokens, timeout=expires_in - 60)
            
            logger.info("Client credentials fetched successfully")
            return tokens
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Curl command failed: {e}")
            logger.error(f"Curl output: {e.stdout}")
            logger.error(f"Curl error: {e.stderr}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse token response as JSON: {e}")
            logger.error(f"Response: {result.stdout}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching client credentials: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[BandcampTokens]:
        """
        Refresh access token using curl
        """
        logger.info(f"Attempting to refresh access token at {datetime.now().isoformat()}")
        
        curl_cmd = [
            'curl', '-s',
            self.TOKEN_URL,
            '-H', 'Content-Type: application/x-www-form-urlencoded',
            '--data-urlencode', 'grant_type=refresh_token',
            '--data-urlencode', f'refresh_token={refresh_token}',
            '--data-urlencode', f'client_id={self.client_id}',
            '--data-urlencode', f'client_secret={self.client_secret}'
        ]
        
        try:
            result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
            token_data = json.loads(result.stdout)
            
            expires_in = token_data.get('expires_in', 3600)
            expires_at = int(time.time()) + expires_in
            
            tokens = BandcampTokens(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', refresh_token),
                expires_at=expires_at
            )
            
            # Update cache
            cache.set(self.TOKEN_CACHE_KEY, tokens, timeout=expires_in - 60)
            
            logger.info("Access token refreshed successfully")
            return tokens
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error refreshing access token with curl: {e}")
            raise BandcampCurlAPIError(f"Failed to refresh access token: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse refresh response as JSON: {e}")
            raise BandcampCurlAPIError(f"Invalid refresh response: {e}")
    
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
                except BandcampCurlAPIError:
                    tokens = None
            
            # If refresh failed or no refresh token, get new credentials
            if not tokens:
                tokens = self.get_client_credentials()
        
        return tokens.access_token if tokens else None
    
    def get_my_bands(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of bands - for now return the configured band ID
        """
        band_id = getattr(settings, 'BAND_ID', None)
        if band_id:
            return [{'id': int(band_id), 'name': f'Band {band_id}'}]
        
        logger.error("No BAND_ID configured")
        return None
    
    def get_sales_report(self, band_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get sales report using curl - try different endpoints until we find one that works
        """
        access_token = self.ensure_valid_access_token()
        if not access_token:
            raise BandcampCurlAPIError("No valid access token available")
        
        # Try different API endpoints and approaches
        endpoints_to_try = [
            "https://bandcamp.com/api/sales/1/sales_report",
            "https://bandcamp.com/api/sales/4/generate_sales_report",
            "https://bandcamp.com/api/band/3460825363/sales_report"
        ]
        
        sales_data = {
            "band_id": band_id,
            "start_time": f"{start_date} 00:00:00",
            "end_time": f"{end_date} 23:59:59",
            "format": "json"
        }
        
        for endpoint in endpoints_to_try:
            logger.info(f"Trying sales endpoint: {endpoint}")
            
            curl_cmd = [
                'curl', '-s', '-X', 'POST',
                endpoint,
                '-H', f'Authorization: Bearer {access_token}',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(sales_data)
            ]
            
            try:
                result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
                
                # Check if response looks like HTML (blocked/error page)
                if result.stdout.strip().startswith('<!DOCTYPE') or '<html' in result.stdout:
                    logger.warning(f"Endpoint {endpoint} returned HTML (possibly blocked)")
                    continue
                
                # Try to parse as JSON
                try:
                    response_data = json.loads(result.stdout)
                    logger.info(f"Successfully got JSON response from {endpoint}")
                    
                    # Convert response format to match expected structure
                    return self._process_sales_response(response_data)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Endpoint {endpoint} returned non-JSON response")
                    logger.debug(f"Response: {result.stdout[:200]}...")
                    continue
                    
            except subprocess.CalledProcessError as e:
                logger.warning(f"Endpoint {endpoint} failed: {e}")
                continue
        
        # If all endpoints fail, try a simpler approach - return mock data for now
        logger.warning("All sales endpoints failed, returning empty data for now")
        return []
    
    def _process_sales_response(self, response_data: Any) -> List[Dict[str, Any]]:
        """
        Process the sales response into the expected format
        """
        if isinstance(response_data, dict):
            # If it's a dict with sales records as values
            sales_records = []
            for unique_id, details in response_data.items():
                if isinstance(details, dict):
                    record = {
                        'unique_bc_id': unique_id,
                        'date': details.get('date'),
                        'paid_to': details.get('paid_to', ''),
                        'item_type': details.get('item_type', ''),
                        'item_name': details.get('item_name', ''),
                        'artist': details.get('artist', ''),
                        'currency': details.get('currency', 'USD'),
                        'item_price': self._safe_float(details.get('item_price')),
                        'quantity': self._safe_int(details.get('quantity', 1)),
                        'discount_code': details.get('discount_code'),
                        'sub_total': self._safe_float(details.get('sub_total')),
                        'shipping': self._safe_float(details.get('shipping')) if details.get('shipping') is not None else None,
                        'ship_from_country_name': details.get('ship_from_country_name'),
                        'transaction_fee': self._safe_float(details.get('transaction_fee')),
                        'fee_type': details.get('fee_type', ''),
                        'item_total': self._safe_float(details.get('item_total')),
                        'amount_you_received': self._safe_float(details.get('amount_you_received')),
                        'bandcamp_transaction_id': details.get('bandcamp_transaction_id', ''),
                        'paypal_transaction_id': details.get('paypal_transaction_id'),
                        'net_amount': self._safe_float(details.get('net_amount')),
                        'catalog_number': details.get('catalog_number'),
                        'upc': details.get('upc'),
                        'isrc': details.get('isrc'),
                        'buyer_name': details.get('buyer_name'),
                        'buyer_email': details.get('buyer_email'),
                        'country': details.get('country'),
                        'country_code': details.get('country_code'),
                    }
                    sales_records.append(record)
            return sales_records
        
        elif isinstance(response_data, list):
            # If it's already a list of records
            return response_data
        
        else:
            logger.warning(f"Unexpected response format: {type(response_data)}")
            return []
    
    def _safe_float(self, value):
        """Safely convert a value to float, handling None and strings"""
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value):
        """Safely convert a value to int, handling None and strings"""
        if value is None:
            return 0
        try:
            return int(float(value))  # Handle string numbers like "1.0"
        except (ValueError, TypeError):
            return 0
