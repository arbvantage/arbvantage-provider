"""
External API Provider Example

This example demonstrates how to implement a provider that interacts with an external API using the Arbvantage Provider Framework and explicit Pydantic schemas.
It shows how to:
1. Integrate with a third-party API (e.g., GitHub)
2. Register actions for API calls
3. Handle API keys and error handling

Environment variables required:
- PROVIDER_NAME: Name of the provider (defaults to "external-api-provider")
- PROVIDER_AUTH_TOKEN: Authentication token for the hub
- HUB_GRPC_URL: URL of the hub service (defaults to "hub-grpc:50051")
- GITHUB_TOKEN: GitHub API token

Why is this important?
----------------------
This example shows how to safely and cleanly wrap external APIs with strict validation and error handling.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from arbvantage_provider import Provider, ProviderResponse
import requests
import os

# --- Pydantic Schemas ---
class RepoInfoPayload(BaseModel):
    owner: str = Field(..., description="GitHub repository owner")
    repo: str = Field(..., description="GitHub repository name")

class SearchReposPayload(BaseModel):
    query: str = Field(..., description="Search query for repositories")
    per_page: Optional[int] = Field(10, description="Results per page")

class GitHubAccount(BaseModel):
    token: str = Field(..., description="GitHub API token")

class ExternalAPIProvider(Provider):
    """
    Example provider for interacting with the GitHub API using explicit Pydantic schemas.
    """
    def __init__(self):
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "external-api-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN", "your-auth-token"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        self._register_actions()

    def handle_task_exception(self, e: Exception, action: str, payload: dict, account: Optional[dict]) -> dict:
        """
        Handles exceptions that occur during task processing.

        This method is overridden to provide specific handling for network-related errors
        that may occur when interacting with the GitHub API.
        """
        if isinstance(e, requests.RequestException):
            self.logger.error(
                "A network error occurred while processing the task",
                action=action,
                error=str(e),
                payload=payload
            )
            return self._handle_response(
                ProviderResponse(status="error", message=f"GitHub API request failed: {e}"),
                action=action
            )
        
        # For any other exceptions, we fall back to the default behavior
        # defined in the base Provider class. This ensures that we still have
        # a generic error handling mechanism for unexpected issues.
        return super().handle_task_exception(e, action, payload, account)

    def _register_actions(self):
        @self.actions.register(
            name="get_repo_info",
            description="Get information about a GitHub repository",
            payload_schema=RepoInfoPayload,
            account_schema=GitHubAccount
        )
        def get_repo_info(payload: RepoInfoPayload, account: GitHubAccount) -> ProviderResponse:
            headers = {"Authorization": f"token {account.token}"}
            url = f"https://api.github.com/repos/{payload.owner}/{payload.repo}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)
            
            return ProviderResponse(status="success", data=response.json())

        @self.actions.register(
            name="search_repos",
            description="Search for GitHub repositories",
            payload_schema=SearchReposPayload,
            account_schema=GitHubAccount
        )
        def search_repos(payload: SearchReposPayload, account: GitHubAccount) -> ProviderResponse:
            headers = {"Authorization": f"token {account.token}"}
            url = f"https://api.github.com/search/repositories"
            params = {"q": payload.query, "per_page": payload.per_page}

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)

            return ProviderResponse(status="success", data=response.json())

if __name__ == "__main__":
    provider = ExternalAPIProvider()
    provider.start() 