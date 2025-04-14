"""
Metrics-related actions for Facebook provider.
"""

from arbvantage_provider.schemas import ProviderResponse
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.adaccount import AdAccount
from datetime import datetime
import time
from typing import Dict, Any

def get_page_insights(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get page insights with automatic retry on failure.
    
    Args:
        payload: Action payload containing page and metric information
        
    Returns:
        ProviderResponse with status:
        - "success" if insights retrieved successfully
        - "error" if there was an error
        - "limit" if rate limits are exceeded
    """
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
        
    if not payload.get("page_id"):
        return ProviderResponse(
            status="error",
            message="Missing page ID in payload",
            data={"error": "missing_page_id"}
        ).model_dump()
        
    if not payload.get("metric"):
        return ProviderResponse(
            status="error",
            message="Missing metric in payload",
            data={"error": "missing_metric"}
        ).model_dump()
        
    if not payload.get("period"):
        return ProviderResponse(
            status="error",
            message="Missing period in payload",
            data={"error": "missing_period"}
        ).model_dump()
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Initialize Facebook API
            FacebookAdsApi.init(access_token=payload["account"]["access_token"])
            api = FacebookAdsApi.get_default_api()
            
            # Get page insights
            page = AdAccount(f"act_{payload['account']['business_id']}")
            insights = page.get_insights(
                fields=[payload["metric"]],
                params={
                    'time_range': {
                        'since': payload["period"],
                        'until': datetime.now().strftime("%Y-%m-%d")
                    }
                }
            )
            
            return ProviderResponse(
                status="success",
                data={
                    "page_id": payload["page_id"],
                    "metric": payload["metric"],
                    "value": insights[0][payload["metric"]] if insights else 0,
                    "period": payload["period"]
                },
                metadata={"retry_count": retry_count}
            ).model_dump()
            
        except FacebookRequestError as e:
            if e.api_error_code() == 4:  # API Throttling
                retry_count += 1
                if retry_count >= max_retries:
                    return ProviderResponse(
                        status="limit",
                        message="Max retries exceeded due to API throttling",
                        data={
                            "error": str(e),
                            "retry_count": retry_count,
                            "error_code": e.api_error_code()
                        }
                    ).model_dump()
                time.sleep(2 ** retry_count)  # Exponential backoff
            else:
                return ProviderResponse(
                    status="error",
                    message=str(e),
                    data={
                        "error_code": e.api_error_code(),
                        "error": str(e)
                    }
                ).model_dump()
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                return ProviderResponse(
                    status="error",
                    message="Max retries exceeded",
                    data={
                        "error": str(e),
                        "retry_count": retry_count
                    }
                ).model_dump()
            time.sleep(2 ** retry_count)  # Exponential backoff 