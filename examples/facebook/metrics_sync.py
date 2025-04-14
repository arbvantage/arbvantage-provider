"""
Metrics Synchronization Example

This example demonstrates how to synchronize metrics from Facebook using the provider.
It shows how to:
1. Fetch metrics for campaigns, ad sets, and ads
2. Handle different time ranges
3. Process large amounts of data
4. Use rate limiting for metrics fetching
"""

from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import AdvancedRateLimitMonitor
from arbvantage_provider.schemas import ProviderResponse
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

class MetricsSyncProvider(Provider):
    """
    Metrics synchronization provider example.
    
    This provider demonstrates how to work with Facebook metrics:
    - Fetching metrics for different entities
    - Handling time ranges
    - Processing large datasets
    - Rate limiting for metrics operations
    """
    
    def __init__(self):
        """
        Initialize the metrics synchronization provider.
        """
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "metrics-sync"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Example 1: Sync campaign metrics
        @self.actions.register(
            name="sync_campaign_metrics",
            description="Synchronize campaign metrics",
            payload_schema={
                "campaign_id": str,
                "start_date": str,
                "end_date": str,
                "metrics": List[str]
            },
            account_schema={
                "business_id": str,
                "access_token": str
            }
        )
        def sync_campaign_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Synchronize metrics for a specific campaign.
            """
            # Validate date range
            start_date = datetime.strptime(payload["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(payload["end_date"], "%Y-%m-%d")
            
            if end_date < start_date:
                return ProviderResponse(
                    status="error",
                    message="End date must be after start date",
                    data={"campaign_id": payload["campaign_id"]}
                )
                
            # In a real implementation, this would call Facebook API
            metrics_data = {
                "campaign_id": payload["campaign_id"],
                "start_date": payload["start_date"],
                "end_date": payload["end_date"],
                "metrics": {
                    "impressions": 1000,
                    "clicks": 50,
                    "spend": 100.50,
                    "ctr": 0.05,
                    "cpc": 2.01
                }
            }
            
            return ProviderResponse(
                status="success",
                data=metrics_data
            )
            
        # Example 2: Batch sync metrics
        @self.actions.register(
            name="batch_sync_metrics",
            description="Synchronize metrics for multiple entities",
            payload_schema={
                "entity_ids": List[str],
                "entity_type": str,
                "start_date": str,
                "end_date": str
            },
            account_schema={
                "business_id": str,
                "access_token": str
            }
        )
        def batch_sync_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Synchronize metrics for multiple entities in batch.
            """
            # Validate entity type
            valid_types = ["campaign", "adset", "ad"]
            if payload["entity_type"] not in valid_types:
                return ProviderResponse(
                    status="error",
                    message=f"Invalid entity type. Must be one of: {valid_types}",
                    data={"entity_type": payload["entity_type"]}
                )
                
            # In a real implementation, this would call Facebook API
            results = []
            for entity_id in payload["entity_ids"]:
                results.append({
                    "entity_id": entity_id,
                    "entity_type": payload["entity_type"],
                    "metrics": {
                        "impressions": 1000,
                        "clicks": 50,
                        "spend": 100.50
                    }
                })
                
            return ProviderResponse(
                status="success",
                data={
                    "total_entities": len(results),
                    "results": results
                }
            )
            
        # Example 3: Get real-time metrics
        @self.actions.register(
            name="get_realtime_metrics",
            description="Get real-time metrics for an entity",
            payload_schema={
                "entity_id": str,
                "entity_type": str
            },
            account_schema={
                "business_id": str,
                "access_token": str
            }
        )
        def get_realtime_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Get real-time metrics for a specific entity.
            """
            # In a real implementation, this would call Facebook API
            return ProviderResponse(
                status="success",
                data={
                    "entity_id": payload["entity_id"],
                    "entity_type": payload["entity_type"],
                    "metrics": {
                        "impressions": 100,
                        "clicks": 5,
                        "spend": 10.50,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            )

if __name__ == "__main__":
    """
    Entry point for running the provider as a standalone service.
    """
    provider = MetricsSyncProvider()
    provider.start()