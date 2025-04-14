from arbvantage_provider.rate_limit import AdvancedRateLimitMonitor
from arbvantage_provider.logger import ProviderLogger
from facebook_business.api import FacebookAdsApi
from typing import Dict, Any, Optional

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
            Optional[Dict[str, Any]]: Rate limit information if exceeded, None otherwise
            
        Response Data Structure:
            {
                "error": "Rate limit exceeded",
                "retry_after": float,    # Seconds to wait before next request
                "current_usage": float,  # Current usage ratio (0.0 to 1.0)
                "limit_type": "facebook",
                "metrics": {
                    "calls_made": int,   # Number of API calls made
                    "total_calls": int,  # Total allowed API calls
                    "time_remaining": int # Time until limits reset
                }
            }
        """
        if not self.access_token:
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
            
            # Calculate usage ratio
            usage_ratio = calls_made / total_calls if total_calls > 0 else 0
            
            # Log rate limit metrics for monitoring
            self.logger.info(
                "Rate limit metrics",
                calls_made=calls_made,
                total_calls=total_calls,
                time_remaining=time_remaining,
                usage_ratio=usage_ratio
            )
            
            if time_remaining > 0:
                self.logger.warning(
                    "Rate limit exceeded",
                    calls_made=calls_made,
                    total_calls=total_calls,
                    time_remaining=time_remaining,
                    usage_ratio=usage_ratio
                )
                return {
                    "error": "Rate limit exceeded",
                    "retry_after": time_remaining,
                    "current_usage": usage_ratio,
                    "limit_type": "facebook",
                    "metrics": {
                        "calls_made": calls_made,
                        "total_calls": total_calls,
                        "time_remaining": time_remaining
                    }
                }
            
            return None
            
        except Exception as e:
            self.logger.exception(
                "Error checking Facebook API limits",
                error=str(e)
            )
            return {
                "error": "Error checking rate limits",
                "retry_after": 60,  # Default wait time on error
                "current_usage": 0,
                "limit_type": "facebook",
                "metrics": {
                    "error": str(e)
                }
            } 