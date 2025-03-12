import asyncio
import requests
from typing import Dict, Any
from app.tool.base import BaseTool


class FDAApiTool(BaseTool):
    name: str = "fda_api_tool"
    description: str = """Interact with openFDA APIs to query public FDA datasets.
Use this tool to fetch data about drugs, devices, food recalls, adverse events, and more.
The tool dynamically maps user queries to the appropriate openFDA API endpoint and retrieves data."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "endpoint": {
                "type": "string",
                "description": "(required) The specific openFDA API endpoint to query (e.g., 'drug/event', 'device/enforcement').",
            },
            "query_params": {
                "type": "object",
                "description": "(optional) Query parameters for the API request (e.g., {'search': 'aspirin', 'limit': 10}).",
                "default": {},
            },
        },
        "required": ["endpoint"],
    }

    async def execute(self, endpoint: str, query_params: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Execute an openFDA API call and return the response.

        Args:
            endpoint (str): The specific openFDA API endpoint to query (e.g., 'drug/event').
            query_params (dict, optional): Query parameters for the API request. Default is an empty dictionary.

        Returns:
            Dict[str, Any]: The JSON response from the openFDA API.
        """
        try:
            # Run the API call in a thread pool to prevent blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._fetch_fda_data(endpoint, query_params),
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def _fetch_fda_data(self, endpoint: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper function to fetch data from the openFDA API synchronously.

        Args:
            endpoint (str): The specific openFDA API endpoint to query.
            query_params (dict): Query parameters for the API request.

        Returns:
            Dict[str, Any]: The JSON response from the openFDA API.
        """
        base_url = "https://api.fda.gov"
        url = f"{base_url}/{endpoint}.json"

        # Send GET request with query parameters
        response = requests.get(url, params=query_params)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
