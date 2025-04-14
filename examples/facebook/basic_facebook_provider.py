"""
Basic Facebook Provider Example

This example demonstrates the basic usage of the Facebook provider.
It shows how to:
1. Initialize the Facebook provider
2. Register basic actions
3. Handle authentication
4. Use rate limiting with FacebookAdsApi.get_usage()
5. Use structured logging with ProviderLogger
6. Use built-in rate limit monitor support

Configuration Environment Variables:
    PROVIDER_NAME: Custom name for the provider instance (default: "basic-facebook")
    PROVIDER_AUTH_TOKEN: Authentication token for the provider
    HUB_GRPC_URL: URL for the gRPC hub connection (default: "hub-grpc:50051")

Dependencies:
    - arbvantage_provider: Core provider functionality
    - facebook_business: Official Facebook Business SDK
    - logging: Python standard logging
    - typing: Type hints support
"""

from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import AdvancedRateLimitMonitor
from arbvantage_provider.schemas import ProviderResponse
from arbvantage_provider.logger import ProviderLogger
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.adaccount import AdAccount
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .actions import get_business_info, get_page_insights

# Configure logging with detailed format
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FacebookRateLimitMonitor(AdvancedRateLimitMonitor):
    """
    Facebook-specific rate limit monitor that uses FacebookAdsApi.get_usage()
    
    This monitor implements Facebook-specific rate limiting logic by:
    - Tracking API usage through FacebookAdsApi.get_usage()
    - Monitoring call counts and CPU time usage
    - Providing wait times when limits are approached
    - Logging rate limit metrics for monitoring
    
    Attributes:
        access_token (str): Facebook API access token for making requests
        logger (ProviderLogger): Structured logger for rate limit events
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the Facebook rate limit monitor.
        
        Args:
            **kwargs: Configuration parameters inherited from AdvancedRateLimitMonitor:
                min_delay (float): Minimum delay between requests
                max_calls_per_second (int): Maximum allowed API calls per second
                warning_threshold (float): Threshold for warning alerts (0.0-1.0)
                critical_threshold (float): Threshold for critical alerts (0.0-1.0)
        """
        super().__init__(**kwargs)
        self.access_token = None
        self.logger = ProviderLogger("facebook-rate-limit")
        
    def set_access_token(self, access_token: str) -> None:
        """
        Set the access token for API calls.
        
        Args:
            access_token (str): Valid Facebook API access token with required permissions
        """
        self.access_token = access_token
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """
        Check Facebook API usage limits using get_usage()
        
        This method:
        1. Initializes the Facebook API if needed
        2. Retrieves current usage statistics
        3. Logs usage metrics for monitoring
        4. Returns rate limit response if limits are exceeded
        
        Returns:
            Optional[Dict[str, Any]]: ProviderResponse with status "limit" if limits 
            are exceeded, None if no limits are exceeded
            
        Response Data Structure:
            {
                "wait_time": int,        # Seconds to wait before next request
                "calls_made": int,       # Number of API calls made
                "total_calls": int,      # Total allowed API calls
                "time_remaining": int    # Time until limits reset
            }
        """
        if not self.access_token:
            self.logger.warning("Access token not set")
            return None
            
        try:
            # Initialize API if not already initialized
            if not FacebookAdsApi.get_default_api():
                FacebookAdsApi.init(access_token=self.access_token)
            
            # Get usage statistics
            usage = FacebookAdsApi.get_default_api().get_usage()
            
            # Extract rate limit information
            calls_made = usage.get('call_count', 0)
            total_calls = usage.get('total_cputime', 0)
            time_remaining = usage.get('estimated_time_to_regain_access', 0)
            
            # Log rate limit metrics for monitoring
            self.logger.log_metric("calls_made", calls_made)
            self.logger.log_metric("total_calls", total_calls)
            self.logger.log_metric("time_remaining", time_remaining)
            
            if time_remaining > 0:
                self.logger.warning(
                    "Rate limit exceeded",
                    calls_made=calls_made,
                    total_calls=total_calls,
                    time_remaining=time_remaining
                )
                return ProviderResponse(
                    status="limit",
                    message=f"Rate limit exceeded. Please wait {time_remaining} seconds",
                    data={
                        "wait_time": time_remaining,
                        "calls_made": calls_made,
                        "total_calls": total_calls,
                        "time_remaining": time_remaining
                    }
                ).model_dump()
            
            return None
            
        except Exception as e:
            self.logger.exception(
                "Error checking Facebook API limits",
                error=str(e)
            )
            return ProviderResponse(
                status="error",
                message="Error checking rate limits",
                data={"error": str(e)}
            ).model_dump()

class BasicFacebookProvider(Provider):
    """
    Basic Facebook provider example.
    
    This provider implements core Facebook API integration features:
    - Secure authentication handling
    - Action registration and execution
    - Rate limit monitoring and protection
    - Structured logging
    - Error handling
    
    Supported Actions:
        get_business_info: Retrieve basic business account information
        get_page_insights: Get page performance metrics with retry logic
        
    Configuration:
        name (str): Provider instance name
        auth_token (str): Provider authentication token
        hub_url (str): gRPC hub connection URL
        rate_limit_monitor (FacebookRateLimitMonitor): Rate limit monitoring configuration
    """
    
    def __init__(self):
        """
        Initialize the basic Facebook provider.
        
        Sets up:
        - Rate limit monitoring with configurable thresholds
        - Provider authentication and connection settings
        - Structured logging
        - Action registration
        """
        # Initialize rate limit monitor with default settings
        rate_limit_monitor = FacebookRateLimitMonitor(
            min_delay=1.0,              # Minimum seconds between requests
            max_calls_per_second=2,     # Maximum API calls per second
            warning_threshold=0.8,      # 80% of limit triggers warning
            critical_threshold=0.9      # 90% of limit triggers critical alert
        )
        
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "basic-facebook"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051"),
            rate_limit_monitor=rate_limit_monitor
        )
        
        # Initialize provider logger with detailed format
        self.logger = ProviderLogger(
            name="basic-facebook-provider",
            log_file="facebook_provider.log",
            log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(context)s"
        )
        
        # Register provider actions with schema validation
        self.actions.register(
            name="get_business_info",
            description="Get basic business information including name, ID, and status",
            payload_schema={},  # No additional payload required
            account_schema={
                "business_id": str,    # Facebook Business ID
                "access_token": str    # Valid access token with business permissions
            }
        )(get_business_info)
        
        self.actions.register(
            name="get_page_insights",
            description="Get page insights with automatic retry logic for temporary failures",
            payload_schema={
                "page_id": str,      # Facebook Page ID
                "metric": str,        # Insight metric name (e.g., "page_impressions")
                "period": str        # Time period for metrics (e.g., "day", "week")
            },
            account_schema={
                "business_id": str,   # Facebook Business ID
                "access_token": str   # Valid access token with page insights permissions
            }
        )(get_page_insights)
                    
    def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action with rate limit monitoring and error handling.
        
        This method:
        1. Updates rate limit monitor with current access token
        2. Executes the requested action with rate limit protection
        3. Handles any execution errors
        
        Args:
            action_name (str): Name of the registered action to execute
            payload (Dict[str, Any]): Action parameters including account credentials
            
        Returns:
            Dict[str, Any]: Action execution result or error response
            
        Raises:
            Any exceptions from action execution are logged and returned as error responses
        """
        # Update access token in rate limit monitor
        if "account" in payload and "access_token" in payload["account"]:
            self.rate_limit_monitor.set_access_token(payload["account"]["access_token"])
            
        return super().execute_action(action_name, payload)

if __name__ == "__main__":
    """
    Entry point for running the provider as a standalone service.
    
    Initializes and starts the Facebook provider service with:
    - Environment-based configuration
    - Rate limit protection
    - Action registration
    - Error handling
    """
    provider = BasicFacebookProvider()
    provider.start()