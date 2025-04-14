"""
Business-related actions for Facebook provider.
"""

from arbvantage_provider.schemas import ProviderResponse
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.adaccount import AdAccount
from typing import Dict, Any

def get_business_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get basic information about a business account.
    
    Args:
        payload: Action payload containing account information
        
    Returns:
        ProviderResponse with status:
        - "success" if business info retrieved successfully
        - "error" if there was an error
        - "limit" if rate limits are exceeded
    """
    try:
        # Validate payload
        if not payload.get("account") or not payload["account"].get("access_token"):
            return ProviderResponse(
                status="error",
                message="Missing access token in account information",
                data={"error": "missing_access_token"}
            ).model_dump()
            
        if not payload["account"].get("business_id"):
            return ProviderResponse(
                status="error",
                message="Missing business ID in account information",
                data={"error": "missing_business_id"}
            ).model_dump()
            
        # Initialize Facebook API
        FacebookAdsApi.init(access_token=payload["account"]["access_token"])
        api = FacebookAdsApi.get_default_api()
        
        # Get business account info
        account = AdAccount(f"act_{payload['account']['business_id']}")
        account_info = account.api_get(fields=[
            'name',
            'timezone_name',
            'currency',
            'business_name',
            'business_city',
            'business_country_code'
        ])
        
        return ProviderResponse(
            status="success",
            data={
                "business_id": account_info.get("id"),
                "name": account_info.get("name"),
                "timezone": account_info.get("timezone_name"),
                "currency": account_info.get("currency"),
                "business_name": account_info.get("business_name"),
                "business_city": account_info.get("business_city"),
                "business_country": account_info.get("business_country_code")
            }
        ).model_dump()
        
    except FacebookRequestError as e:
        if e.api_error_code() == 4:  # API Throttling
            return ProviderResponse(
                status="limit",
                message="Rate limit exceeded",
                data={
                    "error_code": e.api_error_code(),
                    "error": str(e)
                }
            ).model_dump()
            
        return ProviderResponse(
            status="error",
            message=str(e),
            data={
                "error_code": e.api_error_code(),
                "error": str(e)
            }
        ).model_dump()
        
    except Exception as e:
        return ProviderResponse(
            status="error",
            message="Unexpected error getting business info",
            data={"error": str(e)}
        ).model_dump() 