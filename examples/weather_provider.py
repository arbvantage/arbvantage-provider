"""
Weather Provider Example

This example demonstrates how to implement a provider that fetches weather data using the Arbvantage Provider Framework and explicit Pydantic schemas.
It shows how to:
1. Integrate with an external API (OpenWeatherMap)
2. Register actions for current weather and forecast
3. Handle API keys and error handling

Environment variables required:
- PROVIDER_NAME: Name of the provider (defaults to "weather")
- PROVIDER_AUTH_TOKEN: Authentication token for the hub
- HUB_GRPC_URL: URL of the hub service (defaults to "hub-grpc:50051")
- TASK_EXECUTION_TIMEOUT: Timeout for task execution in seconds (defaults to 30)

Why is this important?
-----------------------------------
This example shows how to work with external APIs, handle authentication, and process structured responses.
"""

import os
import requests
from typing import Optional
from pydantic import BaseModel, Field
from arbvantage_provider import Provider, ProviderResponse

# --- Pydantic Schemas ---
class WeatherPayload(BaseModel):
    city: str = Field(..., min_length=1, description="City name")
    country_code: str = Field(..., min_length=2, max_length=2, description="Country code (ISO 3166-1 alpha-2)")

class WeatherAccount(BaseModel):
    api_key: str = Field(..., min_length=10, description="API key for OpenWeatherMap")

class WeatherProvider(Provider):
    """
    Provider for weather data using OpenWeatherMap API and explicit Pydantic schemas.
    """
    def __init__(self):
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "weather"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051"),
            execution_timeout=int(os.getenv("TASK_EXECUTION_TIMEOUT", 30))
        )
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self._register_weather_actions()

    def _register_weather_actions(self):
        @self.actions.register(
            name="get_current_weather",
            description="Get current weather for a specific city",
            payload_schema=WeatherPayload,
            account_schema=WeatherAccount
        )
        def get_current_weather(payload: WeatherPayload, account: WeatherAccount) -> ProviderResponse:
            """
            Get current weather data for a specified city.
            Args:
                payload (WeatherPayload): Validated payload with 'city' and 'country_code'.
                account (WeatherAccount): Validated account with 'api_key'.
            Returns:
                ProviderResponse: status 'success' and weather data, or 'error' on failure.
            """
            try:
                api_key = account.api_key
                city = payload.city
                country_code = payload.country_code
                url = f"{self.base_url}/weather"
                params = {
                    "q": f"{city},{country_code}",
                    "appid": api_key,
                    "units": "metric"
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return ProviderResponse(
                    status="success",
                    data={
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "wind_speed": data["wind"]["speed"],
                        "description": data["weather"][0]["description"],
                        "city": data["name"],
                        "country": data["sys"]["country"]
                    }
                )
            except requests.exceptions.RequestException as e:
                return ProviderResponse(
                    status="error",
                    message=f"Failed to fetch weather data: {str(e)}"
                )

        @self.actions.register(
            name="get_forecast",
            description="Get 5-day weather forecast for a specific city",
            payload_schema=WeatherPayload,
            account_schema=WeatherAccount
        )
        def get_forecast(payload: WeatherPayload, account: WeatherAccount) -> ProviderResponse:
            """
            Get 5-day weather forecast for a specified city.
            Args:
                payload (WeatherPayload): Validated payload with 'city' and 'country_code'.
                account (WeatherAccount): Validated account with 'api_key'.
            Returns:
                ProviderResponse: status 'success' and forecast data, or 'error' on failure.
            """
            try:
                api_key = account.api_key
                city = payload.city
                country_code = payload.country_code
                url = f"{self.base_url}/forecast"
                params = {
                    "q": f"{city},{country_code}",
                    "appid": api_key,
                    "units": "metric"
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                forecasts = []
                current_date = None
                for item in data["list"]:
                    date = item["dt_txt"].split()[0]
                    if date != current_date:
                        current_date = date
                        forecasts.append({
                            "date": date,
                            "temperature": item["main"]["temp"],
                            "feels_like": item["main"]["feels_like"],
                            "humidity": item["main"]["humidity"],
                            "wind_speed": item["wind"]["speed"],
                            "description": item["weather"][0]["description"]
                        })
                return ProviderResponse(
                    status="success",
                    data=forecasts[:5]
                )
            except requests.exceptions.RequestException as e:
                return ProviderResponse(
                    status="error",
                    message=f"Failed to fetch forecast data: {str(e)}"
                )

if __name__ == "__main__":
    """
    Run the provider if this script is executed directly.
    
    Why is this important?
    -----------------------------------
    This allows you to test the provider standalone before integrating with the hub.
    """
    provider = WeatherProvider()
    provider.start() 