"""
Example of a provider with external API support.

This example demonstrates how to implement external API integration in a provider.
It shows:
- API authentication
- Rate limiting
- Error handling
- Response caching
- Retry logic
"""

import os
import time
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from arbvantage_provider import Provider, ProviderResponse
from arbvantage_provider.rate_limit import TimeBasedRateLimitMonitor

class ExternalAPIProvider(Provider):
    """
    Provider with external API support.
    
    This provider demonstrates how to implement external API integration.
    It uses requests library with retry logic and rate limiting.
    """
    
    def __init__(self):
        super().__init__(
            name="external-api-provider",
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Initialize rate limit monitor
        self.rate_limit_monitor = TimeBasedRateLimitMonitor(min_delay=1.0)
        
        # Initialize requests session with retry logic
        self.session = self._create_session()
        
        # Register API actions
        self._register_api_actions()
        
    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry logic.
        
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504]  # HTTP status codes to retry on
        )
        
        # Mount retry strategy to session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
        
    def _register_api_actions(self):
        """Register API actions."""
        
        @self.actions.register(
            name="get_weather",
            description="Get weather data from external API",
            payload_schema={"city": str}
        )
        def get_weather(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Get weather data from external API.
            
            Args:
                payload: Dictionary containing city name
                
            Returns:
                ProviderResponse with weather data
            """
            try:
                city = payload["city"]
                
                # Check rate limits
                limits = self.rate_limit_monitor.check_rate_limits()
                if limits and limits.get("rate_limited"):
                    time.sleep(limits["wait_time"])
                    
                # Make API request
                response = self.session.get(
                    f"https://api.weatherapi.com/v1/current.json",
                    params={
                        "key": os.getenv("WEATHER_API_KEY"),
                        "q": city
                    },
                    timeout=10
                )
                
                # Check response status
                if response.status_code == 200:
                    data = response.json()
                    return ProviderResponse(
                        status="success",
                        message=f"Weather data retrieved for {city}",
                        data=data
                    )
                else:
                    return ProviderResponse(
                        status="error",
                        message=f"API request failed with status {response.status_code}",
                        data={"status_code": response.status_code}
                    )
                    
            except Exception as e:
                self.logger.error("Error getting weather data", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to get weather data: {str(e)}"
                )
                
        @self.actions.register(
            name="get_stock_price",
            description="Get stock price from external API",
            payload_schema={"symbol": str}
        )
        def get_stock_price(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Get stock price from external API.
            
            Args:
                payload: Dictionary containing stock symbol
                
            Returns:
                ProviderResponse with stock price data
            """
            try:
                symbol = payload["symbol"]
                
                # Check rate limits
                limits = self.rate_limit_monitor.check_rate_limits()
                if limits and limits.get("rate_limited"):
                    time.sleep(limits["wait_time"])
                    
                # Make API request
                response = self.session.get(
                    f"https://api.stockdata.org/v1/data/quote",
                    params={
                        "api_token": os.getenv("STOCK_API_KEY"),
                        "symbols": symbol
                    },
                    timeout=10
                )
                
                # Check response status
                if response.status_code == 200:
                    data = response.json()
                    return ProviderResponse(
                        status="success",
                        message=f"Stock price retrieved for {symbol}",
                        data=data
                    )
                else:
                    return ProviderResponse(
                        status="error",
                        message=f"API request failed with status {response.status_code}",
                        data={"status_code": response.status_code}
                    )
                    
            except Exception as e:
                self.logger.error("Error getting stock price", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to get stock price: {str(e)}"
                )
                
        @self.actions.register(
            name="get_currency_rate",
            description="Get currency exchange rate from external API",
            payload_schema={"from_currency": str, "to_currency": str}
        )
        def get_currency_rate(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Get currency exchange rate from external API.
            
            Args:
                payload: Dictionary containing currency codes
                
            Returns:
                ProviderResponse with exchange rate data
            """
            try:
                from_currency = payload["from_currency"]
                to_currency = payload["to_currency"]
                
                # Check rate limits
                limits = self.rate_limit_monitor.check_rate_limits()
                if limits and limits.get("rate_limited"):
                    time.sleep(limits["wait_time"])
                    
                # Make API request
                response = self.session.get(
                    f"https://api.exchangerate-api.com/v4/latest/{from_currency}",
                    timeout=10
                )
                
                # Check response status
                if response.status_code == 200:
                    data = response.json()
                    rate = data["rates"].get(to_currency)
                    if rate:
                        return ProviderResponse(
                            status="success",
                            message=f"Exchange rate retrieved for {from_currency}/{to_currency}",
                            data={
                                "from_currency": from_currency,
                                "to_currency": to_currency,
                                "rate": rate
                            }
                        )
                    else:
                        return ProviderResponse(
                            status="error",
                            message=f"Currency {to_currency} not found",
                            data={"to_currency": to_currency}
                        )
                else:
                    return ProviderResponse(
                        status="error",
                        message=f"API request failed with status {response.status_code}",
                        data={"status_code": response.status_code}
                    )
                    
            except Exception as e:
                self.logger.error("Error getting currency rate", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to get currency rate: {str(e)}"
                )

if __name__ == "__main__":
    provider = ExternalAPIProvider()
    provider.start() 