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

from .protos import hub_pb2, hub_pb2_grpc
from .actions import ActionsRegistry
from .exceptions import ActionNotFoundError, InvalidPayloadError
from .schemas import ProviderResponse
from .rate_limit import RateLimitMonitor, NoRateLimitMonitor, TimeBasedRateLimitMonitor
from .logger import ProviderLogger

class Provider:
    """
    Base class for creating providers that communicate with the Hub service.
    
    This class implements the core provider functionality including:
    - Connection management to the Hub
    - Task processing pipeline
    - Action execution
    - Error handling
    - Graceful shutdown
    - Rate limiting
    
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
    
    # Default rate limit monitor for all instances
    _default_rate_limit_monitor: Optional[RateLimitMonitor] = None
    
    @classmethod
    def set_default_rate_limit(cls) -> None:
        """
        Set default rate limit for all provider instances.
        
        Args:
            min_delay: Minimum delay between calls in seconds
        """
        cls._default_rate_limit_monitor = NoRateLimitMonitor()
    
    def __init__(
        self,
        name: str,
        auth_token: str,
        hub_url: str,
        execution_timeout: int = 1,
        rate_limit_monitor: Optional[RateLimitMonitor] = None,
        log_file: Optional[str] = None,
        log_level: str = "INFO"
    ):
        """
        Initialize the provider with required configuration.
        
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
        self.rate_limit_monitor = rate_limit_monitor or self.__class__._default_rate_limit_monitor or NoRateLimitMonitor()

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

    def _handle_response(self, response: ProviderResponse) -> Dict[str, Any]:
        """
        Helper method to convert ProviderResponse to dictionary.
        
        Args:
            response (ProviderResponse): Response to convert
            
        Returns:
            Dict[str, Any]: Converted response
        """
        return response.model_dump()

    def process_task(self, action: str, payload: Dict, account: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single task by executing the specified action with given parameters.
        
        Args:
            action (str): Name of the action to execute
            payload (Dict): Action parameters
            account (Optional[str]): Account identifier if applicable
            
        Returns:
            Dict[str, Any]: Processed task result with status and data
        """
        try:
            action_def = self.actions.get_action(action)
            if not action_def:
                self.logger.error(
                    "Action not found",
                    action=action,
                    available_actions=list(self.actions.get_actions().keys())
                )
                return self._handle_response(ProviderResponse(status="error", message=f"Action '{action}' not found"))

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
                action=action,
                params=action_params
            )
            
            result = action_def.handler(**action_params)
            
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
        2. Handles rate limiting
        3. Processes tasks and submits results
        4. Handles various error conditions
        
        Args:
            stub: gRPC stub for Hub communication
        """
        while self.running:
            try:
                # Check rate limits before making request
                limits = self.rate_limit_monitor.check_rate_limits()
                if limits and limits.get("rate_limited"):
                    wait_time = limits.get("wait_time", self.execution_timeout)
                    self.logger.warning(
                        "Rate limit exceeded",
                        wait_time=wait_time
                    )
                    self.rate_limit_monitor.handle_throttling(wait_time)
                    
                    # Return rate limit response
                    result = ProviderResponse(
                        status="limit",
                        message=f"Rate limit exceeded. Please wait {wait_time} seconds",
                        data={"wait_time": wait_time}
                    ).model_dump()
                    
                    # Submit rate limit response to Hub
                    stub.SubmitTaskResult(hub_pb2.TaskResult(
                        provider=self.name,
                        auth_token=self.auth_token,
                        status="limit",
                        result=json.dumps(result)
                    ))
                    continue
                
                task = stub.GetTask(hub_pb2.ProviderRequest(
                    provider=self.name,
                    auth_token=self.auth_token
                ))

                if not task.task_id:
                    if task.action == b"rate_limited":
                        try:
                            rate_limit_data = json.loads(task.payload.decode('utf-8'))
                            wait_time = rate_limit_data.get("wait_time", self.execution_timeout)
                            self.logger.warning(
                                "Rate limit exceeded",
                                wait_time=wait_time
                            )
                            self.rate_limit_monitor.handle_throttling(wait_time)
                            
                            # Return rate limit response
                            result = ProviderResponse(
                                status="limit",
                                message=f"Rate limit exceeded. Please wait {wait_time} seconds",
                                data={"wait_time": wait_time}
                            ).model_dump()
                            
                            # Submit rate limit response to Hub
                            stub.SubmitTaskResult(hub_pb2.TaskResult(
                                provider=self.name,
                                auth_token=self.auth_token,
                                status="limit",
                                result=json.dumps(result)
                            ))
                        except json.JSONDecodeError:
                            self.rate_limit_monitor.handle_throttling(self.execution_timeout)
                    else:
                        self.rate_limit_monitor.handle_throttling(self.execution_timeout)
                    continue

                self.logger.info(
                    "Received task",
                    task_id=task.task_id,
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
                        task_id=task.task_id,
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
                        task_id=task.task_id,
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
                        task_id=task.task_id,
                        provider=self.name,
                        auth_token=self.auth_token,
                        status="error",
                        result=json.dumps(result)
                    ))
                    continue

            except grpc.RpcError as e:
                self.logger.error(
                    "gRPC error",
                    error=e.details(),
                    code=e.code()
                )
                if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                    self.logger.error("Provider authentication error")
                    return
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    self.logger.info("Task not found, waiting for next one...")
                    time.sleep(self.execution_timeout)
                    continue
                result = ProviderResponse(
                    status="error",
                    message="gRPC error occurred",
                    data={
                        "error": e.details(),
                        "code": str(e.code())
                    }
                ).model_dump()
                if task.task_id:
                    stub.SubmitTaskResult(hub_pb2.TaskResult(
                        task_id=task.task_id,
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
                if task.task_id:
                    stub.SubmitTaskResult(hub_pb2.TaskResult(
                        task_id=task.task_id,
                        provider=self.name,
                        auth_token=self.auth_token,
                        status="error",
                        result=json.dumps(result)
                    ))
                time.sleep(self.execution_timeout)
                continue
