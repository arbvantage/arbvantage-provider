"""
Provider module for handling communication with the Hub service.

This module implements the core functionality of a provider service that:
1. Connects to a Hub service using gRPC
2. Receives tasks from the Hub
3. Processes tasks using registered actions
4. Returns results back to the Hub

The module handles:
- Connection management with retry logic
- Task processing and validation
- Error handling and logging
- Graceful shutdown
- Rate limiting
"""

import grpc
import json
import time
import signal
import backoff
from typing import Optional, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
import inspect

from .protos import hub_pb2, hub_pb2_grpc
from .actions import ActionsRegistry
from .exceptions import ActionNotFoundError, InvalidPayloadError
from .schemas import ProviderResponse
from .rate_limit import RateLimitMonitor, NoRateLimitMonitor, TimeBasedRateLimitMonitor, AdvancedRateLimitMonitor, CustomRateLimitMonitor   
from .logger import ProviderLogger

class Provider:
    """
    Main class for building providers that communicate with the Hub service via gRPC.
    
    This class manages the full lifecycle of a provider:
    - Establishes and maintains a connection to the Hub
    - Receives and processes tasks from the Hub
    - Executes registered actions with payload validation
    - Handles errors and logs all important events
    - Supports rate limiting and graceful shutdown
    
    Why is this important?
    -----------------------------------
    This class abstracts away the complexity of gRPC communication, error handling,
    and task management, allowing you to focus on business logic and action implementation.
    
    Attributes:
        name (str): Unique identifier for the provider
        auth_token (str): Authentication token for Hub communication
        hub_url (str): URL of the Hub service
        execution_timeout (int): Default timeout for task execution in seconds
        running (bool): Flag indicating if the provider is running
        logger (ProviderLogger): Logger instance for the provider
        actions (ActionsRegistry): Registry of available actions
        rate_limit_monitor (RateLimitMonitor): Rate limit monitoring implementation
    """
    
    def __init__(
        self,
        name: str,
        auth_token: str,
        hub_url: str,
        timezone: str = "UTC",
        execution_timeout: int = 1,
        rate_limit_monitor: Optional[RateLimitMonitor] = None,
        log_file: Optional[str] = None,
        log_level: str = "INFO"
    ):
        """
        Initialize the provider with required configuration.
        
        This constructor sets up all the core components of the provider, including:
        - Logging (for debugging and monitoring)
        - Action registry (for registering and looking up actions)
        - Rate limit monitor (to prevent API abuse)
        - Timezone handling (for correct time reporting)
        
        Args:
            name (str): Unique identifier for the provider
            auth_token (str): Authentication token for Hub communication
            hub_url (str): URL of the Hub service
            execution_timeout (int, optional): Default timeout for task execution. Defaults to 1.
            rate_limit_monitor (Optional[RateLimitMonitor]): Rate limit monitoring implementation
            log_file (Optional[str]): Path to log file
            log_level (str): Logging level (default: INFO)
        """
        self.name = name
        self.auth_token = auth_token
        self.hub_url = hub_url
        self.timezone = timezone
        self.execution_timeout = execution_timeout
        self.running = True
        
        # Initialize logger
        self.logger = ProviderLogger(
            name=name,
            level=log_level,
            log_file=log_file
        )
        
        self.actions = ActionsRegistry()
        
        # Initialize rate limit monitor
        self.rate_limit_monitor = rate_limit_monitor or NoRateLimitMonitor()

        # Initialize timezone
        try:
            self._tzinfo = ZoneInfo(timezone)
        except Exception:
            self._tzinfo = ZoneInfo("UTC")

    def _create_channel(self):
        """
        Create a gRPC channel to connect to the Hub with retry logic.
        
        This method implements exponential backoff for connection attempts:
        - Starts with a base delay
        - Increases delay exponentially with each retry
        - Continues until successful connection or max time reached
        
        Returns:
            grpc.Channel: A gRPC channel connected to the Hub
        """
        @backoff.on_exception(
            backoff.expo,
            (grpc.RpcError, ConnectionRefusedError),
            max_tries=None,
            max_time=300,
            on_backoff=lambda details: self.logger.info(
                "Trying to connect to hub...",
                attempt=details['tries']
            )
        )
        def create():
            channel = grpc.insecure_channel(self.hub_url)
            grpc.channel_ready_future(channel).result(timeout=30)
            return channel
        return create()

    def _handle_response(self, response: ProviderResponse, action: Optional[str] = None) -> Dict[str, Any]:
        """
        Helper method to convert ProviderResponse to dictionary and wrap data field with provider name.
        
        This method ensures that all responses sent back to the Hub are consistently formatted and include
        useful metadata such as provider name, action, timezone, and timestamps. This is important for debugging,
        monitoring, and traceability in distributed systems.
        
        Args:
            response (ProviderResponse): Response to convert
            action (Optional[str]): Name of the action (for metadata)
        
        Returns:
            Dict[str, Any]: Converted response with data field wrapped with provider name
        """
        response_dict = response.model_dump()
        if "data" in response_dict:
            now = datetime.now(self._tzinfo)
            now_utc = datetime.now(ZoneInfo("UTC"))
            data = {
                "provider": self.name,
                "action": action or "",
                "timezone": str(self._tzinfo),
                "now": now.isoformat(),
                "now_utc": now_utc.isoformat(),
                "response": response_dict["data"] or {}
            }
            response_dict["data"] = data
        return response_dict

    def _filter_action_params(self, handler, params: dict) -> dict:
        """
        Filters the input parameters dictionary to only include those
        that are accepted by the handler function.

        This is useful when you have a generic set of parameters (e.g., payload, account, provider, logger, etc.)
        but your action handler only needs a subset of them. By filtering, you avoid passing unexpected arguments
        and make your action handlers more flexible and easier to maintain.

        Args:
            handler (Callable): The action handler function.
            params (dict): The dictionary of all possible parameters.

        Returns:
            dict: A dictionary containing only the parameters accepted by the handler.
        """
        sig = inspect.signature(handler)
        accepted_params = sig.parameters.keys()
        has_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )
        if has_kwargs:
            # If handler accepts **kwargs, pass all params
            return params
        # Only keep parameters that the handler actually accepts
        return {k: v for k, v in params.items() if k in accepted_params}

    def process_task(self, action: str, payload: Dict, account: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single task by executing the specified action with given parameters.
        
        This method is the main entry point for handling tasks received from the Hub. It performs:
        - Rate limit checks (global and per-action)
        - Action lookup and validation
        - Parameter validation (payload and account)
        - Action execution (with filtered parameters)
        - Response validation and formatting
        - Error handling and logging
        
        Args:
            action (str): Name of the action to execute
            payload (Dict): Action parameters
            account (Optional[str]): Account identifier if applicable
        
        Returns:
            Dict[str, Any]: Processed task result with status and data
        """
        try:
            # Check provider rate limits
            limits = self.rate_limit_monitor.check_rate_limits()
            if limits and limits.get("rate_limited"):
                self.logger.warning(
                    "Rate limit exceeded",
                    action=action,
                    wait_time=limits.get("wait_time")
                )
                return self._handle_response(ProviderResponse(
                    status="limit",
                    message=f"Rate limit exceeded: {limits.get('message')}",
                    data={"wait_time": limits.get("wait_time")}
                ))

            action_def = self.actions.get_action(action)
            if not action_def:
                self.logger.error(
                    "Action not found",
                    action=action,
                    available_actions=list(self.actions.get_actions().keys())
                )
                return self._handle_response(ProviderResponse(status="error", message=f"Action '{action}' not found"))

            # Check action-specific rate limits if action supports it
            if hasattr(action_def, 'check_rate_limits'):
                limits = action_def.check_rate_limits(account, payload)
                if limits and limits.get("rate_limited"):
                    self.logger.warning(
                        "Action-specific rate limit exceeded",
                        action=action,
                        wait_time=limits.get("wait_time")
                    )
                    return self._handle_response(ProviderResponse(
                        status="limit",
                        message=f"Action-specific rate limit exceeded: {limits.get('message')}",
                        data={"wait_time": limits.get("wait_time")}
                    ))

            # Validate required parameters for payload if schema exists
            if hasattr(action_def, 'payload_schema') and action_def.payload_schema:
                missing_params = [
                    param for param in action_def.payload_schema.keys()
                    if param not in payload
                ]
                if missing_params:
                    self.logger.warning(
                        "Missing required parameters",
                        action=action,
                        missing_params=missing_params
                    )
                    return self._handle_response(ProviderResponse(status="error", message=f"Missing required parameters: {', '.join(missing_params)}"))
            
            # Validate required parameters for account if schema exists
            if hasattr(action_def, 'account_schema') and action_def.account_schema:
                missing_account_params = [
                    param for param in action_def.account_schema.keys()
                    if not account or param not in account
                ]
                if missing_account_params:
                    self.logger.warning(
                        "Missing required account parameters",
                        action=action,
                        missing_params=missing_account_params
                    )
                    return self._handle_response(ProviderResponse(status="error", message=f"Missing required account parameters: {', '.join(missing_account_params)}"))
            
            action_params = {
                'payload': {},  # By default, we pass empty payload
                'account': {},  # By default, we pass empty account
                'provider': {
                    'name': self.name,
                    'token': self.auth_token,
                },                
                'timezone': self.timezone,
                'now': datetime.now(self._tzinfo).isoformat(),
                'now_utc': datetime.now(ZoneInfo("UTC")).isoformat(),
            }

            # Filter payload parameters only if schema exists
            if hasattr(action_def, 'payload_schema') and action_def.payload_schema:
                action_params['payload'] = {
                    param: payload[param]
                    for param in action_def.payload_schema.keys()
                }

            # Filter account parameters only if schema exists
            if hasattr(action_def, 'account_schema') and action_def.account_schema:
                action_params['account'] = {
                    param: account[param]
                    for param in action_def.account_schema.keys()
                }
            
            # Execute action and validate response
            self.logger.info(
                "Executing action",
                action=action
            )
            
            # Filter parameters before passing to the handler
            # This ensures that only the parameters required by the handler are passed
            # For example, if the handler only needs 'payload' and 'logger', it will not receive 'account', 'provider', etc.
            filtered_params = self._filter_action_params(action_def.handler, action_params)
            result = action_def.handler(**filtered_params)
            
            # Check if result is an instance of ProviderResponse
            if not isinstance(result, ProviderResponse):
                error_msg = f"Action {action} must return ProviderResponse instance, got {type(result)}"
                self.logger.error(
                    "Invalid response type",
                    action=action,
                    expected_type="ProviderResponse",
                    actual_type=str(type(result))
                )
                return self._handle_response(ProviderResponse(
                    status="error",
                    data=result,
                    message=error_msg
                ))
            
            self.logger.info(
                "Action completed successfully",
                action=action,
                status=result.status
            )
            
            return self._handle_response(result)

        except Exception as e:
            self.logger.exception(
                "Error processing task",
                action=action,
                error=str(e)
            )
            return self._handle_response(ProviderResponse(status="error", message=str(e)))

    def start(self):
        """
        Start the provider service.
        
        This method:
        1. Sets up signal handlers for graceful shutdown
        2. Establishes connection to the Hub
        3. Starts processing tasks in a loop
        4. Handles connection errors and retries
        
        This is the main loop of the provider. It will keep running until a shutdown signal is received.
        """
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Starting provider worker")
        
        while self.running:
            try:
                with self._create_channel() as channel:
                    self.logger.info(
                        "Successfully connected to HUB",
                        hub_url=self.hub_url
                    )
                    stub = hub_pb2_grpc.HubStub(channel)
                    self._process_tasks(stub)
            except Exception as e:
                if self.running:
                    self.logger.exception(
                        "Unexpected error",
                        error=str(e)
                    )
                    time.sleep(1)

    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals for graceful termination.
        
        This method allows the provider to shut down cleanly when receiving SIGINT or SIGTERM.
        It sets the running flag to False, which will break the main loop.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info("Signal received, stopping provider...")
        self.running = False

    def _process_tasks(self, stub):
        """
        Process tasks received from the Hub.
        
        This method:
        1. Polls for new tasks from the Hub
        2. Processes tasks and submits results
        3. Handles various error conditions
        
        This is the main worker loop for fetching and processing tasks. It ensures that each task is handled
        robustly, with error handling and retries as needed.
        
        Args:
            stub: gRPC stub for Hub communication
        """
        while self.running:
            try:
                task = stub.GetTask(hub_pb2.ProviderRequest(
                    provider=self.name,
                    auth_token=self.auth_token
                ))

                if not task.id:
                    time.sleep(self.execution_timeout)
                    continue

                self.logger.info(
                    "Received task",
                    id=task.id,
                    action=task.action
                )
                
                try:
                    payload = json.loads(task.payload.decode('utf-8'))
                    action = task.action
                    account = task.account
                    
                    result = self.process_task(action, payload, account)
                    status = result["status"]

                    # Submit task result back to Hub
                    stub.SubmitTaskResult(hub_pb2.TaskResult(
                        id=task.id,
                        provider=self.name,
                        auth_token=self.auth_token,
                        payload=json.dumps(payload),
                        action=action,
                        status=status,
                        result=json.dumps(result),
                        account=account
                    ))
                    
                    self.logger.info(
                        "Task completed",
                        id=task.id,
                        status=status
                    )
                    
                except json.JSONDecodeError as e:
                    self.logger.error(
                        "Failed to parse task data",
                        error=str(e)
                    )
                    result = ProviderResponse(
                        status="error",
                        message="Failed to parse task data",
                        data={"error": str(e)}
                    ).model_dump()
                    stub.SubmitTaskResult(hub_pb2.TaskResult(
                        id=task.id,
                        provider=self.name,
                        auth_token=self.auth_token,
                        status="error",
                        result=json.dumps(result)
                    ))
                    continue

            except grpc.RpcError as e:
                # Log gRPC error details in a safe way, even if some attributes are missing
                error_details = getattr(e, "details", lambda: str(e))()
                error_code = getattr(e, "code", lambda: "Unknown")()
                self.logger.error(
                    "gRPC error",
                    error=error_details,
                    code=str(error_code)
                )
                if error_code == grpc.StatusCode.UNAUTHENTICATED:
                    self.logger.error("Provider authentication error")
                    return
                if error_code == grpc.StatusCode.NOT_FOUND:
                    self.logger.info("Task not found, waiting for next one...")
                    time.sleep(self.execution_timeout)
                    continue
                result = ProviderResponse(
                    status="error",
                    message="gRPC error occurred",
                    data={
                        "error": error_details,
                        "code": str(error_code)
                    }
                ).model_dump()
                if task.id:
                    stub.SubmitTaskResult(hub_pb2.TaskResult(
                        id=task.id,
                        provider=self.name,
                        auth_token=self.auth_token,
                        status="error",
                        result=json.dumps(result)
                    ))
                time.sleep(self.execution_timeout)
                continue
                
            except Exception as e:
                self.logger.exception(
                    "Unexpected error processing task",
                    error=str(e)
                )
                result = ProviderResponse(
                    status="error",
                    message="Unexpected error occurred",
                    data={"error": str(e)}
                ).model_dump()
                if task.id:
                    stub.SubmitTaskResult(hub_pb2.TaskResult(
                        id=task.id,
                        provider=self.name,
                        auth_token=self.auth_token,
                        status="error",
                        result=json.dumps(result)
                    ))
                time.sleep(self.execution_timeout)
                continue
