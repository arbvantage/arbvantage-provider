"""
Campaign Management Example

This example demonstrates how to work with Facebook campaigns using the provider.
It shows how to:
1. Create and manage campaigns
2. Handle campaign status
3. Work with ad sets and ads
4. Use rate limiting for campaign operations
"""

from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import AdvancedRateLimitMonitor
from arbvantage_provider.schemas import ProviderResponse
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampaignProvider(Provider):
    """
    Campaign management provider example.
    
    This provider demonstrates how to work with Facebook campaigns:
    - Campaign creation and management
    - Status tracking
    - Ad set and ad management
    - Rate limiting for campaign operations
    """
    
    def __init__(self):
        """
        Initialize the campaign management provider.
        """
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "campaign-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Example 1: Create campaign
        @self.actions.register(
            name="create_campaign",
            description="Create a new campaign",
            payload_schema={
                "name": str,
                "objective": str,
                "status": str,
                "budget": float,
                "start_time": str
            },
            account_schema={
                "business_id": str,
                "access_token": str,
                "app_id": str,
                "app_secret": str
            }
        )
        def create_campaign(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Create a new campaign with specified parameters.
            """
            try:
                # Initialize Facebook API
                FacebookAdsApi.init(
                    access_token=payload["account"]["access_token"],
                    app_id=payload["account"]["app_id"],
                    app_secret=payload["account"]["app_secret"]
                )
                api = FacebookAdsApi.get_default_api()
                
                # Create campaign
                account = AdAccount(f"act_{payload['account']['business_id']}")
                campaign = account.create_campaign(
                    fields=[],
                    params={
                        'name': payload["name"],
                        'objective': payload["objective"],
                        'status': payload["status"],
                        'daily_budget': payload["budget"],
                        'start_time': payload["start_time"]
                    }
                )
                
                return ProviderResponse(
                    status="success",
                    data={
                        "campaign_id": campaign.get("id"),
                        "name": payload["name"],
                        "objective": payload["objective"],
                        "status": payload["status"],
                        "budget": payload["budget"],
                        "start_time": payload["start_time"]
                    }
                )
                
            except FacebookRequestError as e:
                logger.error(f"Facebook API error: {e}")
                return ProviderResponse(
                    status="error",
                    message=str(e),
                    data={"error_code": e.api_error_code()}
                )
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return ProviderResponse(
                    status="error",
                    message=str(e)
                )
            
        # Example 2: Get campaign status
        @self.actions.register(
            name="get_campaign_status",
            description="Get campaign status and performance",
            payload_schema={
                "campaign_id": str
            },
            account_schema={
                "business_id": str,
                "access_token": str
            }
        )
        def get_campaign_status(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Get detailed status and performance metrics for a campaign.
            """
            try:
                # Initialize Facebook API
                FacebookAdsApi.init(access_token=payload["account"]["access_token"])
                api = FacebookAdsApi.get_default_api()
                
                # Get campaign info
                campaign = Campaign(payload["campaign_id"])
                campaign_info = campaign.api_get(fields=[
                    'name',
                    'status',
                    'daily_budget',
                    'start_time',
                    'stop_time',
                    'objective'
                ])
                
                # Get campaign insights
                insights = campaign.get_insights(fields=[
                    'spend',
                    'impressions',
                    'clicks',
                    'ctr',
                    'cpc'
                ])
                
                return ProviderResponse(
                    status="success",
                    data={
                        "campaign_id": campaign_info.get("id"),
                        "status": campaign_info.get("status"),
                        "spend": insights[0].get("spend") if insights else 0,
                        "impressions": insights[0].get("impressions") if insights else 0,
                        "clicks": insights[0].get("clicks") if insights else 0,
                        "ctr": insights[0].get("ctr") if insights else 0,
                        "cpc": insights[0].get("cpc") if insights else 0
                    }
                )
                
            except FacebookRequestError as e:
                logger.error(f"Facebook API error: {e}")
                return ProviderResponse(
                    status="error",
                    message=str(e),
                    data={"error_code": e.api_error_code()}
                )
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return ProviderResponse(
                    status="error",
                    message=str(e)
                )
            
        # Example 3: Update campaign budget
        @self.actions.register(
            name="update_campaign_budget",
            description="Update campaign budget",
            payload_schema={
                "campaign_id": str,
                "budget": float
            },
            account_schema={
                "business_id": str,
                "access_token": str
            }
        )
        def update_campaign_budget(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Update campaign budget with validation.
            """
            try:
                # Validate budget
                if payload["budget"] < 1.0:
                    return ProviderResponse(
                        status="error",
                        message="Budget must be at least 1.0",
                        data={"campaign_id": payload["campaign_id"]}
                    )
                    
                # Initialize Facebook API
                FacebookAdsApi.init(access_token=payload["account"]["access_token"])
                api = FacebookAdsApi.get_default_api()
                
                # Update campaign budget
                campaign = Campaign(payload["campaign_id"])
                campaign.update({
                    'daily_budget': payload["budget"]
                })
                
                return ProviderResponse(
                    status="success",
                    data={
                        "campaign_id": payload["campaign_id"],
                        "new_budget": payload["budget"],
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                )
                
            except FacebookRequestError as e:
                logger.error(f"Facebook API error: {e}")
                return ProviderResponse(
                    status="error",
                    message=str(e),
                    data={"error_code": e.api_error_code()}
                )
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return ProviderResponse(
                    status="error",
                    message=str(e)
                )

if __name__ == "__main__":
    """
    Entry point for running the provider as a standalone service.
    """
    provider = CampaignProvider()
    provider.start() 