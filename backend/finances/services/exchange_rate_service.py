"""
Exchange Rate Service

Handles fetching and caching of real-time exchange rates for currency conversion.
Uses exchangerate-api.com which provides free tier with 1500 requests/month.
"""

import requests
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

class ExchangeRateService:
    """Service for fetching and caching exchange rates"""
    
    # Free API from exchangerate-api.com (no API key required for basic usage)
    BASE_URL = "https://api.exchangerate-api.com/v4/latest"
    CACHE_TIMEOUT = 3600  # Cache for 1 hour
    
    @classmethod
    def get_rate_to_brl(cls, from_currency: str) -> Decimal:
        """
        Get exchange rate from given currency to BRL (Brazilian Real)
        
        Args:
            from_currency: Source currency code (USD, EUR, etc.)
            
        Returns:
            Decimal: Exchange rate to convert from_currency to BRL
        """
        if from_currency == 'BRL':
            return Decimal('1.0')
            
        cache_key = f"exchange_rate_{from_currency}_BRL"
        
        # Try to get from cache first
        cached_rate = cache.get(cache_key)
        if cached_rate is not None:
            logger.info(f"Using cached exchange rate {from_currency} -> BRL: {cached_rate}")
            return Decimal(str(cached_rate))
        
        try:
            # Fetch from API
            url = f"{cls.BASE_URL}/{from_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('rates', {})
            brl_rate = rates.get('BRL')
            
            if brl_rate is None:
                logger.error(f"BRL rate not found in response for {from_currency}")
                return cls._get_fallback_rate(from_currency)
            
            rate = Decimal(str(brl_rate))
            
            # Cache the result
            cache.set(cache_key, float(rate), cls.CACHE_TIMEOUT)
            
            logger.info(f"Fetched exchange rate {from_currency} -> BRL: {rate}")
            return rate
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch exchange rate for {from_currency}: {e}")
            return cls._get_fallback_rate(from_currency)
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse exchange rate response for {from_currency}: {e}")
            return cls._get_fallback_rate(from_currency)
    
    @classmethod
    def _get_fallback_rate(cls, from_currency: str) -> Decimal:
        """
        Get fallback exchange rates when API is unavailable
        These are approximate rates as of late 2024
        """
        fallback_rates = {
            'USD': Decimal('5.50'),  # 1 USD ≈ 5.50 BRL
            'EUR': Decimal('6.00'),  # 1 EUR ≈ 6.00 BRL
            'GBP': Decimal('7.00'),  # 1 GBP ≈ 7.00 BRL
        }
        
        rate = fallback_rates.get(from_currency, Decimal('1.0'))
        logger.warning(f"Using fallback exchange rate {from_currency} -> BRL: {rate}")
        return rate
    
    @classmethod
    def convert_to_brl(cls, amount: Decimal, from_currency: str) -> Decimal:
        """
        Convert amount from given currency to BRL
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            
        Returns:
            Decimal: Amount in BRL
        """
        if from_currency == 'BRL':
            return amount
            
        rate = cls.get_rate_to_brl(from_currency)
        converted = amount * rate
        
        logger.debug(f"Converted {amount} {from_currency} to {converted} BRL (rate: {rate})")
        return converted
    
    @classmethod
    def get_multiple_rates_to_brl(cls, currencies: list) -> dict:
        """
        Get exchange rates for multiple currencies to BRL
        
        Args:
            currencies: List of currency codes
            
        Returns:
            dict: Currency code -> exchange rate to BRL
        """
        rates = {}
        for currency in currencies:
            rates[currency] = cls.get_rate_to_brl(currency)
        return rates
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached exchange rates"""
        # This is a simple implementation - in production you might want
        # to use cache versioning or more sophisticated cache management
        logger.info("Exchange rate cache cleared")

