from arbvantage_provider import Provider
import os

class ExampleProvider(Provider):
    def __init__(self):
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "example"), # unique name for your provider, should be unique across all providers. ask for this from the hub
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"), # you should ask for this from the hub
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051"), # url of the hub, you can change it to the hub url you want to use
            execution_timeout=int(os.getenv("TASK_EXECUTION_TIMEOUT", 1)) # timeout for the task, you can change it to the timeout you want to use
        )

        # Provider actions
        @self.actions.register(
            name="get_all_records",
            description="get all records",
            payload_schema={"users": list}
        )
        def get_all_records(users: list):
            # Implementation of the method
            pass


        @self.actions.register(
            name="verify_credentials",
            description="verify credentials",
            payload_schema={"credentials": dict}
        )
        def verify_credentials(credentials: dict):
            # Implementation of the method
            pass

if __name__ == "__main__":
    provider = ExampleProvider()
    provider.start() 