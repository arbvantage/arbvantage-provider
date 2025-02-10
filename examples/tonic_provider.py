from arbvantage_provider import Provider
import os

class TonicProvider(Provider):
    def __init__(self):
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "tonic"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051"),
            execution_timeout=int(os.getenv("TASK_EXECUTION_TIMEOUT", 1))
        )

        # Регистрация действий
        @self.actions.register(
            name="offers_all",
            description="get offers",
            payload_schema={"businesses": list}
        )
        def get_offers_all(businesses: list, account: str = None):
            # Реализация метода
            pass

        @self.actions.register(
            name="offers",
            description="get offers"
        )
        def get_offers(account: str = None):
            # Реализация метода
            pass

if __name__ == "__main__":
    provider = TonicProvider()
    provider.start() 