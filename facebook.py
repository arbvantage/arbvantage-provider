"""
Facebook Provider Implementation

This module implements the Facebook provider for the ARB platform.
It provides functionality to interact with Facebook's Business API and retrieve various types of data
including business accounts, pages, and their associated details.

The provider is designed to work with the ARB platform's provider interface and handles:
- Authentication with Facebook API
- Registration of available actions
- Execution of registered actions
- Error handling and response formatting
- Rate limiting and monitoring
- Logging and debugging

Environment Variables:
    PROVIDER_NAME: Name of the provider (default: "facebook")
    PROVIDER_AUTH_TOKEN: Authentication token for the provider
    HUB_GRPC_URL: URL of the hub gRPC service
    TASK_EXECUTION_TIMEOUT: Maximum time in seconds for task execution

Rate Limiting Configuration:
    min_delay: Minimum seconds between API requests (default: 1.0)
    max_calls_per_second: Maximum API calls per second (default: 2)
    warning_threshold: Percentage of rate limit that triggers warning (default: 0.5)
    critical_threshold: Percentage of rate limit that triggers critical alert (default: 0.7)
"""

from arbvantage_provider import Provider
import os
from typing import Dict, Any, Optional
from actions import (
    init_offers,
    create_campaign,
    sync_metrics,
    check_status
)
from rate_limit import FacebookRateLimitMonitor
from arbvantage_provider.logger import ProviderLogger

class FacebookProvider(Provider):
    """
    Facebook Provider Class
    
    This class implements the Facebook provider interface for the ARB platform.
    It handles the initialization of the Facebook API client and registration of available actions.
    
    The provider implements rate limiting, error handling, and logging to ensure reliable
    operation when interacting with Facebook's Business API.
    """
    
    def __init__(self):
        """
        Initialize the Facebook Provider
        
        Sets up the provider with configuration from environment variables and registers
        all available actions that can be executed through this provider.
        """
        # Initialize rate limit monitor with default settings
        rate_limit_monitor = FacebookRateLimitMonitor(
            min_delay=1.0,              # Minimum seconds between requests
            max_calls_per_second=2,     # Maximum API calls per second
            warning_threshold=0.5,      # 50% of limit triggers warning
            critical_threshold=0.7      # 70% of limit triggers critical alert
        )        

        # Init provider
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "facebook"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN", "fb_aibeika3iec3ohnga4she"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051"),
            rate_limit_monitor=rate_limit_monitor
        )

        # Init provider logger with detailed format
        self.logger = ProviderLogger(
            name=f"{self.name}-provider",
            log_file=f"{self.name}-provider.log",
            log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(context)s"
        )        

        # Register INIT_OFFERS action
        self.actions.register(
            name="init_offers",
            description="Initialize offers for a business account",
            payload_schema={},  # No payload required for initialization
            account_schema={
                "business_id": str,      # Facebook Business Manager ID
                "access_token": str,     # Facebook API access token
                "app_id": str,           # Facebook App ID
                "app_secret": str        # Facebook App Secret
            }
        )(init_offers)

        # Register CREATE_CAMPAIGN action
        self.actions.register(
            name="create_campaign",
            description="Create a new advertising campaign for a business",
            payload_schema={
                "campaign": dict,        # Campaign configuration details
                "current": dict          # Current state information
            },
            account_schema={
                "business_id": str,      # Facebook Business Manager ID
                "access_token": str,     # Facebook API access token
                "app_id": str,           # Facebook App ID
                "app_secret": str,       # Facebook App Secret
                "pixel_id": str,         # Facebook Pixel ID for tracking
                "pixel_token": str       # Facebook Pixel access token
            }
        )(create_campaign)

        # Register CHECK_STATUS action
        self.actions.register(
            name="check_status",
            description="Check the current status of a campaign",
            payload_schema={
                "campaign": dict,        # Campaign details to check
                "current": dict          # Current state information
            },
            account_schema={
                "business_id": str,      # Facebook Business Manager ID
                "access_token": str,     # Facebook API access token
                "app_id": str,           # Facebook App ID
                "app_secret": str,       # Facebook App Secret
                "pixel_id": str,         # Facebook Pixel ID for tracking
                "pixel_token": str       # Facebook Pixel access token
            }
        )(check_status)        

        # Register SYNC_METRICS action
        self.actions.register(
            name="sync_metrics",
            description="Synchronize campaign metrics with Facebook API",
            payload_schema={},           # No payload required for sync
            account_schema={
                "business_id": str,      # Facebook Business Manager ID
                "access_token": str,     # Facebook API access token
                "app_id": str,           # Facebook App ID
                "app_secret": str        # Facebook App Secret
            }
        )(sync_metrics)        

    def process_task(self, action: str, payload: Dict, account: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an action with rate limit monitoring and error handling.
        
        Args:
            action_name (str): Name of the registered action to execute
            payload (Dict[str, Any]): Action parameters including account credentials
            account (Optional[str]): Account credentials
            
        Returns:
            Dict[str, Any]: Standardized response containing either result or error
        """
        try:
            # Update access token in rate limit monitor
            if account and "access_token" in account:
                self.rate_limit_monitor.set_access_token(account["access_token"])
                
            # Check rate limits before executing action
            rate_limit_info = self.rate_limit_monitor.check_rate_limits()
            if rate_limit_info:
                self.logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "action": action,
                        "rate_limit_info": rate_limit_info
                    }
                )
                return rate_limit_info
                
            # If rate limit check passed, proceed with action execution    
            result = super().process_task(action, payload, account)
            
            return result
            
        finally:
            # Always clear access token after task completion
            self.rate_limit_monitor.set_access_token(None)

if __name__ == "__main__":
    """
    Entry point for running the provider as a standalone service.
    """
    provider = FacebookProvider()
    provider.start() 