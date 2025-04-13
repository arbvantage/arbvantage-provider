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
import logging
import signal
import backoff
from typing import Optional, Dict, Any
from datetime import datetime

from .protos import hub_pb2, hub_pb2_grpc
from .actions import ActionsRegistry
from .exceptions import ActionNotFoundError, InvalidPayloadError
from .schemas import ProviderResponse
from .rate_limit import RateLimitMonitor, NoRateLimitMonitor, SimpleRateLimitMonitor

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
        logger (logging.Logger): Logger instance for the provider
        actions (ActionsRegistry): Registry of available actions
        rate_limit_monitor (RateLimitMonitor): Rate limit monitoring implementation
    """
    
    def __init__(
        self,
        name: str,
        auth_token: str,
        hub_url: str,
        execution_timeout: int = 1,
        rate_limit_monitor: Optional[RateLimitMonitor] = None
    ):
        """
        Initialize the provider with required configuration.
        
        Args:
            name (str): Unique identifier for the provider
            auth_token (str): Authentication token for Hub communication
            hub_url (str): URL of the Hub service
            execution_timeout (int, optional): Default timeout for task execution. Defaults to 1.
            rate_limit_monitor (Optional[RateLimitMonitor]): Rate limit monitoring implementation
        """
        self.name = name
        self.auth_token = auth_token
        self.hub_url = hub_url
        self.execution_timeout = execution_timeout
        self.running = True
        self.logger = logging.getLogger(name.upper())
        self.actions = ActionsRegistry()
        
        # Initialize rate limit monitor
        if rate_limit_monitor is None:
            self.rate_limit_monitor = NoRateLimitMonitor()
        else:
            self.rate_limit_monitor = rate_limit_monitor

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
            on_backoff=lambda details: self.logger.info(f"Trying to connect to hub... (attempt {details['tries']})")
        )
        def create():
            channel = grpc.insecure_channel(self.hub_url)
            grpc.channel_ready_future(channel).result(timeout=30)
            return channel
        return create()

    def process_task(self, action: str, payload: Dict, account: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single task received from the Hub.
        
        This method:
        1. Validates the action exists
        2. Checks required parameters are present
        3. Executes the action handler
        4. Validates and returns the result
        
        Args:
            action (str): Name of the action to execute
            payload (Dict): Task payload data
            account (Optional[str]): Account identifier if applicable
            
        Returns:
            Dict[str, Any]: Processed task result with status and data
        """
        try:
            action_def = self.actions.get_action(action)
            if not action_def:
                return ProviderResponse(status="error", message=f"Action '{action}' not found").model_dump()

            # Validate required parameters for payload if schema exists
            # If action is required to have payload, we need to validate it
            if hasattr(action_def, 'payload_schema') and action_def.payload_schema:
                missing_params = [
                    param for param in action_def.payload_schema.keys()
                    if param not in payload
                ]
                if missing_params:
                    return ProviderResponse(status="error", message=f"Missing required parameters: {', '.join(missing_params)}").model_dump()
            
            # Validate required parameters for account if schema exists
            # If action is required to have account, we need to validate it
            if hasattr(action_def, 'account_schema') and action_def.account_schema:
                missing_account_params = [
                    param for param in action_def.account_schema.keys()
                    if not account or param not in account
                ]
                if missing_account_params:
                    return ProviderResponse(status="error", message=f"Missing required account parameters: {', '.join(missing_account_params)}").model_dump()
            
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
            result = action_def.handler(**action_params)
            
            # Check if result is an instance of ProviderResponse
            if not isinstance(result, ProviderResponse):
                error_msg = f"Action {action} must return ProviderResponse instance, got {type(result)}"
                self.logger.error(error_msg)
                return ProviderResponse(
                    status="error",
                    data=result,
                    message=error_msg
                ).model_dump()
            
            return result.model_dump()

        except Exception as e:
            self.logger.error(f"Error processing task: {e}")
            return ProviderResponse(status="error", message=str(e)).model_dump()

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
        
        self.logger.info(f"Starting provider worker")
        
        while self.running:
            try:
                with self._create_channel() as channel:
                    self.logger.info(f"Successfully connected to HUB {self.hub_url}")
                    stub = hub_pb2_grpc.HubStub(channel)
                    self._process_tasks(stub)
            except Exception as e:
                if self.running:
                    self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
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
                    self.rate_limit_monitor.handle_throttling(limits["wait_time"])
                
                task = stub.GetTask(hub_pb2.ProviderRequest(
                    provider=self.name,
                    auth_token=self.auth_token
                ))

                if not task.task_id:
                    if task.action == b"rate_limited":
                        try:
                            rate_limit_data = json.loads(task.payload.decode('utf-8'))
                            wait_time = rate_limit_data.get("wait_time", self.execution_timeout)
                            self.logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                            self.rate_limit_monitor.handle_throttling(wait_time)
                        except json.JSONDecodeError:
                            self.rate_limit_monitor.handle_throttling(self.execution_timeout)
                    else:
                        self.rate_limit_monitor.handle_throttling(self.execution_timeout)
                    continue

                self.logger.info(f"Received task: {task}")
                
                try:
                    payload = json.loads(task.payload.decode('utf-8'))
                    action = task.action
                    account = task.account
                    
                    result = self.process_task(action, payload, account)
                    status = "error" if result["status"] == "error" else "success"

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
                    
                    self.logger.info(f"Task {task.task_id} completed")
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse task data: {e}")
                    continue

            except grpc.RpcError as e:
                self.logger.error(f"gRPC error: {e.details()}")
                if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                    self.logger.error("Provider authentication error")
                    return
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    self.logger.info("Task not found, waiting for next one...")
                    time.sleep(self.execution_timeout)
                    continue
                raise 
