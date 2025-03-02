import grpc
import json
import time
import logging
import signal
import backoff
from typing import Optional, Dict, Any
from datetime import datetime

from protos import arbvantage_pb2, arbvantage_pb2_grpc
from .actions import ActionsRegistry
from .exceptions import ActionNotFoundError, InvalidPayloadError

class Provider:
    """Base class for creating providers"""
    
    def __init__(
        self,
        name: str,
        auth_token: str,
        hub_url: str,
        execution_timeout: int = 1
    ):
        self.name = name
        self.auth_token = auth_token
        self.hub_url = hub_url
        self.execution_timeout = execution_timeout
        self.running = True
        self.logger = logging.getLogger(name.upper())
        self.actions = ActionsRegistry()

    def _create_channel(self):
        """Creating a channel to connect to the Hub"""
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
        """Processing a task"""
        try:
            action_def = self.actions.get_action(action)
            if not action_def:
                raise ActionNotFoundError(f"Action '{action}' not found")

            # Checking required parameters
            missing_params = [
                param for param in action_def.payload_schema.keys()
                if param not in payload
            ]
            if missing_params:
                raise InvalidPayloadError(f"Missing required parameters: {', '.join(missing_params)}")

            # Preparing parameters for the handler
            action_params = {
                param: payload[param]
                for param in action_def.payload_schema.keys()
            }
            if account:
                action_params['account'] = account

            # Executing the action
            result = action_def.handler(**action_params)
            return {"status": "success", "data": result}

        except Exception as e:
            self.logger.error(f"Error processing task: {e}")
            return {"status": "error", "error": str(e)}

    def start(self):
        """Starting the provider"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info(f"Starting provider worker")
        
        while self.running:
            try:
                with self._create_channel() as channel:
                    self.logger.info(f"Successfully connected to HUB {self.hub_url}")
                    stub = arbvantage_pb2_grpc.HubStub(channel)
                    self._process_tasks(stub)
            except Exception as e:
                if self.running:
                    self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                    time.sleep(1)

    def _signal_handler(self, signum, frame):
        """Signal handler for graceful shutdown"""
        self.logger.info("Signal received, stopping provider...")
        self.running = False

    def _process_tasks(self, stub):
        """Processing tasks from the Hub"""
        while self.running:
            try:
                task = stub.GetTask(arbvantage_pb2.ProviderRequest(
                    provider=self.name,
                    auth_token=self.auth_token
                ))

                if not task.task_id:
                    if task.action == b"rate_limited":
                        try:
                            rate_limit_data = json.loads(task.payload.decode('utf-8'))
                            wait_time = rate_limit_data.get("wait_time", self.execution_timeout)
                            self.logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                        except json.JSONDecodeError:
                            time.sleep(self.execution_timeout)
                    else:
                        time.sleep(self.execution_timeout)
                    continue

                self.logger.info(f"Received task: {task}")
                
                try:
                    payload = json.loads(task.payload.decode('utf-8'))
                    action = task.action
                    account = task.account
                    
                    result = self.process_task(action, payload, account)
                    
                    status = "error" if result["status"] == "error" else "success"
                    result_data = {"error": result["error"]} if status == "error" else result["data"]
                        
                    stub.SubmitTaskResult(arbvantage_pb2.TaskResult(
                        task_id=task.task_id,
                        provider=self.name,
                        auth_token=self.auth_token,
                        payload=json.dumps(payload),
                        action=action,
                        status=status,
                        result=json.dumps(result_data)
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