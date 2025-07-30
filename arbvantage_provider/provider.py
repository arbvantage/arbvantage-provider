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
        
        # Always add metadata to ensure consistent format for all response types
        now = datetime.now(self._tzinfo)
        now_utc = datetime.now(ZoneInfo("UTC"))
        
        # Get the original data or create empty dict if None
        original_data = response_dict.get("data") or {}
        
        # Create standardized data structure with metadata
        data = {
            "provider": self.name,
            "action": action or "",
            "timezone": str(self._tzinfo),
            "now": now.isoformat(),
            "now_utc": now_utc.isoformat(),
            "response": original_data
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

    def _validate_schema(self, data: dict, schema: dict, path: str = "") -> list:
        """
        Recursively validate that data matches the schema, including nested dictionaries and lists.
        
        This method performs deep validation of nested dictionaries and lists against a schema definition.
        It checks both the presence of required keys and their types, including nested structures.
        
        Args:
            data (dict): Actual data to validate
            schema (dict): Schema definition with expected types or nested dict/list
            path (str): Current path in the data structure for error reporting
        
        Returns:
            list: List of validation errors (empty if all valid)
        
        Example:
            schema = {
                "name": str,
                "settings": {
                    "api_key": str,
                    "timeout": int
                }
            }
            errors = provider._validate_schema(data, schema)
        """
        errors = []
        for key, value_type in schema.items():
            current_path = f"{path}.{key}" if path else key
            if key not in data:
                errors.append(f"Missing key: {current_path}")
                continue
            if isinstance(value_type, dict):
                # Recursively validate nested dict
                if not isinstance(data[key], dict):
                    errors.append(f"Key {current_path} should be a dict, got {type(data[key]).__name__}")
                else:
                    errors.extend(self._validate_schema(data[key], value_type, current_path))
            elif isinstance(value_type, list):
                # Validate list of items with a schema
                if not isinstance(data[key], list):
                    errors.append(f"Key {current_path} should be a list, got {type(data[key]).__name__}")
                else:
                    if len(value_type) != 1:
                        errors.append(f"Schema for list {current_path} should have exactly one type definition")
                    else:
                        item_schema = value_type[0]
                        for idx, item in enumerate(data[key]):
                            item_path = f"{current_path}[{idx}]"
                            if isinstance(item_schema, dict):
                                if not isinstance(item, dict):
                                    errors.append(f"Item {item_path} should be a dict, got {type(item).__name__}")
                                else:
                                    errors.extend(self._validate_schema(item, item_schema, item_path))
                            else:
                                if not isinstance(item, item_schema):
                                    errors.append(f"Item {item_path} should be {item_schema.__name__}, got {type(item).__name__}")
            else:
                if not isinstance(data[key], value_type):
                    errors.append(f"Key {current_path} should be {value_type.__name__}, got {type(data[key]).__name__}")
        return errors
    
    def handle_task_exception(self, e: Exception, action: str, payload: dict, account: Optional[dict]) -> dict:
        """
        Handles exceptions that occur during task processing.
        This method can be overridden by subclasses for provider-specific exception handling.
        """
        self.logger.exception(
            "Error processing task",
            action=action,
            error=str(e)
        )
        return self._handle_response(ProviderResponse(
            status="error", 
            message=str(e),
            data={"error": str(e)}
        ), action=action)

    def process_task(self, action: str, payload: dict, account: Optional[dict] = None) -> dict:
        """
        Process a single task by executing the specified action with given parameters.
        Теперь использует Pydantic-схемы для строгой валидации payload и account.
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
                ), action=action)

            action_def = self.actions.get_action(action)
            if not action_def:
                self.logger.error(
                    "Action not found",
                    action=action,
                    available_actions=list(self.actions.get_actions().keys())
                )
                return self._handle_response(ProviderResponse(status="error", message=f"Action '{action}' not found"), action=action)

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
                    ), action=action)

            # Validate payload using Pydantic
            try:
                validated_payload = action_def.validate_payload(payload) if action_def.payload_schema else payload
            except InvalidPayloadError as e:
                self.logger.warning(
                    "Payload validation failed",
                    action=action,
                    error=str(e)
                )
                return self._handle_response(
                    ProviderResponse(
                        status="error",
                        message="Payload validation failed",
                        data={"error": str(e)}
                    ),
                    action=action
                )

            # Validate account using Pydantic
            if action_def.account_schema:
                if not account:
                    self.logger.warning(
                        "Account data is required but not provided",
                        action=action
                    )
                    return self._handle_response(
                        ProviderResponse(
                            status="error",
                            message="Account data is required but not provided"
                        ),
                        action=action
                    )
                try:
                    validated_account = action_def.validate_account(account)
                except InvalidPayloadError as e:
                    self.logger.warning(
                        "Account validation failed",
                        action=action,
                        error=str(e)
                    )
                    return self._handle_response(
                        ProviderResponse(
                            status="error",
                            message="Account validation failed",
                            data={"error": str(e)}
                        ),
                        action=action
                    )
            else:
                validated_account = account

            action_params = {
                'payload': validated_payload,
                'account': validated_account,
                'provider': {
                    'name': self.name,
                    'token': self.auth_token,
                },
                'timezone': self.timezone,
                'now': datetime.now(self._tzinfo).isoformat(),
                'now_utc': datetime.now(ZoneInfo("UTC")).isoformat(),
            }

            self.logger.info(
                "Executing action",
                action=action
            )

            filtered_params = self._filter_action_params(action_def.handler, action_params)
            result = action_def.handler(**filtered_params)

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

            return self._handle_response(result, action=action)

        except Exception as e:
            return self.handle_task_exception(e, action, payload, account)

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
                    account = json.loads(task.account.decode('utf-8')) if task.account else {}
                    
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
                        account=json.dumps(account)
                    ))

                    # Log the result
                    log_details = {
                        "id": task.id,
                        "status": status,
                    }
                    # Add error/limit details to the log for better diagnostics
                    if status in ["error", "limit"] and result.get("message"):
                        # Truncate the message to avoid excessively long log entries
                        log_details["details"] = str(result["message"])[:1024]

                    self.logger.info(
                        "Task completed",
                        **log_details
                    )
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