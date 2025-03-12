import asyncio
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError
from app.tool.base import BaseTool



class AWSServiceTool(BaseTool):
    name: str = "aws_service_tool"
    description: str = """Interact with AWS services using Boto3.
Use this tool to query AWS resources, perform actions, or retrieve data from your AWS account.
The tool dynamically maps user queries to AWS services and actions."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "service_name": {
                "type": "string",
                "description": "(required) The name of the AWS service (e.g., 'ec2', 's3').",
            },
            "action_name": {
                "type": "string",
                "description": "(required) The action to perform on the service (e.g., 'describe_instances', 'list_buckets').",
            },
            "params": {
                "type": "object",
                "description": "(optional) Parameters to pass to the Boto3 action.",
                "default": {},
            },
            "region_name": {
                "type": "string",
                "description": "(optional) The AWS region to execute the query in. Default is 'us-east-1'.",
                "default": "us-east-1",
            },
        },
        "required": ["service_name", "action_name"],
    }

    async def execute(
        self, service_name: str, action_name: str, params: Dict[str, Any] = {}, region_name: str = "us-east-1"
    ) -> Any:
        """
        Execute a Boto3 command and return the response.

        Args:
            service_name (str): The name of the AWS service (e.g., 'ec2', 's3').
            action_name (str): The action to perform on the service (e.g., 'describe_instances').
            params (dict, optional): Parameters to pass to the Boto3 action. Default is an empty dictionary.

        Returns:
            Any: The response from the Boto3 command.
        """
        
        
        try:
            # Run the Boto3 command in a thread pool to prevent blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._execute_boto3_command(service_name, action_name, params, region_name),
            )
            return response
        except ClientError as e:
            return {"error": str(e)}

    def _execute_boto3_command(self, service_name: str, action_name: str, params: Dict[str, Any],region_name: str) -> Any:
        """
        Helper function to execute a Boto3 command synchronously.

        Args:
            service_name (str): The name of the AWS service.
            action_name (str): The action to perform on the service.
            params (dict): Parameters for the action.

        Returns:
            Any: The response from the Boto3 command.
        """
        client = boto3.client(service_name, region_name=region_name)
        method = getattr(client, action_name)
        
        # Execute the method with provided parameters
        if params:
            return method(**params)
        else:
            return method()
