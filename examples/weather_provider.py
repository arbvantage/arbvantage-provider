from arbvantage_provider import Provider
import os
import requests
from typing import Dict, List
from arbvantage_provider.schemas import ProviderResponse

class WeatherProvider(Provider):
    def __init__(self):
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "weather"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051"),
            execution_timeout=int(os.getenv("TASK_EXECUTION_TIMEOUT", 30))
        )
        
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
        @self.actions.register(
            name="get_current_weather",
            description="Get current weather for a specific city",
            payload_schema={
                "city": str,
                "country_code": str
            },
            account_schema={
                "api_key": str
            }
        )
        def get_current_weather(payload: Dict, account: Dict) -> Dict:
            """
            Get current weather data for a specified city
            """
            try:
                api_key = account.get("api_key")
                city = payload.get("city")
                country_code = payload.get("country_code")
                
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
            payload_schema={
                "city": str,
                "country_code": str
            },
            account_schema={
                "api_key": str
            }
        )
        def get_forecast(payload: Dict, account: Dict) -> Dict:
            """
            Get 5-day weather forecast for a specified city
            """
            try:
                api_key = account.get("api_key")
                city = payload.get("city")
                country_code = payload.get("country_code")
                
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
    provider = WeatherProvider()
    provider.start() 